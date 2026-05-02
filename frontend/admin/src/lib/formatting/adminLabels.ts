import type {
  OrderSource,
  OrderStatus,
  PaymentStatus,
  PointLedgerType,
} from "../../../../../shared/frontend-client/src";

export const orderSourceLabels: Record<OrderSource, string> = {
  kiosk_classic: "클래식 키오스크",
  kiosk_guided: "가이드 키오스크",
  kiosk_premium: "다정 프리미엄",
  ai_agent: "AI Agent",
  mcp: "MCP",
};

export const orderStatusLabels: Record<OrderStatus, string> = {
  draft: "초안",
  pending_payment: "결제 대기",
  paid: "결제 완료",
  completed: "완료",
  cancelled: "취소",
  failed: "실패",
};

export const paymentStatusLabels: Record<PaymentStatus, string> = {
  pending: "대기",
  approved: "승인",
  failed: "실패",
  refunded: "환불",
};

export const pointLedgerTypeLabels: Record<PointLedgerType, string> = {
  earn: "적립",
  spend: "사용",
  adjust: "조정",
};

export function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}
