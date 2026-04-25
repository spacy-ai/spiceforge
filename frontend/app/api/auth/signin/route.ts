import { NextRequest, NextResponse } from 'next/server'
import { apiBase } from '@/lib/config'

export async function POST(req: NextRequest) {
  try {
    const { email, password } = await req.json()

    const backendRes = await fetch(`${apiBase}/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ identifier: email, password }),
    })

    if (!backendRes.ok) {
      return NextResponse.json(
        { message: 'Invalid credentials' },
        { status: 401 }
      )
    }

    const data = await backendRes.json()

    const token = data.access_token

    const res = NextResponse.json({ success: true })

    res.cookies.set('token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
    })

    return res
  } catch (err) {
    return NextResponse.json(
      { message: 'Something went wrong' },
      { status: 500 }
    )
  }
}