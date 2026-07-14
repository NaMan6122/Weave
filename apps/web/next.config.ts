import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@weave/db", "@weave/shared-types"],
};

export default nextConfig;
