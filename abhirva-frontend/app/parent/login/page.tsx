"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * This page is deprecated in favour of the unified /login page.
 * Redirects immediately to /login.
 */
export default function ParentLoginRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/login");
  }, [router]);

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "60vh",
      color: "var(--text-secondary)",
    }}>
      Redirecting to login...
    </div>
  );
}
