from sqlalchemy.exc import IntegrityError
from sqlalchemy import update
from sqlmodel import Session, select

from app.application.contracts import (
    CriarProduto,
    CriarUnidade,
    EstoqueResposta,
    MovimentoEstoqueEntrada,
)
from app.application.errors import ApplicationError
from app.domain.enums import TipoMovimentoEstoque
from app.infrastructure.models import Auditoria, Estoque, Produto, Unidade, Usuario


def create_unit(data: CriarUnidade, user: Usuario, session: Session) -> Unidade:
    unit = Unidade(nome=data.nome.strip(), endereco=data.endereco.strip())
    session.add(unit)
    session.flush()
    session.add(
        Auditoria(
            usuario_id=user.id,
            acao="UNIDADE_CRIADA",
            entidade="UNIDADE",
            entidade_id=str(unit.id),
            detalhes=f"nome={unit.nome}",
        )
    )
    session.commit()
    session.refresh(unit)
    return unit


def create_product(data: CriarProduto, user: Usuario, session: Session) -> Produto:
    product = Produto(
        nome=data.nome.strip(),
        descricao=data.descricao.strip() if data.descricao else None,
        preco=data.preco,
    )
    session.add(product)
    session.flush()
    session.add(
        Auditoria(
            usuario_id=user.id,
            acao="PRODUTO_CRIADO",
            entidade="PRODUTO",
            entidade_id=str(product.id),
            detalhes=f"nome={product.nome};preco={product.preco}",
        )
    )
    session.commit()
    session.refresh(product)
    return product


def move_stock(
    unit_id: int,
    product_id: int,
    data: MovimentoEstoqueEntrada,
    user: Usuario,
    session: Session,
) -> EstoqueResposta:
    unit = session.get(Unidade, unit_id)
    if unit is None or not unit.ativa:
        raise ApplicationError(404, "NOT_FOUND", "Unidade não encontrada ou inativa.")
    product = session.get(Produto, product_id)
    if product is None or not product.ativo:
        raise ApplicationError(404, "NOT_FOUND", "Produto não encontrado ou inativo.")

    stock = session.exec(
        select(Estoque).where(
            Estoque.unidade_id == unit_id,
            Estoque.produto_id == product_id,
        )
    ).first()
    if stock is None:
        if data.tipo == TipoMovimentoEstoque.SAIDA:
            raise ApplicationError(409, "STOCK_CONFLICT", "Não há saldo para esta saída.")
        stock = Estoque(unidade_id=unit_id, produto_id=product_id, quantidade=0)
        session.add(stock)
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            raise ApplicationError(
                409,
                "STOCK_CONFLICT",
                "Outra movimentação criou o saldo simultaneamente; tente novamente.",
            )

    if data.tipo == TipoMovimentoEstoque.ENTRADA:
        result = session.exec(
            update(Estoque)
            .where(Estoque.id == stock.id)
            .values(quantidade=Estoque.quantidade + data.quantidade)
        )
    else:
        result = session.exec(
            update(Estoque)
            .where(
                Estoque.id == stock.id,
                Estoque.quantidade >= data.quantidade,
            )
            .values(quantidade=Estoque.quantidade - data.quantidade)
        )
    if result.rowcount != 1:
        session.rollback()
        raise ApplicationError(409, "STOCK_CONFLICT", "Estoque insuficiente para esta saída.")

    session.flush()
    session.refresh(stock)

    session.add(
        Auditoria(
            usuario_id=user.id,
            acao=f"ESTOQUE_{data.tipo.value}",
            entidade="ESTOQUE",
            entidade_id=f"{unit_id}:{product_id}",
            detalhes=f"tipo={data.tipo.value};quantidade={data.quantidade};novo_saldo={stock.quantidade}",
        )
    )
    session.commit()
    stock = session.exec(
        select(Estoque).where(
            Estoque.unidade_id == unit_id,
            Estoque.produto_id == product_id,
        )
    ).one()
    return EstoqueResposta(
        unidade_id=stock.unidade_id,
        produto_id=stock.produto_id,
        quantidade=stock.quantidade,
    )
