"use client";

import Image from "next/image";
import { motion } from "framer-motion";

export default function Hero() {
  return (
    <section className="relative overflow-hidden px-6 pb-20 pt-20 text-center">
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-10 h-72 w-72 -translate-x-1/2 rounded-full bg-accent-300/40 blur-3xl"
      />
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="relative mx-auto flex max-w-2xl flex-col items-center"
      >
        <Image
          src="/logo.png"
          alt="ZeroDelay"
          width={318}
          height={90}
          priority
          className="mb-6 drop-shadow-[0_0_40px_rgba(122,155,82,0.35)]"
        />
        <p className="mt-5 max-w-lg text-lg text-secondary">
          Hands-free voice guidance for technicians, running entirely on-device.
          No cloud, no signal, no delay — just step-by-step help when you need
          it most.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <a
            href="#download"
            className="rounded-full bg-accent-500 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-accent-600"
          >
            Download for desktop
          </a>
          <a
            href="#features"
            className="rounded-full border border-border-strong px-6 py-3 text-sm font-medium text-primary transition-colors hover:bg-subtle"
          >
            See how it works
          </a>
        </div>
      </motion.div>
    </section>
  );
}
