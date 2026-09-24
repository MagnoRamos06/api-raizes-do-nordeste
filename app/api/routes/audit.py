from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import select

from app.api.dependencies import SessionDependency, require_roles
from app.api.schemas import AuditoriaResposta
from app.domain.enums import PerfilUsuario
from app.infrastructure.models import Auditoria, Usuario


router = APIRouter(prefix="/auditoria", tags=["Auditoria"])
AdminUser = Annotated[
    Usuario,
    Depends(require_roles(PerfilUsuario.ADMIN)),
]


@router.get("", response_model=list[AuditoriaResposta])
def list_audit_events(
    _admin: AdminUser,
    session: SessionDependency,
    entidade: str | None = None,
    entidade_id: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[Auditoria]:
    statement = select(Auditoria)
    if entidade:
        statement = statement.where(Auditoria.entidade == entidade.upper())
    if entidade_id:
        statement = statement.where(Auditoria.entidade_id == entidade_id)
    statement = statement.order_by(Auditoria.criado_em.desc())
    statement = statement.offset((page - 1) * limit).limit(limit)
    return session.exec(statement).all()
