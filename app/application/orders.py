from decimal import Decimal
from uuid import uuid4

from sqlalchemy import update
from sqlmodel import Session, select

from app.application.contracts import (
    CriarPedido,
    ItemPedidoResposta,
    PagamentoResposta,
    PedidoResposta,
)
from app.application.fidelity import apply_payment_points
from app.application.errors import ApplicationError
from app.domain.enums import (
    PerfilUsuario,
    ResultadoPagamentoMock,
    StatusPagamento,
    StatusPedido,
)
from app.infrastructure.models import (
    Auditoria,
    Estoque,
    ItemPedido,
    Pagamento,
    Pedido,
    Produto,
    Unidade,
    Usuario,
)


def create_order(data: CriarPedido, user: Usuario, session: Session) -> PedidoResposta:
    unit = session.get(Unidade, data.unidade_id)
    if unit is None or not unit.ativa:
        raise ApplicationError(404, "NOT_FOUND", "Unidade não encontrada ou inativa.")

    # Validamos todos os itens antes de alterar qualquer saldo.
    selected: list[tuple[Produto, Estoque, int]] = []
    seen_product_ids: set[int] = set()
    for requested_item in data.itens:
        if requested_item.produto_id in seen_product_ids:
            raise ApplicationError(
                422, "VALIDATION_ERROR", "Informe cada produto apenas uma vez no pedido."
            )
        seen_product_ids.add(requested_item.produto_id)

        product = session.get(Produto, requested_item.produto_id)
        if product is None or not product.ativo:
            raise ApplicationError(
                404,
                "NOT_FOUND",
                f"Produto {requested_item.produto_id} não encontrado ou inativo.",
            )
        stock = session.exec(
            select(Estoque).where(
                Estoque.unidade_id == unit.id,
                Estoque.produto_id == product.id,
            )
        ).first()
        if stock is None:
            raise ApplicationError(
                404,
                "NOT_FOUND",
                f"Produto {product.id} não está disponível nesta unidade.",
            )
        if stock.quantidade < requested_item.quantidade:
            raise ApplicationError(
                409, "STOCK_CONFLICT", f"Estoque insuficiente para o produto {product.id}."
            )
        selected.append((product, stock, requested_item.quantidade))

    order = Pedido(
        usuario_id=user.id,
        unidade_id=unit.id,
        canal_pedido=data.canal_pedido,
        status=StatusPedido.AGUARDANDO_PAGAMENTO,
        total=sum(
            (product.preco * quantity for product, _, quantity in selected),
            start=Decimal("0.00"),
        ),
    )
    session.add(order)
    session.flush()

    response_items: list[ItemPedidoResposta] = []
    for product, stock, quantity in selected:
        # A condição no UPDATE evita vender saldo que outra requisição já consumiu.
        result = session.exec(
            update(Estoque)
            .where(Estoque.id == stock.id, Estoque.quantidade >= quantity)
            .values(quantidade=Estoque.quantidade - quantity)
        )
        if result.rowcount != 1:
            session.rollback()
            raise ApplicationError(
                409, "STOCK_CONFLICT", f"Estoque insuficiente para o produto {product.id}."
            )
        session.add(
            ItemPedido(
                pedido_id=order.id,
                produto_id=product.id,
                quantidade=quantity,
                preco_unitario=product.preco,
            )
        )
        response_items.append(
            ItemPedidoResposta(
                produto_id=product.id,
                quantidade=quantity,
                preco_unitario=product.preco,
            )
        )

    session.add(
        Auditoria(
            usuario_id=user.id,
            acao="PEDIDO_CRIADO",
            entidade="PEDIDO",
            entidade_id=str(order.id),
            detalhes=f"canal={order.canal_pedido.value};total={order.total}",
        )
    )
    session.commit()
    session.refresh(order)
    return PedidoResposta(
        id=order.id,
        unidade_id=order.unidade_id,
        canal_pedido=order.canal_pedido,
        status=order.status,
        total=order.total,
        desconto_fidelidade=order.desconto_fidelidade,
        itens=response_items,
    )


