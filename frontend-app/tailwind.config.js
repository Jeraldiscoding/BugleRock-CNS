module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./dashboard/**/*.{js,jsx,ts,tsx,html}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: "#565e74",
        "on-primary": "#ffffff",
        "primary-container": "#f1f5f9",
        "on-primary-container": "#0f172a",
        secondary: "#475569",
        "on-secondary": "#ffffff",
        "secondary-container": "#f8fafc",
        "on-secondary-container": "#0f172a",
        tertiary: "#c2410c",
        "on-tertiary": "#ffffff",
        "tertiary-container": "#ffedd5",
        "on-tertiary-container": "#431407",
        error: "#dc2626",
        "error-container": "#fef2f2",
        "on-error": "#ffffff",
        "on-error-container": "#450a0a",
        surface: "#fbfcfd",
        "on-surface": "#191c1d",
        "surface-variant": "#dfe4e8",
        "on-surface-variant": "#434749",
        outline: "#73777f",
        "outline-variant": "#c3c7cf",
        "surface-container-highest": "#e1e3e4",
        "surface-container-high": "#e6e8e9",
        "surface-container": "#eceeef",
        "surface-container-low": "#f2f4f5",
        "surface-container-lowest": "#ffffff"
      },
      fontFamily: {
        headline: ['Inter', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
      }
    }
  },
  plugins: [],
}
