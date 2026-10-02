import { Hero } from "@/components/landing/Hero";
import { About, ClosingBand, FeaturedProjects, Footer, Sustainability, WhatWeBuild } from "@/components/landing/Sections";

/** The public landing page (Section 8.2): a calm builder's website that invites the admin to sign in. */
export default function Landing() {
  return (
    <div className="scroll-smooth bg-bg">
      <Hero />
      <main>
        <About />
        <WhatWeBuild />
        <Sustainability />
        <FeaturedProjects />
        <ClosingBand />
      </main>
      <Footer />
    </div>
  );
}
