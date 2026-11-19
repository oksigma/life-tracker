import { apiUrl } from "@/lib/api";

type ApiImageProps = {
  path: string;
  alt: string;
  className?: string;
  loading?: "lazy" | "eager";
};

/** An image served by the backend (already resized/optimised there). */
export function ApiImage({ path, alt, className, loading = "lazy" }: ApiImageProps) {
  // eslint-disable-next-line @next/next/no-img-element -- backend serves pre-sized JPEGs
  return <img src={apiUrl(path)} alt={alt} className={className} loading={loading} decoding="async" />;
}
