import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.application.errors import ApplicationError

logger = logging.getLogger("raizes.api")


def _error_body(
    request: Request,
    error: str,
    message: str,
    details: list[dict[str, str]] | None = None,
) -> dict:
    return {
        "error": error,
        "message": message,
        "details": details or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "requestId": getattr(request.state, "request_id", None),
    }


def install_error_handlers(app: FastAPI) -> None:
    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException):
        errors = {
            401: "UNAUTHENTICATED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
        }
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content=_error_body(
                request,
                errors.get(exc.status_code, "REQUEST_ERROR"),
                mensagem_http(exc.detail),
            ),
        )

    @app.exception_handler(ApplicationError)
    async def handle_application_error(request: Request, exc: ApplicationError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(request, exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        details = [
            {
                "field": ".".join(str(part) for part in error["loc"] if part != "body"),
                "issue": mensagem_validacao(error),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_body(
                request,
                "VALIDATION_ERROR",
                "Um ou mais campos são inválidos.",
                details,
            ),
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(request: Request, _exc: IntegrityError):
        return JSONResponse(
            status_code=409,
            content=_error_body(
                request,
                "CONFLICT",
                "A operação conflita com dados já registrados ou com uma regra de integridade.",
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception(
            "Erro inesperado na API; request_id=%s", request.state.request_id
        )
        return JSONResponse(
            status_code=500,
            content=_error_body(
                request,
                "INTERNAL_ERROR",
                "Ocorreu um erro interno. Informe o requestId ao suporte.",
            ),
        )


class DetalheErro(BaseModel):
    field: str
    issue: str


class RespostaErro(BaseModel):
    error: str
    message: str
    details: list[DetalheErro] = Field(default_factory=list)
    timestamp: datetime
    path: str
    requestId: str | None = None


def mensagem_http(detail) -> str:
    return {"Not Found": "Rota não encontrada.", "Method Not Allowed": "Método não permitido nesta rota.",
            "Unauthorized": "Autenticação necessária.", "Forbidden": "Acesso não permitido."}.get(str(detail), str(detail))


def mensagem_validacao(error: dict) -> str:
    tipo = error.get("type", "")
    contexto = error.get("ctx") or {}
    mensagens = {
        "missing": "Campo obrigatório.", "string_type": "Informe um texto.",
        "int_type": "Informe um número inteiro.", "int_parsing": "Informe um número inteiro válido.",
        "int_from_float": "Informe um número inteiro, sem casas decimais.",
        "float_parsing": "Informe um número válido.", "decimal_parsing": "Informe um valor decimal válido.",
        "decimal_type": "Informe um valor decimal.", "finite_number": "Informe um número finito.",
        "bool_parsing": "Informe verdadeiro ou falso.", "bool_type": "Informe verdadeiro ou falso.",
        "list_type": "Informe uma lista.", "enum": "Selecione um dos valores permitidos para o campo.",
        "json_invalid": "O corpo da requisição deve conter um JSON válido.",
        "model_attributes_type": "Informe um objeto JSON válido.",
        "decimal_max_digits": "O valor excede o limite de dígitos permitido.",
        "decimal_max_places": "O valor excede o limite de casas decimais permitido.",
        "decimal_whole_digits": "A parte inteira excede o limite permitido.",
    }
    if tipo in mensagens:
        return mensagens[tipo]
    if tipo in ("string_too_short", "too_short"):
        return f"Informe pelo menos {contexto.get('min_length')} caracteres ou itens."
    if tipo in ("string_too_long", "too_long"):
        return f"Informe no máximo {contexto.get('max_length')} caracteres ou itens."
    limites = {"greater_than": ("maior que", "gt"), "greater_than_equal": ("maior ou igual a", "ge"),
               "less_than": ("menor que", "lt"), "less_than_equal": ("menor ou igual a", "le")}
    if tipo in limites:
        texto, chave = limites[tipo]
        return f"Informe um valor {texto} {contexto.get(chave)}."
    if tipo == "multiple_of":
        return f"Informe um múltiplo de {contexto.get('multiple_of')}."
    if "email" in error.get("loc", ()):
        return "Informe um endereço de e-mail válido."
    if tipo == "value_error" and isinstance(contexto.get("error"), ValueError):
        return str(contexto["error"])
    return "Valor inválido para este campo."


def install_openapi(app: FastAPI) -> None:
    # Cada operação descreve os mesmos envelopes usados pelos tratadores HTTP.
    codigos = {
        ("/auth/cadastro", "post"): [409], ("/auth/login", "post"): [401],
        ("/auth/usuarios-operacionais", "post"): [403, 409],
        ("/unidades", "post"): [403, 409], ("/produtos", "post"): [403, 409],
        ("/unidades/{unidade_id}/cardapio", "get"): [404],
        ("/unidades/{unidade_id}/estoque", "get"): [403, 404],
        ("/unidades/{unidade_id}/estoque/{produto_id}/movimentacoes", "post"): [403, 404, 409],
        ("/pedidos", "post"): [403, 404, 409],
        ("/pedidos/{pedido_id}/pagamento-mock", "post"): [403, 404, 409],
        ("/pedidos/{pedido_id}/status", "patch"): [403, 404, 409],
        ("/fidelidade/me", "get"): [403], ("/fidelidade/consentimento", "post"): [403, 409],
        ("/fidelidade/resgates", "post"): [403, 404, 409], ("/auditoria", "get"): [403],
    }
    descricoes = {401: "Autenticação ausente ou inválida.", 403: "Perfil sem permissão.",
                  404: "Recurso não encontrado.", 409: "Conflito com uma regra de negócio ou integridade.",
                  422: "Dados de entrada inválidos.", 500: "Erro interno sem exposição de informações sensíveis."}
    codigos_erro = {401: "UNAUTHENTICATED", 403: "FORBIDDEN", 404: "NOT_FOUND", 409: "CONFLICT", 422: "VALIDATION_ERROR", 500: "INTERNAL_ERROR"}
    resumos = {("/unidades", "get"): "Listar unidades", ("/unidades", "post"): "Cadastrar unidade",
               ("/produtos", "get"): "Listar produtos", ("/produtos", "post"): "Cadastrar produto",
               ("/unidades/{unidade_id}/estoque", "get"): "Consultar estoque da unidade",
               ("/fidelidade/me", "get"): "Consultar saldo e extrato de pontos",
               ("/fidelidade/consentimento", "post"): "Registrar consentimento para fidelidade",
               ("/fidelidade/resgates", "post"): "Resgatar pontos", ("/auditoria", "get"): "Consultar auditoria"}
    def gerar():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
        modelos = schema.setdefault("components", {}).setdefault("schemas", {})
        erro = RespostaErro.model_json_schema(ref_template="#/components/schemas/{model}")
        modelos.update(erro.pop("$defs", {})); modelos["RespostaErro"] = erro
        for rota, metodos in schema["paths"].items():
            for metodo, operacao in metodos.items():
                if metodo not in ("get", "post", "patch", "put", "delete"):
                    continue
                cods = set(codigos.get((rota, metodo), [])) | {500}
                if operacao.get("security"): cods.add(401)
                if operacao.get("parameters") or operacao.get("requestBody"): cods.add(422)
                if (rota, metodo) in resumos: operacao["summary"] = resumos[(rota, metodo)]
                for codigo in cods:
                    operacao["responses"][str(codigo)] = {
                        "description": descricoes[codigo], "content": {"application/json": {
                            "schema": {"$ref": "#/components/schemas/RespostaErro"},
                            "example": {"error": codigos_erro[codigo], "message": descricoes[codigo],
                                "details": [{"field": "canalPedido", "issue": "Campo obrigatório."}] if codigo == 422 else [],
                                "timestamp": "2026-09-25T12:00:00Z", "path": rota, "requestId": "identificador-da-requisicao"}}}}
        modelos.pop("HTTPValidationError", None); modelos.pop("ValidationError", None)
        app.openapi_schema = schema
        return schema
    app.openapi = gerar
