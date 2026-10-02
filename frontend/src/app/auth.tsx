import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, type ReactNode } from "react";
import { Navigate, useLocation, useNavigate } from "react-router";
import { api, SIGNED_OUT_EVENT } from "@/lib/api";
import type { Role, User } from "@/lib/types";
import { Skeleton } from "@/components/data/States";

/** Who is signed in. The answer comes from the server, because the browser cannot read the login cookie. */
export function useMe() {
  return useQuery({ queryKey: ["me"], queryFn: () => api<User>("/auth/me"), retry: false, staleTime: 5 * 60 * 1000 });
}

export function useAuthActions() {
  const client = useQueryClient();
  const navigate = useNavigate();
  return {
    async login(email: string, password: string, remember: boolean) {
      const user = await api<User>("/auth/login", { method: "POST", body: { email, password, remember } });
      client.setQueryData(["me"], user);
      return user;
    },
    async logout() {
      try { await api("/auth/logout", { method: "POST" }); } finally {
        client.clear(); // forget every cached reply, so nothing is left for the next person
        navigate("/", { replace: true });
      }
    },
  };
}

/**
 * Wraps the console and both portals. Without a valid session it sends the visitor to /login.
 * A signed-in person who opens another role's area is sent to their own home page.
 * (This is only for a tidy screen: the server refuses the data anyway.)
 */
export function AuthGuard({ role, children }: { role: Role; children: ReactNode }) {
  const { data, isPending, isError } = useMe();
  const client = useQueryClient();
  const location = useLocation();

  useEffect(() => {  // any request that comes back "401 not signed in" lands here
    const signedOut = () => client.resetQueries({ queryKey: ["me"] });
    window.addEventListener(SIGNED_OUT_EVENT, signedOut);
    return () => window.removeEventListener(SIGNED_OUT_EVENT, signedOut);
  }, [client]);

  if (isPending) return <div className="p-10"><Skeleton className="h-8 w-64" /></div>;
  if (isError || !data) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  if (data.role !== role) return <Navigate to={data.home} replace />;
  return <>{children}</>;
}
