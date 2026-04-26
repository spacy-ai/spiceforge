import { NextRequest, NextResponse } from 'next/server';
import { apiBase } from '@/lib/config';

export async function PATCH(req: NextRequest, context: { params: Promise<{ id: string }> }) {
  const token = req.cookies.get('token')?.value;

  if (!token) {
    return NextResponse.json({ message: 'Not authenticated' }, { status: 401 });
  }

  try {
    const payload = await req.json();
    const { id } = await context.params;
    const backendRes = await fetch(`${apiBase}/circuits/${id}`, {
      method: 'PATCH',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await backendRes.json();

    if (!backendRes.ok) {
      return NextResponse.json(
        { message: data?.detail || 'Failed to update circuit' },
        { status: backendRes.status }
      );
    }

    return NextResponse.json(data, { status: 200 });
  } catch {
    return NextResponse.json({ message: 'Something went wrong' }, { status: 500 });
  }
}
