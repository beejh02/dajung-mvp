import type { ApiClient } from "./client";
import type { MenuItemRead } from "../types/menu";

export interface MenuApi {
  listMenu(): Promise<MenuItemRead[]>;
  getMenuItem(menuItemId: string): Promise<MenuItemRead>;
}

export function createMenuApi(client: ApiClient): MenuApi {
  return {
    listMenu: () => client.get<MenuItemRead[]>("/menu"),
    getMenuItem: (menuItemId) => client.get<MenuItemRead>(`/menu/${encodeURIComponent(menuItemId)}`),
  };
}
