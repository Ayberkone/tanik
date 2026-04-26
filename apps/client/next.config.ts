import type { NextConfig } from "next";

// Standalone output keeps the Docker runtime image small (Dockerfile copies
// from .next/standalone/), but it produces a self-hosted Node.js server that
// Vercel's serverless runtime cannot route — every request 404s on Vercel
// when standalone is on. Gate it behind BUILD_STANDALONE=true so:
//   - Docker build sets BUILD_STANDALONE=true → standalone bundle for /data Docker
//   - Vercel build leaves it unset           → standard Next build for serverless
const nextConfig: NextConfig = {
  output: process.env.BUILD_STANDALONE === "true" ? "standalone" : undefined,
};

export default nextConfig;
