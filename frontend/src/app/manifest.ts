import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "JanSaathi — independent citizen information",
    short_name: "JanSaathi",
    description: "Government schemes, constitutional rights and public services — explained with official sources.",
    start_url: "/",
    display: "standalone",
    background_color: "#fbf8f1",
    theme_color: "#0b1f3a",
    icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml" }],
  };
}
