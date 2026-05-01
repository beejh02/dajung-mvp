export type UserRole = "user" | "admin";

export interface UserRead {
  id: string;
  email: string;
  name: string;
  phone: string | null;
  role: UserRole;
  points_balance: number;
  created_at: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  name: string;
  phone?: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  token_use: string;
  user: UserRead;
}

export interface AgentHandoffResponse {
  handoff_token: string;
  token_type: string;
  expires_in: number;
  expires_at: string;
}
