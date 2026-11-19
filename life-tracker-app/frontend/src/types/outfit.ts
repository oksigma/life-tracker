// Mirrors backend/app/modules/clothing/schemas.py

export type Outfit = {
  id: string;
  /** Calendar date, YYYY-MM-DD */
  worn_on: string;
  notes: string | null;
  /** API path to the full-size JPEG */
  photo_url: string;
  /** API path to the 400px JPEG thumbnail */
  thumbnail_url: string;
  created_at: string;
  updated_at: string;
};

export type OutfitList = {
  items: Outfit[];
  total: number;
};

export type OutfitUpdate = {
  worn_on?: string;
  notes?: string | null;
};
