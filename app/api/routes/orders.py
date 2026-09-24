from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import select

from app.api.dependencies import CurrentUser, SessionDependency, require_roles
from app.api.schemas import (
    AtualizarStatusPedido,
    CriarPedido,
    PedidoResposta,
    ResultadoPagamento,
)
from app.application.orders import (
    create_order,
    register_mock_payment,
    update_order_status,
)
from app.domain.enums import CanalPedido, PerfilUsuario, StatusPedido
from app.infrastructure.models import ItemPedido, Pedido, Usuario


router = APIRouter(prefix="/pedidos", tags=["Pedidos"])
OrderWriter = Annotated[
    Usuario,
    Depends(require_roles(PerfilUsuario.CLIENTE)),
]


@router.post(
    "",
    response_model=PedidoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Criar pedido e reservar o estoque",
)
def create_order_route(
    data: CriarPedido,
    current_user: OrderWriter,
    session: SessionDependency,
) -> PedidoResposta:
    return create_order(data, current_user, session)


@router.post(
    "/{pedido_id}/pagamento-mock",
    response_model=PedidoResposta,
    summary="Simular aprovação ou recusa do pagamento",
)
def mock_payment_route(
    pedido_id: int,
    data: ResultadoPagamento,
    current_user: CurrentUser,
    session: SessionDependency,
) -> PedidoResposta:
    return register_mock_payment(
        pedido_id, data.resultado, current_user, session
    )


@router.patch(
    "/{pedido_id}/status",
    response_model=PedidoResposta,
    summary="Avançar o pedido para pronto ou entregue",
)
def update_order_status_route(
    pedido_id: int,
    data: AtualizarStatusPedido,
    current_user: CurrentUser,
    session: SessionDependency,
) -> PedidoResposta:
    return update_order_status(
        pedido_id, data.status, current_user, session
    )


@router.get(
    "",
    response_model=list[PedidoResposta],
    summary="Listar pedidos visíveis ao usuário",
)
def list_orders(
    current_user: CurrentUser,
    session: SessionDependency,
    canal_pedido: CanalPedido | None = Query(default=None, alias="canalPedido"),
    status_pedido: StatusPedido | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
) -> list[PedidoResposta]:
    statement = select(Pedido)
    if current_user.perfil == PerfilUsuario.CLIENTE:
        statement = statement.where(Pedido.usuario_id == current_user.id)
    if canal_pedido:
        statement = statement.where(Pedido.canal_pedido == canal_pedido)
    if status_pedido:
        statement = statement.where(Pedido.status == status_pedido)
    statement = statement.order_by(Pedido.criado_em.desc())
    statement = statement.offset((page - 1) * limit).limit(limit)
    orders = session.exec(statement).all()

    responses = []
    for order in orders:
        items = session.exec(
            select(ItemPedido).where(ItemPedido.pedido_id == order.id)
        ).all()
        responses.append(
            PedidoResposta(
                id=order.id,
                unidade_id=order.unidade_id,
                canal_pedido=order.canal_pedido,
                status=order.status,
                total=order.total,
                desconto_fidelidade=order.desconto_fidelidade,
                itens=[
                    {
                        "produto_id": item.produto_id,
                        "quantidade": item.quantidade,
                        "preco_unitario": item.preco_unitario,
                    }
                    for item in items
                ],
            )
        )
    return responses
