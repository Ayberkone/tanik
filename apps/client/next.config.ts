import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output keeps the runtime image small for Docker.
  output: "standalone",
};

export default nextConfig;
