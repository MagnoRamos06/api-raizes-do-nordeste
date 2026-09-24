from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.api.dependencies import CurrentUser, SessionDependency, require_roles
from app.api.schemas import (
    CadastroOperador,
    CadastroUsuario,
    LoginUsuario,
    TokenResposta,
    UsuarioPublico,
)
from app.application.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    hash_password,
    verify_password,
)
from app.domain.enums import PerfilUsuario
from app.infrastructure.models import Auditoria, ConsentimentoFidelidade, Usuario


router = APIRouter(prefix="/auth", tags=["Autenticação"])
AdminUser = Annotated[
    Usuario,
    Depends(require_roles(PerfilUsuario.ADMIN)),
]


@router.post(
    "/cadastro",
    response_model=UsuarioPublico,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar um cliente",
)
def register_user(data: CadastroUsuario, session: SessionDependency) -> Usuario:
    user = Usuario(
        nome=data.nome,
        email=str(data.email).lower(),
        senha_hash=hash_password(data.senha),
        # Cadastro público sempre cria CLIENTE; perfis internos serão criados por ADMIN.
        perfil=PerfilUsuario.CLIENTE,
    )
    session.add(user)
    try:
        session.flush()
        session.add(
            ConsentimentoFidelidade(
                usuario_id=user.id,
                consentido=data.consentimento_fidelidade,
            )
        )
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta com este e-mail.",
        )
    session.refresh(user)
    return user


@router.post(
    "/login",
    response_model=TokenResposta,
    summary="Autenticar e obter token de acesso",
)
def login(data: LoginUsuario, session: SessionDependency) -> TokenResposta:
    user = session.exec(
        select(Usuario).where(Usuario.email == str(data.email).lower())
    ).first()
    if user is None:
        verify_password(data.senha, DUMMY_PASSWORD_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(data.senha, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResposta(access_token=create_access_token(user.id))


@router.get(
    "/me",
    response_model=UsuarioPublico,
    summary="Consultar o usuário autenticado",
)
def read_current_user(current_user: CurrentUser) -> Usuario:
    return current_user


@router.post(
    "/usuarios-operacionais",
    response_model=UsuarioPublico,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar usuário interno com perfil operacional",
)
def create_operational_user(
    data: CadastroOperador,
    current_user: AdminUser,
    session: SessionDependency,
) -> Usuario:
    if data.perfil in (PerfilUsuario.CLIENTE, PerfilUsuario.ADMIN):
        raise HTTPException(
            status_code=422,
            detail="O cadastro operacional aceita apenas ATENDENTE, COZINHA ou GERENTE.",
        )
    user = Usuario(
        nome=data.nome,
        email=str(data.email).lower(),
        senha_hash=hash_password(data.senha),
        perfil=data.perfil,
    )
    session.add(user)
    try:
        session.flush()
        session.add(
            Auditoria(
                usuario_id=current_user.id,
                acao="USUARIO_OPERACIONAL_CRIADO",
                entidade="USUARIO",
                entidade_id=str(user.id),
                detalhes=f"perfil={data.perfil.value}",
            )
        )
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Já existe uma conta com este e-mail.",
        )
    session.refresh(user)
    return user
