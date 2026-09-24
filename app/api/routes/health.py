from fastapi import APIRouter

router = APIRouter(tags=["Saúde da API"])


@router.get("/health", summary="Verificar se a API está ativa")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
