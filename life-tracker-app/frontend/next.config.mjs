// The browser always calls /api on this site; Next.js forwards it to the FastAPI backend (ADR 0004).
// Locally that's uvicorn on :8000; on Vercel set BACKEND_URL to the backend project's URL.
const backendUrl = (process.env.BACKEND_URL || "http://localhost:8000").replace(/\/+$/, "");

/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backendUrl}/api/:path*` }];
  },
};

export default nextConfig;
