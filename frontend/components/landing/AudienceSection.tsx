"use client";

import { motion } from "framer-motion";

const audiences = [
  {
    label: "Astronauts",
    detail: "Spacewalk repairs and habitat maintenance with no ground link.",
  },
  {
    label: "Miners",
    detail: "Underground equipment fixes, far below any signal.",
  },
  {
    label: "Offshore technicians",
    detail: "Platform and rig maintenance, hundreds of miles from shore.",
  },
  {
    label: "Ship engineers",
    detail: "Engine room repairs mid-voyage, with no satellite uplink.",
  },
];

export default function AudienceSection() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-16">
      <h2 className="text-center text-2xl font-semibold tracking-tight">
        Built for work that can&apos;t wait for a connection
      </h2>
      <p className="mx-auto mt-3 max-w-xl text-center text-secondary">
        Anywhere a technician has to fix something alone, offline, and get it
        right the first time.
      </p>
      <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {audiences.map((a, i) => (
          <motion.div
            key={a.label}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.35, delay: i * 0.06 }}
            whileHover={{ y: -4 }}
            className="rounded-2xl border border-border bg-card p-5 shadow-sm transition-shadow hover:shadow-md"
          >
            <h3 className="font-medium">{a.label}</h3>
            <p className="mt-2 text-sm text-secondary">{a.detail}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
