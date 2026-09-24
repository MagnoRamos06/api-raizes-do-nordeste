from decimal import Decimal

from sqlmodel import Session, select

from app.application.contracts import (
    FidelidadeResumo,
    MovimentoFidelidadeResposta,
    ResgateResposta,
)
from app.application.errors import ApplicationError
from app.domain.enums import (
    PerfilUsuario,
    StatusPedido,
    TipoMovimentoFidelidade,
)
from app.infrastructure.models import (
    Auditoria,
    ConsentimentoFidelidade,
    MovimentoFidelidade,
    Pedido,
    Usuario,
)


POINTS_PER_CURRENCY_UNIT = Decimal("0.05")
PAID_CURRENCY_UNITS_PER_POINT = Decimal("1.00")


def _has_consent(user_id: int, session: Session) -> bool:
    latest = session.exec(
        select(ConsentimentoFidelidade)
        .where(ConsentimentoFidelidade.usuario_id == user_id)
        .order_by(ConsentimentoFidelidade.id.desc())
        .limit(1)
    ).first()
    return bool(latest and latest.consentido)


def _balance(user_id: int, session: Session) -> int:
    movements = session.exec(
        select(MovimentoFidelidade).where(MovimentoFidelidade.usuario_id == user_id)
    ).all()
    earned = sum(
        row.pontos
        for row in movements
        if row.tipo in (TipoMovimentoFidelidade.GANHO, TipoMovimentoFidelidade.ESTORNO)
    )
    redeemed = sum(
        row.pontos
        for row in movements
        if row.tipo == TipoMovimentoFidelidade.RESGATE
    )
    return earned - redeemed


def get_summary(user: Usuario, session: Session) -> FidelidadeResumo:
    if user.perfil != PerfilUsuario.CLIENTE:
        raise ApplicationError(403, "FORBIDDEN", "A fidelidade está disponível para clientes.")
    consented = _has_consent(user.id, session)
    movements = session.exec(
        select(MovimentoFidelidade)
        .where(MovimentoFidelidade.usuario_id == user.id)
        .order_by(MovimentoFidelidade.criado_em.desc())
        .limit(50)
    ).all()
    return FidelidadeResumo(
        consentido=consented,
        pontos=_balance(user.id, session),
        extrato=[
            MovimentoFidelidadeResposta(
                tipo=row.tipo,
                pontos=row.pontos,
                pedido_id=row.pedido_id,
                criado_em=row.criado_em,
            )
            for row in movements
        ],
    )


def record_consent(user: Usuario, consented: bool, session: Session) -> FidelidadeResumo:
    if user.perfil != PerfilUsuario.CLIENTE:
        raise ApplicationError(403, "FORBIDDEN", "A fidelidade está disponível para clientes.")
    session.add(
        ConsentimentoFidelidade(usuario_id=user.id, consentido=consented)
    )
    session.add(
        Auditoria(
            usuario_id=user.id,
            acao="CONSENTIMENTO_FIDELIDADE_ATUALIZADO",
            entidade="CONSENTIMENTO_FIDELIDADE",
            entidade_id=str(user.id),
            detalhes=f"consentido={consented}",
        )
    )
    session.commit()
    return get_summary(user, session)


def redeem_points(
    user: Usuario,
    order_id: int,
    points: int,
    session: Session,
) -> ResgateResposta:
    if user.perfil != PerfilUsuario.CLIENTE:
        raise ApplicationError(403, "FORBIDDEN", "A fidelidade está disponível para clientes.")
    if not _has_consent(user.id, session):
        raise ApplicationError(
            409,
            "CONSENT_REQUIRED",
            "É necessário consentir com o programa de fidelidade antes do resgate.",
        )
    order = session.get(Pedido, order_id)
    if order is None:
        raise ApplicationError(404, "NOT_FOUND", "Pedido não encontrado.")
    if order.usuario_id != user.id:
        raise ApplicationError(403, "FORBIDDEN", "Este pedido pertence a outro cliente.")
    if order.status != StatusPedido.AGUARDANDO_PAGAMENTO:
        raise ApplicationError(409, "ORDER_STATE_CONFLICT", "O pedido não aceita mais resgate de pontos.")
    existing = session.exec(
        select(MovimentoFidelidade).where(
            MovimentoFidelidade.pedido_id == order.id,
            MovimentoFidelidade.tipo == TipoMovimentoFidelidade.RESGATE,
        )
    ).first()
    if existing:
        raise ApplicationError(409, "ORDER_STATE_CONFLICT", "Já existe resgate aplicado neste pedido.")
    if points > _balance(user.id, session):
        raise ApplicationError(409, "LOYALTY_BALANCE_CONFLICT", "Saldo de pontos insuficiente.")

    discount = (Decimal(points) * POINTS_PER_CURRENCY_UNIT).quantize(Decimal("0.01"))
    if discount >= order.total:
        raise ApplicationError(
            409,
            "REDEMPTION_CONFLICT",
            "O resgate precisa deixar um valor positivo para pagamento.",
        )

    order.total -= discount
    order.desconto_fidelidade += discount
    session.add(order)
    session.add(
        MovimentoFidelidade(
            usuario_id=user.id,
            pedido_id=order.id,
            tipo=TipoMovimentoFidelidade.RESGATE,
            pontos=points,
        )
    )
    session.add(
        Auditoria(
            usuario_id=user.id,
            acao="PONTOS_RESGATADOS",
            entidade="PEDIDO",
            entidade_id=str(order.id),
            detalhes=f"pontos={points};desconto={discount}",
        )
    )
    session.commit()
    return ResgateResposta(
        pedido_id=order.id,
        pontos_resgatados=points,
        desconto=discount,
        total_atualizado=order.total,
    )


def apply_payment_points(
    order: Pedido,
    approved: bool,
    session: Session,
) -> None:
    if approved:
        if not _has_consent(order.usuario_id, session):
            return
        existing = session.exec(
            select(MovimentoFidelidade).where(
                MovimentoFidelidade.pedido_id == order.id,
                MovimentoFidelidade.tipo == TipoMovimentoFidelidade.GANHO,
            )
        ).first()
        if existing:
            return
        points = int(order.total // PAID_CURRENCY_UNITS_PER_POINT)
        if points > 0:
            session.add(
                MovimentoFidelidade(
                    usuario_id=order.usuario_id,
                    pedido_id=order.id,
                    tipo=TipoMovimentoFidelidade.GANHO,
                    pontos=points,
                )
            )
        return

    redemption = session.exec(
        select(MovimentoFidelidade).where(
            MovimentoFidelidade.pedido_id == order.id,
            MovimentoFidelidade.tipo == TipoMovimentoFidelidade.RESGATE,
        )
    ).first()
    if redemption:
        session.add(
            MovimentoFidelidade(
                usuario_id=order.usuario_id,
                pedido_id=order.id,
                tipo=TipoMovimentoFidelidade.ESTORNO,
                pontos=redemption.pontos,
            )
        )
