import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createBrowserRouter, Navigate, RouterProvider } from "react-router";
import type { ReactNode } from "react";
import Collections from "@/pages/console/Collections";
import Construction from "@/pages/console/Construction";
import Customers from "@/pages/console/Customers";
import Employees from "@/pages/console/Employees";
import Overview from "@/pages/console/Overview";
import Risks from "@/pages/console/Risks";
import Sales from "@/pages/console/Sales";
import Placeholder from "@/pages/console/Placeholder";
import Projects from "@/pages/console/Projects";
import Styleguide from "@/pages/console/styleguide/Styleguide";
import Landing from "@/pages/public/Landing";
import Login from "@/pages/public/Login";
import { AuthGuard } from "./auth";
import { ConsoleLayout } from "./ConsoleLayout";
import { NAV } from "./nav";
import { CUSTOMER_PORTAL, EMPLOYEE_PORTAL, PortalLayout, PortalPage } from "./PortalLayout";

// Server data is cached for a minute, so moving between pages does not refetch everything.
const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 60 * 1000, retry: 1, refetchOnWindowFocus: false } },
});

// Console pages that are built. Any sidebar item not listed here shows a placeholder.
const BUILT: Record<string, ReactNode> = {
  overview: <Overview />,
  projects: <Projects />,
  sales: <Sales />,
  customers: <Customers />,
  collections: <Collections />,
  construction: <Construction />,
  employees: <Employees />,
  risks: <Risks />,
};

const router = createBrowserRouter([
  { path: "/", element: <Landing /> },
  { path: "/login", element: <Login /> },
  {
    path: "/console",
    element: <AuthGuard role="admin"><ConsoleLayout /></AuthGuard>, // every page below needs an admin session
    children: [
      { index: true, element: <Navigate to="overview" replace /> },
      ...NAV.map((item) => ({ path: item.path, element: BUILT[item.path] ?? <Placeholder item={item} /> })),
      { path: "styleguide", element: <Styleguide /> }, // hidden: not in the sidebar
    ],
  },
  // The two portals. Each person sees only their own pages; the server checks every request.
  ...[{ portal: EMPLOYEE_PORTAL, role: "employee" as const }, { portal: CUSTOMER_PORTAL, role: "customer" as const }].map(({ portal, role }) => ({
    path: portal.base,
    element: <AuthGuard role={role}><PortalLayout portal={portal} /></AuthGuard>,
    children: [
      { index: true, element: <Navigate to={portal.menu[0].path} replace /> },
      { path: ":page", element: <PortalPage portal={portal} /> },
    ],
  })),
  { path: "*", element: <Navigate to="/" replace /> },
]);

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
