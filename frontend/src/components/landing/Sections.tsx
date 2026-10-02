import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";
import { api } from "@/lib/api";
import { BRAND } from "@/lib/brand";
import { Eyebrow, Reveal } from "./Reveal";

const wrap = "mx-auto w-full max-w-[1320px] px-6 lg:px-12";

// DEMO FIGURES: Radhe Constructions is a fictional brand. These four numbers are made up for the demo.
const NUMBERS = [["12", "projects delivered"], ["3,400", "families at home"], ["210", "acres developed"], ["18", "years of building"]];

export function About() {
  return (
    <section id="about" className={`${wrap} grid gap-14 py-24 lg:grid-cols-[1.15fr_1fr] lg:gap-24 lg:py-36`}>
      <Reveal>
        <Eyebrow>About</Eyebrow>
        <h2 className="mt-5 font-display text-4xl leading-tight text-ink lg:text-[44px]">We build slowly, so that what we build lasts.</h2>
        <p className="mt-7 max-w-xl leading-relaxed text-muted">
          Radhe began with a single apartment block in the west of Hyderabad. We still work the same way: our own engineers on site,
          our own designers for the interiors, and one team that stays with a family from the first visit to the day they get their keys.
        </p>
        <p className="mt-4 max-w-xl leading-relaxed text-muted">
          We keep trees where we find them, plan homes around light and air, and tell buyers the truth about dates.
        </p>
      </Reveal>
      <Reveal delay={0.1} className="self-end">
        <dl className="grid grid-cols-2 border-l border-t border-line">
          {NUMBERS.map(([value, label]) => (
            <div key={label} className="border-b border-r border-line p-7 lg:p-9">
              <dt className="font-display text-4xl text-ink lg:text-5xl">{value}</dt>
              <dd className="mt-2 text-sm text-muted">{label}</dd>
            </div>
          ))}
        </dl>
      </Reveal>
    </section>
  );
}

const BUILD = [
  { name: "Apartments", text: "Gated high-rise communities with three and four bedroom homes and a clubhouse.", image: "radhe-skyline", alt: "Apartment buildings with wide balconies behind street trees" },
  { name: "Villas", text: "Independent villas in quiet, gated neighbourhoods with room for a garden.", image: "radhe-vanam-villas", alt: "A low white villa with a tall pine tree in front" },
  { name: "Plots", text: "Plotted developments with roads, water and power in place, ready to build on.", image: "radhe-bhoomi", alt: "Green fields seen from above, divided by a line of trees" },
  { name: "Construction", text: "We build our own projects: foundations, slabs and finishing, with our own site teams.", image: "construction", alt: "A building site seen from above with a tower crane" },
  { name: "Interiors", text: "Design and execution packages, so a new home is ready to live in on day one.", image: "interiors", alt: "A calm living room with warm wood and soft daylight" },
];

