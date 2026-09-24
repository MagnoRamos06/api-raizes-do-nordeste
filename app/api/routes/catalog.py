from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select

from app.api.dependencies import CurrentUser, SessionDependency, require_roles
from app.api.schemas import (
    CriarProduto,
    CriarUnidade,
    EstoqueResposta,
    ItemCardapio,
    MovimentoEstoqueEntrada,
    ProdutoResposta,
    UnidadeResposta,
)
from app.application.catalog import create_product, create_unit, move_stock
from app.domain.enums import PerfilUsuario
from app.infrastructure.models import Estoque, Produto, Unidade, Usuario


router = APIRouter(tags=["Catálogo e estoque"])
CatalogManager = Annotated[
    Usuario,
    Depends(require_roles(PerfilUsuario.GERENTE, PerfilUsuario.ADMIN)),
]
StockViewer = Annotated[
    Usuario,
    Depends(
        require_roles(
            PerfilUsuario.COZINHA,
            PerfilUsuario.GERENTE,
            PerfilUsuario.ADMIN,
        )
    ),
]


@router.get("/unidades", response_model=list[UnidadeResposta])
def list_units(session: SessionDependency) -> list[Unidade]:
    return session.exec(select(Unidade).where(Unidade.ativa.is_(True))).all()


@router.post(
    "/unidades",
    response_model=UnidadeResposta,
    status_code=status.HTTP_201_CREATED,
)
def create_unit_route(
    data: CriarUnidade,
    current_user: CatalogManager,
    session: SessionDependency,
) -> Unidade:
    return create_unit(data, current_user, session)


@router.get("/produtos", response_model=list[ProdutoResposta])
def list_products(
    session: SessionDependency,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[Produto]:
    statement = (
        select(Produto)
        .where(Produto.ativo.is_(True))
        .order_by(Produto.nome)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return session.exec(statement).all()


@router.get(
    "/unidades/{unidade_id}/cardapio",
    response_model=list[ItemCardapio],
    summary="Consultar cardápio e disponibilidade de uma unidade",
)
def get_unit_menu(
    unidade_id: int,
    session: SessionDependency,
) -> list[ItemCardapio]:
    unit = session.get(Unidade, unidade_id)
    if unit is None or not unit.ativa:
        raise HTTPException(status_code=404, detail="Unidade não encontrada ou inativa.")
    rows = session.exec(
        select(Produto, Estoque)
        .join(Estoque, Estoque.produto_id == Produto.id)
        .where(
            Estoque.unidade_id == unidade_id,
            Produto.ativo.is_(True),
            Estoque.quantidade > 0,
        )
        .order_by(Produto.nome)
    ).all()
    return [
        ItemCardapio(
            produto_id=product.id,
            nome=product.nome,
            descricao=product.descricao,
            preco=product.preco,
            disponivel=stock.quantidade > 0,
        )
        for product, stock in rows
    ]


@router.post(
    "/produtos",
    response_model=ProdutoResposta,
    status_code=status.HTTP_201_CREATED,
)
def create_product_route(
    data: CriarProduto,
    current_user: CatalogManager,
    session: SessionDependency,
) -> Produto:
    return create_product(data, current_user, session)


@router.post(
    "/unidades/{unidade_id}/estoque/{produto_id}/movimentacoes",
    response_model=EstoqueResposta,
    summary="Registrar entrada ou saída de estoque",
)
def stock_movement_route(
    unidade_id: int,
    produto_id: int,
    data: MovimentoEstoqueEntrada,
    current_user: CatalogManager,
    session: SessionDependency,
) -> EstoqueResposta:
    return move_stock(unidade_id, produto_id, data, current_user, session)


@router.get(
    "/unidades/{unidade_id}/estoque",
    response_model=list[EstoqueResposta],
)
def get_unit_stock(
    unidade_id: int,
    _current_user: StockViewer,
    session: SessionDependency,
) -> list[EstoqueResposta]:
    unit = session.get(Unidade, unidade_id)
    if unit is None:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")
    rows = session.exec(
        select(Estoque).where(Estoque.unidade_id == unidade_id).order_by(Estoque.produto_id)
    ).all()
    return [
        EstoqueResposta(
            unidade_id=row.unidade_id,
            produto_id=row.produto_id,
            quantidade=row.quantidade,
        )
        for row in rows
    ]