def register_mock_payment(
    order_id: int,
    result: ResultadoPagamentoMock,
    user: Usuario,
    session: Session,
) -> PedidoResposta:
    order = session.get(Pedido, order_id)
    if order is None:
        raise ApplicationError(404, "NOT_FOUND", "Pedido não encontrado.")
    if user.perfil == PerfilUsuario.CLIENTE and order.usuario_id != user.id:
        raise ApplicationError(403, "FORBIDDEN", "Este pedido pertence a outro cliente.")
    if user.perfil not in (PerfilUsuario.CLIENTE, PerfilUsuario.ADMIN):
        raise ApplicationError(403, "FORBIDDEN", "Seu perfil não pode registrar pagamentos.")
    if order.status != StatusPedido.AGUARDANDO_PAGAMENTO:
        raise ApplicationError(409, "ORDER_STATE_CONFLICT", "O pedido não está aguardando pagamento.")

    payment_status = (
        StatusPagamento.APROVADO
        if result == ResultadoPagamentoMock.APROVADO
        else StatusPagamento.RECUSADO
    )
    payment = Pagamento(
        pedido_id=order.id,
        status=payment_status,
        referencia_mock=f"MOCK-{uuid4().hex[:12].upper()}",
        valor=order.total,
    )
    payment.payload_resposta = {
        "gateway": "MOCK",
        "status": payment_status.value,
        "referencia": payment.referencia_mock,
        "mensagem": (
            "Pagamento aprovado na simulação."
            if payment_status == StatusPagamento.APROVADO
            else "Pagamento recusado na simulação."
        ),
    }
    session.add(payment)
    session.add(
        Auditoria(
            usuario_id=user.id,
            acao=f"PAGAMENTO_{payment_status.value}",
            entidade="PEDIDO",
            entidade_id=str(order.id),
            detalhes=f"valor={order.total};referencia={payment.referencia_mock}",
        )
    )

    if payment_status == StatusPagamento.APROVADO:
        order.status = StatusPedido.EM_PREPARACAO
    else:
        order.status = StatusPedido.CANCELADO
        items = session.exec(
            select(ItemPedido).where(ItemPedido.pedido_id == order.id)
        ).all()
        for item in items:
            stock = session.exec(
                select(Estoque).where(
                    Estoque.unidade_id == order.unidade_id,
                    Estoque.produto_id == item.produto_id,
                )
            ).first()
            if stock is not None:
                stock.quantidade += item.quantidade

    apply_payment_points(
        order,
        approved=payment_status == StatusPagamento.APROVADO,
        session=session,
    )

    session.add(order)
    session.commit()
    session.refresh(order)
    items = session.exec(
        select(ItemPedido).where(ItemPedido.pedido_id == order.id)
    ).all()
    return PedidoResposta(
        id=order.id,
        unidade_id=order.unidade_id,
        canal_pedido=order.canal_pedido,
        status=order.status,
        total=order.total,
        desconto_fidelidade=order.desconto_fidelidade,
        pagamento=PagamentoResposta(
            status=payment.status,
            referencia=payment.referencia_mock,
            valor=payment.valor,
            payload=payment.payload_resposta,
        ),
        itens=[
            ItemPedidoResposta(
                produto_id=item.produto_id,
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario,
            )
            for item in items
        ],
    )


def update_order_status(
    order_id: int,
    target_status: StatusPedido,
    user: Usuario,
    session: Session,
) -> PedidoResposta:
    order = session.get(Pedido, order_id)
    if order is None:
        raise ApplicationError(404, "NOT_FOUND", "Pedido não encontrado.")

    allowed_roles: tuple[PerfilUsuario, ...]
    if order.status == StatusPedido.EM_PREPARACAO and target_status == StatusPedido.PRONTO:
        allowed_roles = (PerfilUsuario.COZINHA, PerfilUsuario.GERENTE, PerfilUsuario.ADMIN)
    elif order.status == StatusPedido.PRONTO and target_status == StatusPedido.ENTREGUE:
        allowed_roles = (PerfilUsuario.ATENDENTE, PerfilUsuario.GERENTE, PerfilUsuario.ADMIN)
    else:
        raise ApplicationError(
            409,
            "ORDER_STATE_CONFLICT",
            f"Transição não permitida: {order.status.value} para {target_status.value}.",
        )

    if user.perfil not in allowed_roles:
        raise ApplicationError(
            403, "FORBIDDEN", "Seu perfil não pode executar esta transição de status."
        )

    previous_status = order.status
    order.status = target_status
    session.add(order)
    session.add(
        Auditoria(
            usuario_id=user.id,
            acao="STATUS_PEDIDO_ATUALIZADO",
            entidade="PEDIDO",
            entidade_id=str(order.id),
            detalhes=f"de={previous_status.value};para={target_status.value}",
        )
    )
    session.commit()
    session.refresh(order)
    items = session.exec(
        select(ItemPedido).where(ItemPedido.pedido_id == order.id)
    ).all()
    return PedidoResposta(
        id=order.id,
        unidade_id=order.unidade_id,
        canal_pedido=order.canal_pedido,
        status=order.status,
        total=order.total,
        desconto_fidelidade=order.desconto_fidelidade,
        itens=[
            ItemPedidoResposta(
                produto_id=item.produto_id,
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario,
            )
            for item in items
        ],
    )
