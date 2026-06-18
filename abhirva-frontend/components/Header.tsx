"use client";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "../lib/auth-context";

export default function Header() {
  const { session, profile, isLoading, logout } = useAuth();
  const isLoggedIn = !isLoading && session !== null;

  // Role-based nav links
  const getDashboardLink = () => {
    if (!profile) return null;
    if (profile.role === "STUDENT") return { href: "/student/dashboard", label: "My Dashboard" };
    if (profile.role === "PARENT") return { href: "/parent/dashboard", label: "Parent Dashboard" };
    if (profile.role === "ADMIN") return { href: "/admin", label: "Admin Portal" };
    return null;
  };

  const dashboardLink = getDashboardLink();

  return (
    <header style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "1rem 2rem",
      backgroundColor: "rgba(10, 10, 26, 0.85)",
      borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
      backdropFilter: "blur(10px)",
      WebkitBackdropFilter: "blur(10px)",
      position: "sticky",
      top: 0,
      zIndex: 1000,
    }}>
      {/* Logo */}
      <Link href="/" style={{ display: "flex", alignItems: "center", gap: "1rem", textDecoration: "none" }}>
        <Image src="/logo.png" alt="Abhirva Learning Logo" width={40} height={40} style={{ borderRadius: "8px" }} />
        <h1 style={{ margin: 0, fontSize: "1.5rem", color: "#fff", fontWeight: "bold" }}>
          Abhirva <span className="gradient-text">Learning</span>
        </h1>
      </Link>

      {/* Navigation */}
      <nav style={{ display: "flex", gap: "1.5rem", alignItems: "center" }}>
        {isLoggedIn && dashboardLink && (
          <Link href={dashboardLink.href} style={{ color: "#ccc", textDecoration: "none", fontWeight: 500 }}>
            {dashboardLink.label}
          </Link>
        )}

        {/* Welcome message */}
        {isLoggedIn && profile && (
          <span style={{
            color: "var(--text-secondary)",
            fontSize: "0.875rem",
            padding: "0.3rem 0.75rem",
            background: "rgba(99, 102, 241, 0.1)",
            borderRadius: "20px",
            border: "1px solid rgba(99, 102, 241, 0.2)",
          }}>
            👋 {profile.full_name.split(" ")[0]}
          </span>
        )}

        {isLoggedIn ? (
          <button
            onClick={logout}
            id="logout-btn"
            style={{
              background: "transparent",
              border: "1px solid #ff4d4d",
              color: "#ff4d4d",
              padding: "0.4rem 1rem",
              borderRadius: "4px",
              cursor: "pointer",
              fontWeight: "bold",
              fontSize: "0.875rem",
              transition: "all 0.2s ease-in-out",
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = "#ff4d4d";
              e.currentTarget.style.color = "white";
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.color = "#ff4d4d";
            }}
          >
            Logout
          </button>
        ) : (
          <Link
            href="/login"
            id="login-btn"
            style={{
              background: "var(--primary-color)",
              color: "white",
              padding: "0.4rem 1rem",
              borderRadius: "4px",
              textDecoration: "none",
              fontWeight: "bold",
              fontSize: "0.875rem",
              boxShadow: "0 4px 14px 0 rgba(99, 102, 241, 0.39)",
              transition: "all 0.2s ease-in-out",
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = "translateY(-2px)";
              e.currentTarget.style.boxShadow = "0 6px 20px rgba(99, 102, 241, 0.5)";
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = "0 4px 14px 0 rgba(99, 102, 241, 0.39)";
            }}
          >
            Login
          </Link>
        )}
      </nav>
    </header>
  );
}
