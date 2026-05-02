from typing import Any

from app.schemas import McpJsonSchema
from app.tools.base import ToolContext, ToolDefinition


def get_menu(arguments: dict[str, Any], context: ToolContext) -> Any:
    return {"items": context.backend.get_menu()}


tool = ToolDefinition(
    name="dajung.get_menu",
    description="다정 백엔드에서 현재 메뉴 목록을 조회합니다.",
    input_schema=McpJsonSchema(),
    output_schema=McpJsonSchema(
        properties={
            "items": {"type": "array", "description": "메뉴 목록"},
        },
        required=["items"],
    ),
    handler=get_menu,
)
