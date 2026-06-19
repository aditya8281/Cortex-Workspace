import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "../src/shared/auth/AuthProvider";
import ErrorBoundary from "../src/shared/ui/ErrorBoundary";
import { ToastProvider } from "../src/shared/ui/Toast";
import type { Metadata } from "next";
import type { ReactNode } from "react";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetBrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});

export const metadata: Metadata = {
  title: "Cortex",
  description: "Your machine's intelligence layer",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} ${jetBrainsMono.variable} min-h-screen bg-bg text-text font-sans antialiased`}
      >
        <AuthProvider>
          <ToastProvider />
          <ErrorBoundary>{children}</ErrorBoundary>
        </AuthProvider>
      </body>
    </html>
  );
}
