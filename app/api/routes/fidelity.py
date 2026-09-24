from fastapi import APIRouter

from app.api.dependencies import CurrentUser, SessionDependency
from app.api.schemas import (
    AtualizarConsentimento,
    FidelidadeResumo,
    ResgateResposta,
    ResgatarPontos,
)
from app.application.fidelity import get_summary, record_consent, redeem_points


router = APIRouter(prefix="/fidelidade", tags=["Fidelidade e consentimento"])


@router.get("/me", response_model=FidelidadeResumo)
def read_fidelity_summary(
    current_user: CurrentUser,
    session: SessionDependency,
) -> FidelidadeResumo:
    return get_summary(current_user, session)


@router.post("/consentimento", response_model=FidelidadeResumo)
def update_fidelity_consent(
    data: AtualizarConsentimento,
    current_user: CurrentUser,
    session: SessionDependency,
) -> FidelidadeResumo:
    return record_consent(current_user, data.consentido, session)


@router.post("/resgates", response_model=ResgateResposta)
def redeem_fidelity_points(
    data: ResgatarPontos,
    current_user: CurrentUser,
    session: SessionDependency,
) -> ResgateResposta:
    return redeem_points(current_user, data.pedido_id, data.pontos, session)
