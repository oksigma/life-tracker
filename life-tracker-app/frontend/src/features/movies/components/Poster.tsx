import { posterUrl, type PosterSize } from "@/lib/tmdb";

type PosterProps = {
  path: string | null | undefined;
  title: string;
  size?: PosterSize;
  className?: string;
};

/** A movie poster from TMDB, or a placeholder when there isn't one. */
export function Poster({ path, title, size = "w185", className = "" }: PosterProps) {
  if (!path) {
    return (
      <span className={`flex items-center justify-center rounded bg-slate-100 text-slate-400 ${className}`} aria-hidden>
        🎬
      </span>
    );
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element -- posters are served by TMDB's image CDN
    <img
      src={posterUrl(path, size)}
      alt={`Poster for ${title}`}
      loading="lazy"
      decoding="async"
      className={`rounded bg-slate-100 object-cover ${className}`}
    />
  );
}
