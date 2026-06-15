import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["localhost", "127.0.0.1", "10.5.0.2", "192.168.8.121"],

  async redirects() {
    return [
      {
        source: "/physicians",
        destination: "/dentists",
        permanent: true,
      },
      {
        source: "/physicians/:slug",
        destination: "/dentists/:slug",
        permanent: true,
      },
      {
        source: "/",
        has: [
          {
            type: "host",
            value: "360.dentist",
          },
        ],
        destination: "https://www.360.dentist/dentists/drqali",
        permanent: true,
      },
      {
        source: "/",
        has: [
          {
            type: "host",
            value: "www.360.dentist",
          },
        ],
        destination: "https://www.360.dentist/dentists/drqali",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
