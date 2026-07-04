"use client";

import { motion } from "framer-motion";

// Flat/still when `amplitude` is ~0 (silence), scales and brightens in real
// time as `amplitude` (0-1) rises — driven by either the mic input level or
// a synthetic value while the AI's own turn is "speaking".
export default function VoiceVisual({
  amplitude,
  size = "default",
}: {
  amplitude: number;
  size?: "default" | "compact";
}) {
  const dimension = size === "compact" ? "h-36 w-36" : "h-64 w-64";
  const coreSize = size === "compact" ? "h-14 w-14" : "h-24 w-24";
  const dotSize = size === "compact" ? "h-5 w-5" : "h-9 w-9";

  const level = Math.max(0, Math.min(1, amplitude));
  const coreScale = 1 + level * 0.2;
  const ringScale = 1 + level * 0.75;
  const ringOpacity = 0.1 + level * 0.4;

  return (
    <div className={`flex ${dimension} items-center justify-center`}>
      <div className="relative flex h-full w-full items-center justify-center">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="absolute rounded-full bg-accent-500/20"
            style={{ width: "70%", height: "70%" }}
            animate={{
              scale: Math.max(1, ringScale - i * 0.12),
              opacity: Math.max(0.05, ringOpacity - i * 0.1),
            }}
            transition={{ duration: 0.12, ease: "easeOut" }}
          />
        ))}
        <motion.div
          className={`relative flex ${coreSize} items-center justify-center rounded-full bg-accent-500 shadow-lg`}
          animate={{ scale: coreScale }}
          transition={{ duration: 0.12, ease: "easeOut" }}
        >
          <div className={`${dotSize} rounded-full bg-white/90`} />
        </motion.div>
      </div>
    </div>
  );
}
