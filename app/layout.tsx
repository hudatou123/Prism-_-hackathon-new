import type { Metadata } from "next";
import { Fragment_Mono, Schibsted_Grotesk } from "next/font/google";
import { PRODUCT_NAME } from "@/lib/brand";
import "./globals.css";

const schibsted = Schibsted_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-schibsted",
  display: "swap",
});

const fragment = Fragment_Mono({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-fragment",
  display: "swap",
});

export const metadata: Metadata = {
  title: `${PRODUCT_NAME} · Source-first fact checking`,
  description: "A calibrated, source-first view of complex claims.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${schibsted.variable} ${fragment.variable}`}>
      <body>{children}</body>
    </html>
  );
}
