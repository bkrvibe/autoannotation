'use client';

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { api, MeResponse, setCsrfToken, clearCsrfToken } from '@/lib/api';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface Tenant {
  id: string;
  name: string;
  slug: string;
}

interface TenantMembership {
  tenant_id: string;
  tenant_name: string;
  tenant_slug: string;
  role_in_tenant: string;
  is_default: boolean;
}

interface AuthContextType {
  user: User | null;
  tenant: Tenant | null;
  tenants: TenantMembership[];
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  switchTenant: (tenantId: string) => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [tenants, setTenants] = useState<TenantMembership[]>([]);
  const [loading, setLoading] = useState(true);

  const refreshSession = useCallback(async () => {
    try {
      const response = await api.auth.me();
      setUser(response.user);
      setTenant(response.tenant);
      setTenants(response.tenants || []);
    } catch (error) {
      // Not authenticated or session expired
      setUser(null);
      setTenant(null);
      setTenants([]);
      clearCsrfToken();
    }
  }, []);

  // Check session on mount
  useEffect(() => {
    const checkSession = async () => {
      try {
        await refreshSession();
      } finally {
        setLoading(false);
      }
    };
    checkSession();
  }, [refreshSession]);

  const login = async (email: string, password: string) => {
    const response = await api.auth.login(email, password);
    setUser(response.user);
    setTenant(response.tenant);
    // Refresh to get full tenants list
    await refreshSession();
  };

  const logout = async () => {
    try {
      await api.auth.logout();
    } finally {
      setUser(null);
      setTenant(null);
      setTenants([]);
      clearCsrfToken();
    }
  };

  const switchTenant = async (tenantId: string) => {
    const response = await api.auth.switchTenant(tenantId);
    setUser(response.user);
    setTenant(response.tenant);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        tenant,
        tenants,
        loading,
        isAuthenticated: !!user,
        login,
        logout,
        switchTenant,
        refreshSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Hook for protected routes
export function useRequireAuth(redirectTo: string = '/login') {
  const { isAuthenticated, loading } = useAuth();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      const currentPath = window.location.pathname;
      window.location.href = `${redirectTo}?redirect=${encodeURIComponent(currentPath)}`;
    }
  }, [isAuthenticated, loading, redirectTo]);

  return { isAuthenticated, loading };
}
