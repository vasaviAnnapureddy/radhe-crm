import { Eye, EyeOff, LoaderCircle } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router";
import { useAuthActions, useMe } from "@/app/auth";
import { Button } from "@/components/ui/button";
import { BRAND } from "@/lib/brand";

const fieldClass = "mt-1.5 h-11 w-full rounded-sharp border border-line bg-surface px-3 text-sm text-ink placeholder:text-neutral";

/** The sign-in form: email, password with show/hide, "keep me signed in", and a clear error line. */
export function LoginForm() {
  const { login } = useAuthActions();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const user = await login(email, password, remember);
      // Go back to the page they wanted if it is in their own area; otherwise to their home page.
      const wanted = (location.state as { from?: string } | null)?.from;
      const area = user.home.split("/")[1];
      navigate(wanted?.startsWith(`/${area}/`) ? wanted : user.home, { replace: true });
    } catch (problem) {
      setError((problem as Error).message);
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="w-full max-w-sm" noValidate>
      <h1 className="font-display text-3xl text-ink">Sign in</h1>
      <p className="mt-2 text-sm text-muted">For the Radhe team and for home owners. We take you to your own page.</p>

      <label className="mt-8 block text-sm font-medium text-ink">
        Email
        <input type="email" required autoComplete="username" autoFocus value={email} onChange={(e) => setEmail(e.target.value)} className={fieldClass} />
      </label>
      <label className="mt-5 block text-sm font-medium text-ink">
        Password
        <span className="relative block">
          <input type={show ? "text" : "password"} required autoComplete="current-password" value={password}
            onChange={(e) => setPassword(e.target.value)} className={`${fieldClass} pr-11`} />
          <button type="button" onClick={() => setShow(!show)} aria-label={show ? "Hide password" : "Show password"}
            className="absolute right-2 top-1/2 mt-[3px] -translate-y-1/2 rounded p-1.5 text-muted hover:text-ink">
            {show ? <EyeOff size={17} strokeWidth={1.75} /> : <Eye size={17} strokeWidth={1.75} />}
          </button>
        </span>
      </label>
      <label className="mt-5 flex items-center gap-2.5 text-sm text-muted">
        <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="h-4 w-4 accent-primary" />
        Keep me signed in
      </label>

      {error && <p role="alert" className="mt-5 rounded-sharp border border-risk/30 bg-risk/10 px-3 py-2.5 text-sm text-risk">{error}</p>}

      <Button type="submit" variant="primary" disabled={busy || !email || !password} className="mt-6 h-11 w-full justify-center rounded-sharp">
        {busy && <LoaderCircle size={16} className="animate-spin" />}
        {busy ? "Signing in" : "Sign in"}
      </Button>

      {import.meta.env.VITE_SHOW_DEMO_HINT === "true" && (
        <div className="mt-6 border-t border-line pt-4 text-xs leading-relaxed text-muted">
          <p className="font-semibold text-ink">Demo accounts</p>
          <p className="mt-1">The emails and passwords are in the project's .env file, never on this page:</p>
          <ul className="mt-2 space-y-1">
            <li>Admin: ADMIN_EMAIL and ADMIN_PASSWORD</li>
            <li>Home owner: PORTAL_CUSTOMER_EMAIL</li>
            <li>Relationship manager: PORTAL_RM_EMAIL</li>
            <li>Sales manager: PORTAL_SALES_EMAIL</li>
            <li>All three portal accounts use PORTAL_PASSWORD</li>
          </ul>
        </div>
      )}
    </form>
  );
}

export default function Login() {
  const { data: me } = useMe();
  if (me) return <Navigate to={me.home} replace />;
  return (
    <main className="grid min-h-screen bg-bg lg:grid-cols-2">
      {/* Left half: one calm photo and one short line. Hidden on narrow screens so the form comes first. */}
      <div className="relative hidden lg:block">
        <img src="/images/login.webp" alt="Apartment buildings seen through tall trees" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#141c17]/80 via-transparent to-[#141c17]/30" />
        <Link to="/" className="absolute left-12 top-10 font-display text-xl tracking-wide text-white">{BRAND.name}</Link>
        <p className="absolute bottom-14 left-12 right-12 max-w-md font-display text-3xl leading-snug text-white">
          Every number traces back to the site, the buyer and the bank.
        </p>
      </div>
      <div className="flex flex-col items-center justify-center px-6 py-16">
        <Link to="/" className="mb-12 font-display text-xl text-ink lg:hidden">{BRAND.name}</Link>
        <LoginForm />
        <Link to="/" className="mt-10 text-sm text-muted underline decoration-line underline-offset-4 hover:text-ink">Back to the website</Link>
      </div>
    </main>
  );
}
