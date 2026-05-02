from fastapi import FastAPI, Header
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.adapter import ToolAdapter, ToolNotFoundError
from app.backend_client import BackendClient
from app.config import get_settings
from app.schemas import McpToolDescriptor, ToolCallRequest, ToolCallResponse, ToolError

settings = get_settings()
adapter = ToolAdapter(BackendClient(settings.backend_api_base_url))

app = FastAPI(title="다정 Fake MCP HTTP 서버", version="0.1.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "ok": False,
            "error": {
                "code": "invalid_request",
                "message": "요청 형식이 올바르지 않습니다.",
                "detail": jsonable_encoder(exc.errors()),
            },
        },
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "mcp-server", "environment": settings.app_env}


@app.get("/mcp/tools", response_model=list[McpToolDescriptor])
def list_tools() -> list[McpToolDescriptor]:
    return adapter.list_tools()


@app.post("/mcp/tools/call", response_model=ToolCallResponse)
def call_tool(
    payload: ToolCallRequest,
    authorization: str | None = Header(default=None),
) -> ToolCallResponse:
    access_token = _extract_bearer_token(authorization)
    try:
        return adapter.call_tool(payload.name, payload.arguments, access_token=access_token)
    except ToolNotFoundError as exc:
        return ToolCallResponse(
            ok=False,
            tool=payload.name,
            error=ToolError(code="tool_not_found", message=str(exc)),
        )


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    prefix = "Bearer "
    if authorization.startswith(prefix):
        return authorization.removeprefix(prefix).strip()
    return authorization.strip()
