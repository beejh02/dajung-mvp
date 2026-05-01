export interface MenuOptionChoice {
  id: string;
  name: string;
  price_delta: number;
  is_available: boolean;
}

export interface MenuOptionGroup {
  id: string;
  name: string;
  required: boolean;
  min_select: number;
  max_select: number;
  choices: MenuOptionChoice[];
}

export interface MenuItemRead {
  id: string;
  brand_id: string | null;
  name: string;
  category: string;
  description: string | null;
  price: number;
  image_url: string | null;
  is_available: boolean;
  ingredients: string[];
  options: MenuOptionGroup[];
}
