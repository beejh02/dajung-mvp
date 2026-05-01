import type { ApiClient } from "./client";
import type { PointBalanceRead, PointLedgerRead } from "../types/points";

export interface PointsApi {
  getMyPoints(): Promise<PointBalanceRead>;
  listPointLedger(): Promise<PointLedgerRead[]>;
}

export function createPointsApi(client: ApiClient): PointsApi {
  return {
    getMyPoints: () => client.get<PointBalanceRead>("/points/me"),
    listPointLedger: () => client.get<PointLedgerRead[]>("/points/ledger"),
  };
}
