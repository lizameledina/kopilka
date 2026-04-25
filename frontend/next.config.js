/** @type {import('next').NextConfig} */
const nextConfig = {
  allowedDevOrigins: [
    "rekindle-sulfite-greeter.ngrok-free.dev",
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