/**
 * Firebase Auth 에러 코드 → 한국어 메시지 매핑.
 * 사용처: components/auth/* 의 form catch 블록.
 */

const MAP: Record<string, string> = {
  // === 로그인 관련 ===
  "auth/invalid-email": "이메일 형식이 올바르지 않습니다.",
  "auth/user-disabled": "비활성화된 계정입니다. 관리자에게 문의해 주세요.",
  "auth/user-not-found": "등록되지 않은 이메일입니다.",
  "auth/wrong-password": "비밀번호가 일치하지 않습니다.",
  "auth/invalid-credential": "이메일 또는 비밀번호가 올바르지 않습니다.",
  "auth/invalid-login-credentials": "이메일 또는 비밀번호가 올바르지 않습니다.",

  // === 회원가입 관련 ===
  "auth/email-already-in-use": "이미 가입된 이메일입니다. 로그인해 주세요.",
  "auth/weak-password": "비밀번호는 최소 8자 이상이어야 합니다.",
  "auth/operation-not-allowed":
    "이 로그인 방식은 현재 사용할 수 없습니다. 관리자에게 문의해 주세요.",

  // === 소셜 로그인 ===
  "auth/popup-closed-by-user":
    "로그인 창이 닫혔습니다. 다시 시도해 주세요.",
  "auth/popup-blocked":
    "팝업이 차단되었습니다. 브라우저 설정에서 팝업을 허용해 주세요.",
  "auth/cancelled-popup-request": "이전 로그인 시도를 취소했습니다.",
  "auth/account-exists-with-different-credential":
    "다른 로그인 방식으로 이미 가입된 이메일입니다.",
  "auth/unauthorized-domain":
    "이 도메인에서는 로그인이 허용되지 않습니다.",

  // === 비밀번호 재설정 ===
  "auth/missing-email": "이메일을 입력해 주세요.",
  "auth/expired-action-code": "재설정 링크가 만료되었습니다. 다시 요청해 주세요.",
  "auth/invalid-action-code": "유효하지 않은 링크입니다.",

  // === 네트워크/한도 ===
  "auth/network-request-failed":
    "네트워크 오류입니다. 연결 상태를 확인해 주세요.",
  "auth/too-many-requests":
    "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.",
  "auth/internal-error": "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",

  // === 토큰/세션 ===
  "auth/id-token-expired": "세션이 만료되었습니다. 다시 로그인해 주세요.",
  "auth/id-token-revoked": "세션이 해지되었습니다. 다시 로그인해 주세요.",
  "auth/session-cookie-expired": "세션이 만료되었습니다. 다시 로그인해 주세요.",
  "auth/session-cookie-revoked": "세션이 해지되었습니다. 다시 로그인해 주세요.",
};

export function translateAuthError(err: unknown): string {
  if (typeof err === "object" && err !== null && "code" in err) {
    const code = String((err as { code: unknown }).code);
    if (MAP[code]) return MAP[code];
  }
  if (err instanceof Error && err.message) return err.message;
  return "로그인 중 오류가 발생했습니다.";
}

/** 비밀번호 강도 검증 (회원가입) */
export function validatePassword(pw: string): string | null {
  if (pw.length < 8) return "비밀번호는 최소 8자 이상이어야 합니다.";
  if (!/[a-z]/.test(pw)) return "비밀번호에 소문자를 포함해 주세요.";
  if (!/\d/.test(pw)) return "비밀번호에 숫자를 포함해 주세요.";
  return null;
}

/** 이메일 형식 빠른 검증 */
export function validateEmail(email: string): string | null {
  if (!email.trim()) return "이메일을 입력해 주세요.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
    return "이메일 형식이 올바르지 않습니다.";
  return null;
}
