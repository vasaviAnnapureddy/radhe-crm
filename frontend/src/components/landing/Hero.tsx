import { Link } from "react-router";
import { BRAND } from "@/lib/brand";

const LINKS = [["About", "#about"], ["What we build", "#build"], ["Sustainability", "#sustainability"], ["Projects", "#projects"]];

/** Top navigation over the photo, then the headline. One clay button on the screen: Admin login. */
export function Hero() {
  return (
    <header className="relative flex min-h-[92vh] flex-col text-white">
      <img src="/images/hero.webp" alt="A residential building set among tall, mature trees" fetchPriority="high"
        className="absolute inset-0 h-full w-full object-cover" />
      {/* A soft dark wash so white text stays readable on any part of the photo. */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#141c17]/85 via-[#141c17]/35 to-[#141c17]/45" />

      <nav className="relative z-10 mx-auto flex w-full max-w-[1320px] items-center justify-between px-6 py-6 lg:px-12" aria-label="Main">
        <a href="#top" className="font-display text-xl tracking-wide">{BRAND.name}</a>
        <div className="flex items-center gap-8">
          <ul className="hidden items-center gap-8 text-sm text-white/85 md:flex">
            {LINKS.map(([label, href]) => (
              <li key={href}><a href={href} className="transition-colors duration-200 hover:text-white">{label}</a></li>
            ))}
          </ul>
          <Link to="/login" className="rounded-sharp bg-accent px-4 py-2.5 text-sm font-medium transition-colors duration-200 hover:bg-accent/90">
            Sign in
          </Link>
        </div>
      </nav>

      <div id="top" className="relative z-10 mx-auto mt-auto w-full max-w-[1320px] px-6 pb-16 lg:px-12 lg:pb-24">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/75">{BRAND.city}, since 2008</p>
        <h1 className="mt-5 max-w-3xl font-display text-5xl leading-[1.05] sm:text-6xl lg:text-7xl">{BRAND.tagline}</h1>
        <p className="mt-6 max-w-xl text-base leading-relaxed text-white/85 lg:text-lg">
          Apartments, villas and plotted communities in Hyderabad, built by our own teams with care for the people who live in them and the land they stand on.
        </p>
        <div className="mt-9 flex flex-wrap gap-3">
          <a href="#about" className="rounded-sharp bg-white px-5 py-3 text-sm font-medium text-ink transition-colors duration-200 hover:bg-bg">Discover Radhe</a>
          <Link to="/login" className="rounded-sharp border border-white/60 px-5 py-3 text-sm font-medium transition-colors duration-200 hover:bg-white/10">Sign in</Link>
        </div>
      </div>
    </header>
  );
}
