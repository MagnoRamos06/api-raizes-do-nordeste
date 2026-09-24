from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, Column, Enum as SqlEnum, JSON, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.domain.enums import (
    CanalPedido,
    PerfilUsuario,
    StatusPagamento,
    StatusPedido,
    TipoMovimentoFidelidade,
)


class Usuario(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(min_length=2, max_length=120)
    email: str = Field(index=True, unique=True, max_length=254)
    senha_hash: str = Field(max_length=255)
    perfil: PerfilUsuario = Field(
        sa_column=Column(SqlEnum(PerfilUsuario), nullable=False)
    )


class Unidade(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(max_length=120, index=True)
    endereco: str = Field(max_length=255)
    ativa: bool = Field(default=True)


class Produto(SQLModel, table=True):
    __table_args__ = (CheckConstraint("preco > 0", name="ck_produto_preco_positivo"),)

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(max_length=120, index=True)
    descricao: str | None = Field(default=None, max_length=500)
    preco: Decimal = Field(max_digits=10, decimal_places=2, gt=0)
    ativo: bool = Field(default=True)


class Estoque(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("unidade_id", "produto_id"),
        CheckConstraint("quantidade >= 0", name="ck_estoque_quantidade_nao_negativa"),
    )

    id: int | None = Field(default=None, primary_key=True)
    unidade_id: int = Field(foreign_key="unidade.id", index=True)
    produto_id: int = Field(foreign_key="produto.id", index=True)
    quantidade: int = Field(default=0, ge=0)


class Pedido(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("total > 0", name="ck_pedido_total_positivo"),
        CheckConstraint(
            "desconto_fidelidade >= 0", name="ck_pedido_desconto_nao_negativo"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    unidade_id: int = Field(foreign_key="unidade.id", index=True)
    canal_pedido: CanalPedido = Field(
        sa_column=Column(SqlEnum(CanalPedido), nullable=False, index=True)
    )
    status: StatusPedido = Field(
        default=StatusPedido.AGUARDANDO_PAGAMENTO,
        sa_column=Column(
            SqlEnum(StatusPedido),
            nullable=False,
            default=StatusPedido.AGUARDANDO_PAGAMENTO,
            index=True,
        ),
    )
    total: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)
    desconto_fidelidade: Decimal = Field(
        default=Decimal("0.00"), max_digits=10, decimal_places=2
    )
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )


class ItemPedido(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_itempedido_quantidade_positiva"),
        CheckConstraint("preco_unitario > 0", name="ck_itempedido_preco_positivo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedido.id", index=True)
    produto_id: int = Field(foreign_key="produto.id", index=True)
    quantidade: int = Field(gt=0)
    # Snapshot do preço: preserva o valor cobrado mesmo se o produto mudar de preço.
    preco_unitario: Decimal = Field(max_digits=10, decimal_places=2, gt=0)


class Pagamento(SQLModel, table=True):
    __table_args__ = (CheckConstraint("valor > 0", name="ck_pagamento_valor_positivo"),)

    id: int | None = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedido.id", index=True)
    status: StatusPagamento = Field(
        default=StatusPagamento.PENDENTE,
        sa_column=Column(
            SqlEnum(StatusPagamento), nullable=False, default=StatusPagamento.PENDENTE
        ),
    )
    referencia_mock: str | None = Field(default=None, max_length=100)
    payload_resposta: dict = Field(default_factory=dict, sa_type=JSON)
    valor: Decimal = Field(max_digits=10, decimal_places=2, gt=0)
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )


class Auditoria(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    acao: str = Field(max_length=80, index=True)
    entidade: str = Field(max_length=80, index=True)
    entidade_id: str = Field(max_length=80, index=True)
    detalhes: str | None = Field(default=None, max_length=500)
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )


class ConsentimentoFidelidade(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    consentido: bool
    registrado_em: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )


class MovimentoFidelidade(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("pedido_id", "tipo"),
        CheckConstraint("pontos > 0", name="ck_movimentofidelidade_pontos_positivos"),
    )

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    pedido_id: int | None = Field(default=None, foreign_key="pedido.id", index=True)
    tipo: TipoMovimentoFidelidade = Field(
        sa_column=Column(SqlEnum(TipoMovimentoFidelidade), nullable=False, index=True)
    )
    pontos: int = Field(gt=0)
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
