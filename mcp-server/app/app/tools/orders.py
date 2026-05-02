from typing import Any

from app.schemas import McpJsonSchema
from app.tools.base import ToolContext, ToolDefinition


def submit_order(arguments: dict[str, Any], context: ToolContext) -> Any:
    payload = {
        "source": arguments.get("source", "mcp"),
        "items": arguments.get("items", []),
        "simulate_failure": bool(arguments.get("simulate_failure", False)),
    }
    return context.backend.submit_order(context.access_token, payload)


tool = ToolDefinition(
    name="dajung.submit_order",
    description="다정 백엔드 주문 API로 주문을 제출합니다. 가격 계산과 검증은 백엔드가 수행합니다.",
    input_schema=McpJsonSchema(
        properties={
            "source": {
                "type": "string",
                "description": "주문 출처입니다. 기본값은 mcp입니다.",
                "enum": ["mcp", "ai_agent", "kiosk_premium", "kiosk_classic", "kiosk_guided"],
            },
            "items": {
                "type": "array",
                "description": "주문 상품 목록입니다.",
                "items": {
                    "type": "object",
                    "properties": {
                        "menu_item_id": {"type": "string"},
                        "quantity": {"type": "integer", "minimum": 1},
                        "selected_options": {"type": "array"},
                    },
                    "required": ["menu_item_id", "quantity"],
                },
            },
            "simulate_failure": {"type": "boolean", "description": "더미 실패 케이스를 요청합니다."},
        },
        required=["items"],
    ),
    output_schema=McpJsonSchema(
        properties={
            "id": {"type": "integer"},
            "source": {"type": "string"},
            "status": {"type": "string"},
            "total_amount": {"type": "integer"},
            "items": {"type": "array"},
        },
        required=["id", "source", "status", "total_amount", "items"],
    ),
    handler=submit_order,
)
