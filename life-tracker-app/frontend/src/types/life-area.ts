// Keep in sync with the backend modules in backend/app/modules/.
export const LIFE_AREAS = ["clothing", "health", "movies", "food", "drinks"] as const;

export type LifeArea = (typeof LIFE_AREAS)[number];
