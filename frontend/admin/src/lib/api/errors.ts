import { ApiError } from "../../../../../shared/frontend-client/src";

export function toKoreanApiError(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return "로그인이 필요하거나 세션이 만료되었습니다.";
    }
    if (error.status === 403) {
      return "관리자 권한이 필요합니다.";
    }
    if (error.status === 404) {
      return "요청한 데이터를 찾을 수 없습니다.";
    }
    if (error.status === 409) {
      return "현재 상태에서는 요청을 처리할 수 없습니다.";
    }
  }

  return fallback;
}
