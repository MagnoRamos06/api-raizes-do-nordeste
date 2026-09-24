from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.audit import router as audit_router
from app.api.routes.catalog import router as catalog_router
from app.api.routes.fidelity import router as fidelity_router
from app.api.routes.health import router as health_router
from app.api.routes.orders import router as orders_router
from app.api.errors import install_error_handlers
app = FastAPI(
    title="Raízes do Nordeste - API",
    description="API de pedidos para a rede de lanchonetes Raízes do Nordeste.",
    version="0.1.0",
)
install_error_handlers(app)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(audit_router)
app.include_router(catalog_router)
app.include_router(fidelity_router)
app.include_router(orders_router)
