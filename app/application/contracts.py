from decimal import Decimal
from datetime import datetime

from pydantic import ConfigDict, EmailStr, Field as PydanticField, field_validator
from sqlmodel import SQLModel

from app.domain.enums import (
    CanalPedido,
    PerfilUsuario,
    ResultadoPagamentoMock,
    StatusPagamento,
    StatusPedido,
    TipoMovimentoFidelidade,
    TipoMovimentoEstoque,
)


class CadastroUsuario(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    nome: str = PydanticField(min_length=2, max_length=120)
    email: EmailStr
    senha: str = PydanticField(min_length=8, max_length=128)
    consentimento_fidelidade: bool = False

    @field_validator("nome")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Informe ao menos dois caracteres no nome.")
        return normalized


class CadastroOperador(CadastroUsuario):
    perfil: PerfilUsuario


class LoginUsuario(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr
    senha: str


class UsuarioPublico(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    nome: str
    email: EmailStr
    perfil: PerfilUsuario


class TokenResposta(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    access_token: str
    token_type: str = "bearer"


class ItemPedidoEntrada(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    produto_id: int = PydanticField(gt=0, alias="produtoId")
    quantidade: int = PydanticField(gt=0)


class CriarPedido(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    unidade_id: int = PydanticField(gt=0, alias="unidadeId")
    canal_pedido: CanalPedido = PydanticField(alias="canalPedido")
    itens: list[ItemPedidoEntrada] = PydanticField(min_length=1)


class ItemPedidoResposta(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    produto_id: int = PydanticField(alias="produtoId")
    quantidade: int
    preco_unitario: Decimal = PydanticField(alias="precoUnitario")


class PagamentoResposta(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    status: StatusPagamento
    referencia: str
    valor: Decimal
    payload: dict


class PedidoResposta(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    unidade_id: int = PydanticField(alias="unidadeId")
    canal_pedido: CanalPedido = PydanticField(alias="canalPedido")
    status: StatusPedido
    total: Decimal
    desconto_fidelidade: Decimal = PydanticField(
        default=Decimal("0.00"), alias="descontoFidelidade"
    )
    itens: list[ItemPedidoResposta]
    pagamento: PagamentoResposta | None = None


class ResultadoPagamento(SQLModel):
    resultado: ResultadoPagamentoMock


class AtualizarStatusPedido(SQLModel):
    status: StatusPedido


class CriarUnidade(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    nome: str = PydanticField(min_length=2, max_length=120)
    endereco: str = PydanticField(min_length=5, max_length=255)

    @field_validator("nome", "endereco")
    @classmethod
    def strip_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("O campo não pode ficar vazio.")
        return normalized


class UnidadeResposta(SQLModel):
    id: int
    nome: str
    endereco: str
    ativa: bool


class CriarProduto(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    nome: str = PydanticField(min_length=2, max_length=120)
    descricao: str | None = PydanticField(default=None, max_length=500)
    preco: Decimal = PydanticField(gt=0, max_digits=10, decimal_places=2)

    @field_validator("nome")
    @classmethod
    def strip_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("O nome do produto não pode ficar vazio.")
        return normalized


class ProdutoResposta(SQLModel):
    id: int
    nome: str
    descricao: str | None
    preco: Decimal
    ativo: bool


class ItemCardapio(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    produto_id: int = PydanticField(alias="produtoId")
    nome: str
    descricao: str | None
    preco: Decimal
    disponivel: bool


class MovimentoEstoqueEntrada(SQLModel):
    tipo: TipoMovimentoEstoque
    quantidade: int = PydanticField(gt=0)


class EstoqueResposta(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    unidade_id: int = PydanticField(alias="unidadeId")
    produto_id: int = PydanticField(alias="produtoId")
    quantidade: int


class AuditoriaResposta(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    usuario_id: int = PydanticField(alias="usuarioId")
    acao: str
    entidade: str
    entidade_id: str = PydanticField(alias="entidadeId")
    detalhes: str | None
    criado_em: datetime = PydanticField(alias="criadoEm")


class AtualizarConsentimento(SQLModel):
    consentido: bool


class ResgatarPontos(SQLModel):
    pedido_id: int = PydanticField(gt=0, alias="pedidoId")
    pontos: int = PydanticField(gt=0, multiple_of=100)


class MovimentoFidelidadeResposta(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    tipo: TipoMovimentoFidelidade
    pontos: int
    pedido_id: int | None = PydanticField(default=None, alias="pedidoId")
    criado_em: datetime = PydanticField(alias="criadoEm")


class FidelidadeResumo(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    consentido: bool
    pontos: int
    extrato: list[MovimentoFidelidadeResposta]


class ResgateResposta(SQLModel):
    model_config = ConfigDict(populate_by_name=True)

    pedido_id: int = PydanticField(alias="pedidoId")
    pontos_resgatados: int = PydanticField(alias="pontosResgatados")
    desconto: Decimal
    total_atualizado: Decimal = PydanticField(alias="totalAtualizado")
