"use client";

import { Provider } from "react-redux";
import { store } from "@/state/store";
import { RootProvider } from "@/components/shared/RootProvider";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import "@/styles/globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Cortex - AI Workspace</title>
      </head>
      <body>
        <Provider store={store}>
          <ErrorBoundary>
            <RootProvider>{children}</RootProvider>
          </ErrorBoundary>
        </Provider>
      </body>
    </html>
  );
}
