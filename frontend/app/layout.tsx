import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/lib/providers";
import { Sidebar } from "@/components/layout/sidebar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "TSMOM | Quantitative Strategy Platform",
  description:
    "Production-grade Time-Series Momentum strategy engine and analytics platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased noise-overlay`}>
        <Providers>
          <div className="bg-mesh" />
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 ml-[240px] p-6 lg:p-8">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
