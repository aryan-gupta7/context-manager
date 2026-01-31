/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: "#135bec",
        "primary-hover": "#2563eb", // blue-600 match from code1.html
        "background-light": "#f6f6f8",
        "background-dark": "#111318",
        "surface-dark": "#1a1d26",
        "surface-border": "#282e39",
        // Node specific colors from plan
        "node-active": "#0EA5E9",
        "node-frozen": "#8B5CF6",
        "node-deleted": "#EF4444",
        "node-ai": "#10B981",
        "node-user": "#F59E0B",
      },
      fontFamily: {
        display: ["Space Grotesk", "Noto Sans", "sans-serif"],
        body: ["Inter", "Noto Sans", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      backgroundImage: {
        'grid-pattern': "radial-gradient(#282e39 1.5px, transparent 1.5px)",
      }
    },
  },
  plugins: [],
}
