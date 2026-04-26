/** @type {import('next').NextConfig} */
const nextConfig = {
  allowedDevOrigins: [
    "https://kopilka-dusky.vercel.app,
  ],
  async rewrites() {
    return [
      {
        source: "/backend/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;