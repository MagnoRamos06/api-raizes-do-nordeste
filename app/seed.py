from decimal import Decimal

from sqlmodel import Session, select

from app.application.security import hash_password
from app.config import settings
from app.domain.enums import PerfilUsuario
from app.infrastructure import models  # Ensure all tables are registered.
from app.infrastructure.database import engine
from app.infrastructure.models import Estoque, Produto, Unidade, Usuario


def main() -> None:
    admin_email = settings.seed_admin_email.strip().lower()
    admin_password = settings.seed_admin_password
    if not admin_email or len(admin_password) < 12:
        raise SystemExit(
            "Configure SEED_ADMIN_EMAIL e SEED_ADMIN_PASSWORD (mínimo 12 caracteres) no .env."
        )

    with Session(engine) as session:
        admin = session.exec(
            select(Usuario).where(Usuario.email == admin_email)
        ).first()
        if admin is None:
            admin = Usuario(
                nome="Administrador da Rede",
                email=admin_email,
                senha_hash=hash_password(admin_password),
                perfil=PerfilUsuario.ADMIN,
            )
            session.add(admin)
        elif admin.perfil != PerfilUsuario.ADMIN:
            raise SystemExit(
                "O e-mail informado já pertence a um usuário sem perfil ADMIN. Use outro e-mail."
            )

        unit = session.exec(
            select(Unidade).where(Unidade.nome == "Unidade Demonstracao")
        ).first()
        if unit is None:
            unit = Unidade(
                nome="Unidade Demonstracao",
                endereco="Endereco de demonstracao, 100",
            )
            session.add(unit)
            session.flush()

        product = session.exec(
            select(Produto).where(Produto.nome == "Sanduiche Demonstracao")
        ).first()
        if product is None:
            product = Produto(
                nome="Sanduiche Demonstracao",
                descricao="Produto inicial para validar o fluxo do MVP.",
                preco=Decimal("25.00"),
            )
            session.add(product)
            session.flush()

        stock = session.exec(
            select(Estoque).where(
                Estoque.unidade_id == unit.id,
                Estoque.produto_id == product.id,
            )
        ).first()
        if stock is None:
            session.add(
                Estoque(unidade_id=unit.id, produto_id=product.id, quantidade=30)
            )
        session.commit()

    print("Dados de demonstração preparados.")
    print(f"Administrador: {admin_email}")
    print("Unidade: Unidade Demonstracao | Produto: Sanduiche Demonstracao | Saldo inicial: 30")


if __name__ == "__main__":
    main()
