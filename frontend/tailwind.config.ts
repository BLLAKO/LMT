import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        page: "#FAF9F5",
        card: "#FFFFFF",
        subtle: "#F4F2EC",
        sunken: "#EFECE3",

        primary: "#141413",
        secondary: "#6B6A60",
        muted: "#B0AEA5",
        disabled: "#D3D1C7",

        border: {
          DEFAULT: "#E8E6DC",
          strong: "#D3CFC2",
          stronger: "#B0AEA5",
        },

        accent: {
          50: "#EEF2E4",
          100: "#DBE4C4",
          300: "#AEC78A",
          500: "#7A9B52",
          600: "#5F7D3D",
          700: "#48602E",
          900: "#283419",
        },

        success: { DEFAULT: "#2F8F74", bg: "#E2F2EE", text: "#1C5445" },
        warning: { DEFAULT: "#C98A3E", bg: "#FAF0DC", text: "#6B4A1C" },
        danger: { DEFAULT: "#C2453A", bg: "#FBE9E6", text: "#6E241D" },
        info: { DEFAULT: "#4D7EA8", bg: "#E8F0F5", text: "#28425A" },
      },
    },
  },
  plugins: [],
};

export default config;
