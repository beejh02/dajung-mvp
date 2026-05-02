from typing import Any

from app.schemas import McpJsonSchema
from app.tools.base import ToolContext, ToolDefinition


def list_recent_orders(arguments: dict[str, Any], context: ToolContext) -> Any:
    limit = int(arguments.get("limit", 10))
    limit = min(max(limit, 1), 100)
    return {"orders": context.backend.list_recent_orders(context.access_token, limit)}


tool = ToolDefinition(
    name="dajung.list_recent_orders",
    description="관리자 권한으로 최근 주문 목록을 조회합니다.",
    input_schema=McpJsonSchema(
        properties={
            "limit": {"type": "integer", "minimum": 1, "maximum": 100, "description": "조회할 주문 수입니다."},
        },
    ),
    output_schema=McpJsonSchema(
        properties={
            "orders": {"type": "array", "description": "최근 주문 목록입니다."},
        },
        required=["orders"],
    ),
    handler=list_recent_orders,
)
