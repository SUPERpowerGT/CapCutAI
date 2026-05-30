/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: process.env.DESKTOP_BUILD ? "export" : undefined,
  images: process.env.DESKTOP_BUILD
    ? {
        unoptimized: true
      }
    : undefined
};

module.exports = nextConfig;
