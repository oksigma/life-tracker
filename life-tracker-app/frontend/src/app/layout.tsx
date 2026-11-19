import type { Metadata, Viewport } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "LifeTracker",
  description: "A personal record of the different parts of your life.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  // Lets content use the full iPhone screen; safe-area insets keep buttons clear of the home bar.
  viewportFit: "cover",
  themeColor: "#f8fafc",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">{children}</body>
    </html>
  );
}