/** An editorial list. The photo follows the line you hover or focus; no icon cards. */
export function WhatWeBuild() {
  const [active, setActive] = useState(0);
  return (
    <section id="build" className="bg-subtle">
      <div className={`${wrap} grid gap-12 py-24 lg:grid-cols-2 lg:gap-20 lg:py-32`}>
        <Reveal>
          <Eyebrow>What we build</Eyebrow>
          <ol className="mt-8">
            {BUILD.map((item, i) => (
              <li key={item.name} className="border-t border-line last:border-b">
                <button type="button" onMouseEnter={() => setActive(i)} onFocus={() => setActive(i)} onClick={() => setActive(i)}
                  className="group flex w-full items-baseline gap-6 py-6 text-left">
                  <span className="w-7 text-xs font-medium text-muted">{String(i + 1).padStart(2, "0")}</span>
                  <span className="flex-1">
                    <span className={`block font-display text-3xl transition-colors duration-200 lg:text-[34px] ${active === i ? "text-primary" : "text-ink/60 group-hover:text-ink"}`}>{item.name}</span>
                    <span className={`mt-2 block max-w-md text-sm leading-relaxed text-muted transition-opacity duration-200 ${active === i ? "opacity-100" : "opacity-0 max-lg:hidden"}`}>{item.text}</span>
                  </span>
                </button>
              </li>
            ))}
          </ol>
        </Reveal>
        <Reveal delay={0.1} className="relative min-h-[380px] overflow-hidden rounded-sharp lg:min-h-0">
          {BUILD.map((item, i) => (
            <img key={item.image} src={`/images/${item.image}.webp`} alt={item.alt} loading="lazy"
              className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-500 ${active === i ? "opacity-100" : "opacity-0"}`} />
          ))}
        </Reveal>
      </div>
    </section>
  );
}

const PRINCIPLES = [
  ["Rainwater harvesting", "Recharge pits and storage sized for the monsoon, so less water runs off the site."],
  ["Solar-ready rooftops", "Roofs planned with the structure and wiring that panels need."],
  ["Native landscaping", "Trees and plants that belong to the Deccan and need little watering."],
  ["Waste segregation", "Separate collection in every block, with composting on site."],
  ["Low-VOC interiors", "Paints, adhesives and boards chosen for cleaner indoor air."],
  ["Natural ventilation", "Homes laid out for cross-breeze and daylight in every room."],
];

export function Sustainability() {
  return (
    <section id="sustainability" className={`${wrap} grid gap-12 py-24 lg:grid-cols-[0.85fr_1fr] lg:gap-24 lg:py-36`}>
      <Reveal className="overflow-hidden rounded-sharp">
        <img src="/images/sustainability.webp" alt="A home seen from above, with a planted roof and a lawn between its wings" loading="lazy"
          className="h-full min-h-[340px] w-full object-cover" />
      </Reveal>
      <Reveal delay={0.1}>
        <Eyebrow>Sustainability</Eyebrow>
        <h2 className="mt-5 font-display text-4xl leading-tight text-ink lg:text-[44px]">Built to sit lightly on the land.</h2>
        <p className="mt-6 max-w-xl leading-relaxed text-muted">
          Six design principles guide every Radhe project. They are our own working rules, not certifications.
        </p>
        <dl className="mt-10 grid gap-x-10 sm:grid-cols-2">
          {PRINCIPLES.map(([name, text]) => (
            <div key={name} className="border-t border-line py-5">
              <dt className="font-medium text-ink">{name}</dt>
              <dd className="mt-1.5 text-sm leading-relaxed text-muted">{text}</dd>
            </div>
          ))}
        </dl>
      </Reveal>
    </section>
  );
}

interface Featured { name: string; locality: string; type: string; status: string; hero_image: string }
// Shown only if the backend cannot be reached, so the landing page never looks broken.
const FALLBACK: Featured[] = [
  { name: "Radhe Skyline", locality: "Narsingi", type: "Apartments", status: "Under construction", hero_image: "/images/radhe-skyline.webp" },
  { name: "Radhe Vanam Villas", locality: "Kokapet", type: "Villas", status: "Under construction", hero_image: "/images/radhe-vanam-villas.webp" },
  { name: "Radhe Bhoomi", locality: "Kollur", type: "Plots", status: "Launched", hero_image: "/images/radhe-bhoomi.webp" },
];

export function FeaturedProjects() {
  const { data } = useQuery({ queryKey: ["featured"], queryFn: () => api<Featured[]>("/public/featured-projects"), retry: false, staleTime: Infinity });
  const projects = data?.length ? data : FALLBACK;
  return (
    <section id="projects" className="bg-subtle">
      <div className={`${wrap} py-24 lg:py-32`}>
        <Reveal className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <Eyebrow>Projects</Eyebrow>
            <h2 className="mt-5 font-display text-4xl leading-tight text-ink lg:text-[44px]">Three places we are building now.</h2>
          </div>
          <p className="max-w-xs text-sm text-muted">Project details are for the leadership team. Sign in to open one.</p>
        </Reveal>
        <div className="mt-14 grid gap-8 md:grid-cols-3">
          {projects.map((project, i) => (
            <Reveal key={project.name} delay={i * 0.08}>
              <Link to="/login" className="group block">
                <div className="overflow-hidden rounded-sharp">
                  <img src={project.hero_image} alt={`${project.name}, ${project.type.toLowerCase()} in ${project.locality}`} loading="lazy"
                    className="aspect-[4/5] w-full object-cover transition-transform duration-700 group-hover:scale-[1.03]" />
                </div>
                <div className="mt-5 flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-display text-2xl text-ink">{project.name}</h3>
                    <p className="mt-1 text-sm text-muted">{project.type} in {project.locality}</p>
                  </div>
                  <ArrowUpRight size={20} strokeWidth={1.5} className="mt-1 text-muted transition-colors duration-200 group-hover:text-accent" />
                </div>
                <p className="mt-3 text-xs font-medium uppercase tracking-[0.14em] text-muted">{project.status}</p>
              </Link>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

export function ClosingBand() {
  return (
    <section className="bg-sidebar text-bg">
      <Reveal className={`${wrap} flex flex-col items-start justify-between gap-8 py-20 lg:flex-row lg:items-center lg:py-24`}>
        <div>
          <Eyebrow light>For the Radhe leadership team</Eyebrow>
          <h2 className="mt-4 max-w-2xl font-display text-3xl leading-tight lg:text-4xl">See the chain from the construction site to the bank account, in one screen.</h2>
        </div>
        <Link to="/login" className="shrink-0 rounded-sharp bg-accent px-6 py-3.5 text-sm font-medium text-white transition-colors duration-200 hover:bg-accent/90">Sign in</Link>
      </Reveal>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="bg-bg">
      <div className={`${wrap} flex flex-col gap-8 py-14 text-sm text-muted md:flex-row md:justify-between`}>
        <div>
          <p className="font-display text-xl text-ink">{BRAND.name}</p>
          <p className="mt-3">Corporate office (placeholder address)<br />Financial District, {BRAND.city}, Telangana</p>
        </div>
        <div className="md:text-right">
          <p className="font-medium text-ink">{BRAND.footerNote}</p>
          <p className="mt-2">Photographs from Unsplash, used under the Unsplash licence.</p>
        </div>
      </div>
    </footer>
  );
}
