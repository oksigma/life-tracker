import type { WhereWatched } from "@/types/movie";

export { formatDate as formatWatchedOn, todayLocal } from "@/lib/dates";

export const WHERE_LABELS: Record<WhereWatched, string> = {
  cinema: "Cinema",
  home: "Home",
  streaming: "Streaming",
  other: "Other",
};

export const FIRST_FILM_YEAR = 1888;
