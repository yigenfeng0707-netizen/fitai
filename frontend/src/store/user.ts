import { useState, useEffect, useCallback } from 'react';

export interface User {
  id: number;
  username: string;
  name: string;
  role_id: number;
  store_id: number;
}

const STORAGE_KEY = 'user';

export function useUser() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback((userData: User) => {
    setUser(userData);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(userData));
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem('access_token');
  }, []);

  return { user, loading, login, logout };
}

export const roleNames: Record<number, string> = {
  1: '超级管理员',
  2: '店长',
  3: '前台',
  4: '教练',
  5: '财务',
};