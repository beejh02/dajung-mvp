from app.tools.admin import tool as list_recent_orders_tool
from app.tools.menu import tool as get_menu_tool
from app.tools.orders import tool as submit_order_tool
from app.tools.payments import tool as approve_dummy_payment_tool
from app.tools.receipts import tool as get_receipt_tool

ALL_TOOLS = [
    get_menu_tool,
    submit_order_tool,
    approve_dummy_payment_tool,
    get_receipt_tool,
    list_recent_orders_tool,
]

__all__ = ["ALL_TOOLS"]
