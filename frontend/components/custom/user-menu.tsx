'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { LogOut } from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

type UserResponse = {
  id: number;
  public_id: string;
  full_name: string;
  email: string;
  created_at: string;
};

export function UserMenu() {
  const router = useRouter();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoadingUser, setIsLoadingUser] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const loadUser = async () => {
      try {
        const res = await fetch('/api/auth/me');

        if (!res.ok) {
          if (isMounted) {
            setUser(null);
          }
          return;
        }

        const data = (await res.json()) as UserResponse;
        if (isMounted) {
          setUser(data);
        }
      } catch {
        if (isMounted) {
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoadingUser(false);
        }
      }
    };

    loadUser();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    setUser(null);
    router.push('/auth/signin');
  };

  const getUserInitial = (name?: string) => {
    const trimmed = name?.trim();
    if (!trimmed) {
      return '?';
    }
    return trimmed[0].toUpperCase();
  };

  if (isLoadingUser) {
    return null;
  }

  if (!user) {
    return (
      <Link
        href="/auth/signin"
        className="rounded-full border border-orange-600 px-4 py-2 text-sm text-orange-600 transition-colors hover:bg-orange-600 hover:text-white"
      >
        Sign In
      </Link>
    );
  }

  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className="ring-offset-background focus-visible:ring-ring rounded-full transition-shadow outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
        >
          <Avatar className="border-border bg-background h-9 w-9 border">
            <AvatarFallback className="text-sm font-semibold">
              {getUserInitial(user.full_name)}
            </AvatarFallback>
          </Avatar>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuLabel className="space-y-1">
          <div className="text-foreground text-xs font-semibold break-words whitespace-normal">
            {user.full_name}
          </div>
          <div className="text-muted-foreground text-[11px] break-words whitespace-normal">
            {user.email}
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        <DropdownMenuItem onSelect={handleLogout}>
          <LogOut className="h-4 w-4" />
          Logout
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
