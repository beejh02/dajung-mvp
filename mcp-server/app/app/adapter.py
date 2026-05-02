from typing import Any

from app.backend_client import BackendApiError, BackendClient
from app.schemas import McpToolDescriptor, ToolCallResponse, ToolError
from app.tools import ALL_TOOLS
from app.tools.base import ToolContext, ToolDefinition


class ToolNotFoundError(ValueError):
    pass


class ToolAdapter:
    def __init__(self, backend: BackendClient) -> None:
        self.backend = backend
        self._tools: dict[str, ToolDefinition] = {tool.name: tool for tool in ALL_TOOLS}

    def list_tools(self) -> list[McpToolDescriptor]:
        return [tool.descriptor() for tool in self._tools.values()]

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        access_token: str | None = None,
    ) -> ToolCallResponse:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(f"등록되지 않은 tool입니다: {name}")

        try:
            content = tool.handler(arguments, ToolContext(backend=self.backend, access_token=access_token))
            return ToolCallResponse(ok=True, tool=name, content=content)
        except BackendApiError as exc:
            return ToolCallResponse(
                ok=False,
                tool=name,
                error=ToolError(
                    code="backend_api_error",
                    message=f"백엔드 API 오류: {exc}",
                    backend_status=exc.status_code,
                    detail=exc.detail,
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            return ToolCallResponse(
                ok=False,
                tool=name,
                error=ToolError(
                    code="invalid_arguments",
                    message=f"tool 입력값이 올바르지 않습니다: {exc}",
                ),
            )
