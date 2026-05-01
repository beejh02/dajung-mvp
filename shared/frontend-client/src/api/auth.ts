import type { ApiClient } from "./client";
import type {
  AgentHandoffResponse,
  LoginRequest,
  SignupRequest,
  TokenResponse,
  UserRead,
} from "../types/auth";

export interface AuthApi {
  login(payload: LoginRequest): Promise<TokenResponse>;
  signup(payload: SignupRequest): Promise<TokenResponse>;
  getCurrentUser(): Promise<UserRead>;
  createAgentHandoff(): Promise<AgentHandoffResponse>;
}

export function createAuthApi(client: ApiClient): AuthApi {
  return {
    login: (payload) => client.post<TokenResponse, LoginRequest>("/auth/login", payload),
    signup: (payload) => client.post<TokenResponse, SignupRequest>("/auth/signup", payload),
    getCurrentUser: () => client.get<UserRead>("/auth/me"),
    createAgentHandoff: () => client.post<AgentHandoffResponse>("/auth/agent-handoff"),
  };
}
