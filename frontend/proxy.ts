import { jwtVerify } from 'jose';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const AUTH_COOKIE = 'token';
const CIRCUIT_PATH_PREFIX = '/circuit';
const SIGN_IN_PATH = '/auth/signin';
const SIGN_UP_PATH = '/auth/signup';

async function isValidSessionToken(token: string) {
  const secretKey = process.env.SECRET_KEY;

  if (!secretKey) {
    return false;
  }

  try {
    await jwtVerify(token, new TextEncoder().encode(secretKey));
    return true;
  } catch {
    return false;
  }
}

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname === '/') {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  if (pathname === SIGN_IN_PATH || pathname === SIGN_UP_PATH) {
    const token = request.cookies.get(AUTH_COOKIE)?.value;

    if (token && (await isValidSessionToken(token))) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
  }

  if (pathname === CIRCUIT_PATH_PREFIX || pathname.startsWith(`${CIRCUIT_PATH_PREFIX}/`)) {
    const token = request.cookies.get(AUTH_COOKIE)?.value;

    if (!token || !(await isValidSessionToken(token))) {
      const signInUrl = new URL(SIGN_IN_PATH, request.url);
      signInUrl.searchParams.set('next', pathname);

      return NextResponse.redirect(signInUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next|api|favicon.ico).*)'],
};
