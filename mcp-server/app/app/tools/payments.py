from typing import Any

from app.schemas import McpJsonSchema
from app.tools.base import ToolContext, ToolDefinition


def approve_dummy_payment(arguments: dict[str, Any], context: ToolContext) -> Any:
    payload = {
        "order_id": arguments.get("order_id"),
        "idempotency_key": arguments.get("idempotency_key"),
        "simulate_failure": bool(arguments.get("simulate_failure", False)),
    }
    return context.backend.approve_dummy_payment(context.access_token, payload)


tool = ToolDefinition(
    name="dajung.approve_dummy_payment",
    description="기존 백엔드 더미 결제 승인 API를 호출합니다.",
    input_schema=McpJsonSchema(
        properties={
            "order_id": {"type": "integer", "description": "결제를 승인할 주문 ID입니다."},
            "idempotency_key": {"type": "string", "description": "재시도 중복 방지 키입니다."},
            "simulate_failure": {"type": "boolean", "description": "더미 결제 실패 케이스를 요청합니다."},
        },
        required=["order_id"],
    ),
    output_schema=McpJsonSchema(
        properties={
            "id": {"type": "integer"},
            "order_id": {"type": "integer"},
            "status": {"type": "string"},
            "approved_amount": {"type": "integer"},
            "dummy_approval_code": {"type": "string"},
        },
        required=["id", "order_id", "status", "approved_amount"],
    ),
    handler=approve_dummy_payment,
)
