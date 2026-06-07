import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Present Yourself",
  description: "AI-powered slide deck generation — beautiful, branded, fast.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
