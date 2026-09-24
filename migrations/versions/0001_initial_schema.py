"""Create the initial Raizes do Nordeste schema.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "perfil",
            sa.Enum(
                "CLIENTE", "ATENDENTE", "COZINHA", "GERENTE", "ADMIN",
                name="perfilusuario", native_enum=False,
            ),
            nullable=False,
        ),
    )
    op.create_index("ix_usuario_email", "usuario", ["email"], unique=True)

    op.create_table(
        "unidade",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("endereco", sa.String(length=255), nullable=False),
        sa.Column("ativa", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_unidade_nome", "unidade", ["nome"])

    op.create_table(
        "produto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("descricao", sa.String(length=500), nullable=True),
        sa.Column("preco", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.CheckConstraint("preco > 0", name="ck_produto_preco_positivo"),
    )
    op.create_index("ix_produto_nome", "produto", ["nome"])

    op.create_table(
        "estoque",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("unidade_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["unidade_id"], ["unidade.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produto.id"]),
        sa.UniqueConstraint("unidade_id", "produto_id"),
        sa.CheckConstraint("quantidade >= 0", name="ck_estoque_quantidade_nao_negativa"),
    )
    op.create_index("ix_estoque_unidade_id", "estoque", ["unidade_id"])
    op.create_index("ix_estoque_produto_id", "estoque", ["produto_id"])

    op.create_table(
        "pedido",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("unidade_id", sa.Integer(), nullable=False),
        sa.Column(
            "canal_pedido",
            sa.Enum(
                "APP", "TOTEM", "BALCAO", "PICKUP", "WEB",
                name="canalpedido", native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "AGUARDANDO_PAGAMENTO", "EM_PREPARACAO", "PRONTO", "ENTREGUE", "CANCELADO",
                name="statuspedido", native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("total", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("desconto_fidelidade", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["unidade_id"], ["unidade.id"]),
        sa.CheckConstraint("total > 0", name="ck_pedido_total_positivo"),
        sa.CheckConstraint("desconto_fidelidade >= 0", name="ck_pedido_desconto_nao_negativo"),
    )
    op.create_index("ix_pedido_usuario_id", "pedido", ["usuario_id"])
    op.create_index("ix_pedido_unidade_id", "pedido", ["unidade_id"])
    op.create_index("ix_pedido_canal_pedido", "pedido", ["canal_pedido"])
    op.create_index("ix_pedido_status", "pedido", ["status"])
    op.create_index("ix_pedido_criado_em", "pedido", ["criado_em"])

    op.create_table(
        "itempedido",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pedido_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column("preco_unitario", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedido.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produto.id"]),
        sa.CheckConstraint("quantidade > 0", name="ck_itempedido_quantidade_positiva"),
        sa.CheckConstraint("preco_unitario > 0", name="ck_itempedido_preco_positivo"),
    )
    op.create_index("ix_itempedido_pedido_id", "itempedido", ["pedido_id"])
    op.create_index("ix_itempedido_produto_id", "itempedido", ["produto_id"])

    op.create_table(
        "pagamento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pedido_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDENTE", "APROVADO", "RECUSADO", name="statuspagamento", native_enum=False),
            nullable=False,
        ),
        sa.Column("referencia_mock", sa.String(length=100), nullable=True),
        sa.Column("payload_resposta", sa.JSON(), nullable=False),
        sa.Column("valor", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedido.id"]),
        sa.CheckConstraint("valor > 0", name="ck_pagamento_valor_positivo"),
    )
    op.create_index("ix_pagamento_pedido_id", "pagamento", ["pedido_id"])
    op.create_index("ix_pagamento_status", "pagamento", ["status"])
    op.create_index("ix_pagamento_criado_em", "pagamento", ["criado_em"])

    op.create_table(
        "auditoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("acao", sa.String(length=80), nullable=False),
        sa.Column("entidade", sa.String(length=80), nullable=False),
        sa.Column("entidade_id", sa.String(length=80), nullable=False),
        sa.Column("detalhes", sa.String(length=500), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
    )
    op.create_index("ix_auditoria_usuario_id", "auditoria", ["usuario_id"])
    op.create_index("ix_auditoria_acao", "auditoria", ["acao"])
    op.create_index("ix_auditoria_entidade", "auditoria", ["entidade"])
    op.create_index("ix_auditoria_entidade_id", "auditoria", ["entidade_id"])
    op.create_index("ix_auditoria_criado_em", "auditoria", ["criado_em"])

    op.create_table(
        "consentimentofidelidade",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("consentido", sa.Boolean(), nullable=False),
        sa.Column("registrado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
    )
    op.create_index("ix_consentimentofidelidade_usuario_id", "consentimentofidelidade", ["usuario_id"])
    op.create_index("ix_consentimentofidelidade_registrado_em", "consentimentofidelidade", ["registrado_em"])

    op.create_table(
        "movimentofidelidade",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("pedido_id", sa.Integer(), nullable=True),
        sa.Column(
            "tipo",
            sa.Enum("GANHO", "RESGATE", "ESTORNO", name="tipomovimentofidelidade", native_enum=False),
            nullable=False,
        ),
        sa.Column("pontos", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedido.id"]),
        sa.UniqueConstraint("pedido_id", "tipo"),
        sa.CheckConstraint("pontos > 0", name="ck_movimentofidelidade_pontos_positivos"),
    )
    op.create_index("ix_movimentofidelidade_usuario_id", "movimentofidelidade", ["usuario_id"])
    op.create_index("ix_movimentofidelidade_pedido_id", "movimentofidelidade", ["pedido_id"])
    op.create_index("ix_movimentofidelidade_tipo", "movimentofidelidade", ["tipo"])
    op.create_index("ix_movimentofidelidade_criado_em", "movimentofidelidade", ["criado_em"])


def downgrade() -> None:
    op.drop_table("movimentofidelidade")
    op.drop_table("consentimentofidelidade")
    op.drop_table("auditoria")
    op.drop_table("pagamento")
    op.drop_table("itempedido")
    op.drop_table("pedido")
    op.drop_table("estoque")
    op.drop_table("produto")
    op.drop_table("unidade")
    op.drop_table("usuario")
