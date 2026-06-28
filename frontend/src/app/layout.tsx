import type { Metadata } from "next";
import { Geist, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/shared/auth/AuthProvider";
import { ToastProvider } from "@/shared/ui/Toast";

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
});

export const metadata: Metadata = {
  title: "CORTEX",
  description: "Local-first machine intelligence layer",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${geist.variable} ${jetbrains.variable}`}>
      <body className="font-sans antialiased bg-void text-text-primary">
        <AuthProvider>
          <ToastProvider>
            {children}
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
