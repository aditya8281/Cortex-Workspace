import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { AppShell } from "../src/shared/layout/app-shell";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetBrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});

export const metadata = {
  title: "CORTEX",
  description: "Developer-grade AI operating system interface",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en-GB">
      <body
        className={`${inter.variable} ${jetBrainsMono.variable} min-h-screen bg-cortex-bg text-cortex-text antialiased`}
      >
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
