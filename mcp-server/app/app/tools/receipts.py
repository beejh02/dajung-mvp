from typing import Any

from app.schemas import McpJsonSchema
from app.tools.base import ToolContext, ToolDefinition


def get_receipt(arguments: dict[str, Any], context: ToolContext) -> Any:
    return context.backend.get_receipt(context.access_token, int(arguments["order_id"]))


tool = ToolDefinition(
    name="dajung.get_receipt",
    description="주문 ID로 백엔드 영수증을 조회합니다.",
    input_schema=McpJsonSchema(
        properties={
            "order_id": {"type": "integer", "description": "영수증을 조회할 주문 ID입니다."},
        },
        required=["order_id"],
    ),
    output_schema=McpJsonSchema(
        properties={
            "id": {"type": "integer"},
            "order_id": {"type": "integer"},
            "receipt_number": {"type": "string"},
            "content": {"type": "object"},
            "issued_at": {"type": "string"},
        },
        required=["id", "order_id", "receipt_number", "content", "issued_at"],
    ),
    handler=get_receipt,
)
