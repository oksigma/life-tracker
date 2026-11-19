import Link from "next/link";
import { SignOutButton } from "@/features/auth/SignOutButton";
import { LIFE_AREAS } from "@/types/life-area";

export default function Home() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-3xl font-semibold">LifeTracker</h1>
        <SignOutButton />
      </div>
      <Link
        href="/calendar"
        className="mt-6 flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 hover:border-slate-400"
      >
        <span className="font-medium">
          <span aria-hidden>📅</span> Calendar
        </span>
        <span className="text-sm text-slate-500">See what you logged each day →</span>
      </Link>
      <ul className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {LIFE_AREAS.map((area) => (
          <li key={area}>
            <Link
              href={`/${area}`}
              className="block rounded-lg border border-slate-200 bg-white px-4 py-3 capitalize hover:border-slate-400"
            >
              {area}
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
