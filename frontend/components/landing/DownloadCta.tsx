"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";

type Os = "mac" | "pc";

const labels: Record<Os, string> = { mac: "macOS", pc: "Windows" };

export default function DownloadCta() {
  const [os, setOs] = useState<Os>("mac");

  return (
    <section id="download" className="mx-auto max-w-4xl px-6 py-20">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.4 }}
        className="rounded-3xl border border-border bg-card px-8 py-14 text-center shadow-sm"
      >
        <h2 className="text-2xl font-semibold tracking-tight">
          Get ZeroDelay on your device
        </h2>
        <p className="mx-auto mt-3 max-w-md text-secondary">
          Runs fully local. Pick your platform, then sign in with your
          company's access code to download.
        </p>

        <div className="mx-auto mt-8 inline-flex rounded-full border border-border bg-subtle p-1">
          {(Object.keys(labels) as Os[]).map((key) => (
            <button
              key={key}
              onClick={() => setOs(key)}
              className={`rounded-full px-5 py-2 text-sm font-medium transition-colors ${
                os === key ? "bg-accent-500 text-white" : "text-secondary hover:text-primary"
              }`}
            >
              {labels[key]}
            </button>
          ))}
        </div>

        <div className="mt-6 flex justify-center">
          <Link
            href={`/login?os=${os}`}
            className="rounded-full bg-primary px-8 py-3 text-sm font-medium text-white transition-colors hover:bg-accent-700"
          >
            Download for {labels[os]}
          </Link>
        </div>
        <p className="mt-4 text-xs text-muted">
          {os === "mac"
            ? "Unsigned build — right-click the installed app and choose Open the first time."
            : "Windows build isn't packaged yet — you'll be able to sign in, but the download itself is coming soon."}
        </p>
      </motion.div>
    </section>
  );
}
