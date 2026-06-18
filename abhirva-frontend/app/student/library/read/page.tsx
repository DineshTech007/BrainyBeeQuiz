"use client";

import dynamic from "next/dynamic";

// Dynamically import the ReadBookClient component and disable SSR.
// This prevents "DOMMatrix is not defined" errors during Vercel's build step
// caused by react-pageflip and react-pdf accessing browser-only APIs.
const ReadBookClient = dynamic(() => import("./ReadBookClient"), {
  ssr: false,
  loading: () => <div style={{ padding: "2rem", color: "white", textAlign: "center" }}>Loading Library Viewer...</div>
});

export default function LibraryReadPage() {
  return <ReadBookClient />;
}
