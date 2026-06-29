import { NextRequest, NextResponse } from "next/server";

/**
 * Protect all routes except auth pages, static assets, and API routes.
 * Checks for the cortex_access cookie — if missing, redirects to /auth.
 * API routes are proxied to FastAPI which handles its own auth.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip auth check for:
  // - /auth and /auth/* (login/register pages)
  // - /_next/* (Next.js internals)
  // - Static files (favicon, images, etc.)
  // - API routes (handled by FastAPI)
  if (
    pathname.startsWith("/auth") ||
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.includes(".") // static files: favicon.ico, etc.
  ) {
    return NextResponse.next();
  }

  const token = request.cookies.get("cortex_access");

  if (!token) {
    const authUrl = new URL("/auth", request.url);
    authUrl.searchParams.set("from", pathname);
    return NextResponse.redirect(authUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all paths except:
     * - _next/static (static files)
     * - _next/image (image optimization)
     * - favicon.ico
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
