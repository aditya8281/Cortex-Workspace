import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/auth", "/auth/register", "/api", "/_next", "/favicon.ico"];
const PROTECTED_PATHS = [
  "/", "/chat", "/agents", "/models", "/system",
  "/settings", "/vault", "/privacy", "/memory", "/search",
  "/cognition", "/execution", "/awareness",
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("cortex_access")?.value;

  // Always allow public paths
  if (PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"))) {
    // If already logged in and trying to access /auth, redirect to dashboard
    if (token && (pathname === "/auth" || pathname === "/auth/register")) {
      return NextResponse.redirect(new URL("/", request.url));
    }
    return NextResponse.next();
  }

  // Check protected paths
  if (PROTECTED_PATHS.some((p) => pathname === p || pathname.startsWith(p))) {
    if (!token) {
      const loginUrl = new URL("/auth", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }
    return NextResponse.next();
  }

  // Unknown paths — allow (404 will be handled by Next.js)
  return NextResponse.next();
}

export const config = {
  matcher: [
    // Match all paths except static files and Next.js internals
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
