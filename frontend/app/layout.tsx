import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ZeroDelay — Offline voice guidance for technicians",
  description:
    "Hands-free, voice-guided repair and maintenance procedures that run entirely offline on a local Gemma model.",
  icons: {
    icon: "/logo.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-page text-primary antialiased">{children}</body>
    </html>
  );
}
