import { Building2, HardHat, LayoutDashboard, TrendingUp, TriangleAlert, UserCog, Users, Wallet, type LucideIcon } from "lucide-react";

export interface NavItem { path: string; label: string; icon: LucideIcon; question: string; phase: number }

/** The sidebar, in order. `question` is what each page answers; `phase` is when the page gets built. */
export const NAV: NavItem[] = [
  { path: "overview", label: "Overview", icon: LayoutDashboard, question: "How is Radhe doing, and what needs my attention?", phase: 7 },
  { path: "projects", label: "Projects & Inventory", icon: Building2, question: "What are we building, what is sold, and what is not moving?", phase: 7 },
  { path: "sales", label: "Sales & Leads", icon: TrendingUp, question: "Is our sales engine healthy, and where are deals stuck?", phase: 8 },
  { path: "customers", label: "Customers", icon: Users, question: "Who are our buyers, and who is unhappy or at risk?", phase: 8 },
  { path: "collections", label: "Collections", icon: Wallet, question: "How much money is due, what came in, and what is stuck?", phase: 8 },
  { path: "construction", label: "Construction", icon: HardHat, question: "Are we building on time, and what does a delay cost us?", phase: 9 },
  { path: "employees", label: "Employees & Teams", icon: UserCog, question: "Which teams and people are doing well, and who needs support?", phase: 9 },
  { path: "risks", label: "Risks & Alerts", icon: TriangleAlert, question: "What needs attention first?", phase: 10 },
];
