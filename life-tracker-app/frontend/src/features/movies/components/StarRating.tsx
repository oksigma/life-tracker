"use client";

const STARS = [1, 2, 3, 4, 5];

export function StarDisplay({ rating }: { rating: number | null }) {
  if (rating === null) return <span className="text-sm text-slate-400">Not rated</span>;
  return (
    <span className="text-amber-500" aria-label={`${rating} out of 5 stars`} title={`${rating}/5`}>
      {STARS.map((star) => (star <= rating ? "★" : "☆")).join("")}
    </span>
  );
}

type StarInputProps = {
  value: number | null;
  onChange: (value: number | null) => void;
};

/** Click a star to set the rating; click the current rating again to clear it. */
export function StarInput({ value, onChange }: StarInputProps) {
  return (
    <div className="flex items-center gap-1" role="radiogroup" aria-label="Rating">
      {STARS.map((star) => (
        <button
          key={star}
          type="button"
          role="radio"
          aria-checked={value === star}
          aria-label={`${star} star${star > 1 ? "s" : ""}`}
          onClick={() => onChange(value === star ? null : star)}
          className={`text-2xl leading-none ${value !== null && star <= value ? "text-amber-500" : "text-slate-300"} hover:text-amber-400`}
        >
          ★
        </button>
      ))}
      {value !== null && (
        <button type="button" onClick={() => onChange(null)} className="ml-2 text-xs text-slate-500 underline">
          Clear
        </button>
      )}
    </div>
  );
}
