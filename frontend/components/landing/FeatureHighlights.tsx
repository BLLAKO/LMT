"use client";

import { motion } from "framer-motion";

const features = [
  {
    title: "Voice-guided, step by step",
    detail:
      "Every procedure is spoken one step at a time and confirmed hands-free, so you never have to touch a screen mid-task.",
  },
  {
    title: "Works with zero connectivity",
    detail:
      "A local Gemma model runs entirely on-device. No cloud calls, no internet required, ever.",
  },
  {
    title: "Live sensor monitoring",
    detail:
      "Readings are checked against safe ranges in real time, so drift and faults get caught before they become dangerous.",
  },
  {
    title: "Safety alerts that stop you in time",
    detail:
      "Caution and critical steps get explicit spoken warnings and confirmations before anything risky happens.",
  },
];

export default function FeatureHighlights() {
  return (
    <section id="features" className="mx-auto max-w-6xl px-6 py-16">
      <h2 className="text-center text-2xl font-semibold tracking-tight">
        Everything you need, nothing you don&apos;t
      </h2>
      <div className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-2">
        {features.map((f, i) => (
          <motion.div
            key={f.title}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.35, delay: i * 0.06 }}
            className="rounded-2xl border border-border bg-subtle p-6"
          >
            <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-full bg-accent-100 text-accent-700">
              <span className="text-sm font-semibold">{i + 1}</span>
            </div>
            <h3 className="font-medium">{f.title}</h3>
            <p className="mt-2 text-sm text-secondary">{f.detail}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
