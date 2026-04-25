import { NextRequest, NextResponse } from 'next/server';
import { apiBase } from '@/lib/config';

export async function POST(req: NextRequest) {
  try {
    const { username, full_name, email, password } = await req.json();

    const backendRes = await fetch(`${apiBase}/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, full_name, email, password }),
    });

    const data = await backendRes.json();

    if (!backendRes.ok) {
      return NextResponse.json(
        { message: data.detail || 'Signup failed' },
        { status: backendRes.status }
      );
    }

    const token = data.access_token;

    if (!token) {
      return NextResponse.json({ message: 'Token not received from backend' }, { status: 500 });
    }

    const res = NextResponse.json({ success: true });

    res.cookies.set('token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
    });

    return res;
  } catch {
    return NextResponse.json({ message: 'Something went wrong' }, { status: 500 });
  }
}
