"use client";

import dynamic from "next/dynamic";
import { Navbar } from "./Navbar";
import { ScrollBackdrop } from "./ScrollBackdrop";
import { Hero } from "./Hero";
import { LogoMarquee } from "./LogoMarquee";
import { Problem } from "./Problem";
import { Pipeline } from "./Pipeline";
import { LiveDemo } from "./LiveDemo";
import { UseCases } from "./UseCases";
import { Testimonials } from "./Testimonials";
import { Faq } from "./Faq";
import { FinalCta } from "./FinalCta";
import { Footer } from "./Footer";

const BackgroundFlow = dynamic(
  () => import("./three/BackgroundFlow").then((m) => m.BackgroundFlow),
  { ssr: false }
);

export function LandingShell() {
  return (
    <div className="relative min-h-screen">
      <ScrollBackdrop />
      <BackgroundFlow />
      <Navbar />
      <main className="relative z-10">
        <Hero />
        <LogoMarquee />
        <Problem />
        <Pipeline />
        <LiveDemo />
        <UseCases />
        <Testimonials />
        <Faq />
        <FinalCta />
      </main>
      <div className="relative z-10">
        <Footer />
      </div>
    </div>
  );
}
