import type { Metadata } from "next";
import { Space_Grotesk, Source_Serif_4 } from "next/font/google";
import SiteHeader from "./components/site-header";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});

const sourceSerif = Source_Serif_4({
  variable: "--font-source-serif",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "360 Consult Platform",
  description: "doctor-to-doctor consultations",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${sourceSerif.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#f9f9f9]">
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}



