"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  BarChart3,
  Activity,
  Brain,
  Shield,
  FlaskConical,
  BookOpen,
  Radio,
  FileText,
  Moon,
  Sun,
} from "lucide-react";
import { useTheme } from "next-themes";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/dashboard/signals", label: "Signals", icon: Activity },
  { href: "/dashboard/regime", label: "Regime", icon: Brain },
  { href: "/dashboard/risk", label: "Risk", icon: Shield },
  { href: "/backtest", label: "Backtest Lab", icon: FlaskConical },
  { href: "/research", label: "Research", icon: BookOpen },
  { href: "/equity-research", label: "Equity Report", icon: FileText },
  { href: "/live", label: "Live Trading", icon: Radio },
];

export function Sidebar() {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-[240px] glass flex flex-col">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-border/30">
        <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center shadow-lg glow-primary">
          <BarChart3 className="w-4.5 h-4.5 text-white" />
          <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-primary to-purple-500 blur-lg opacity-30" />
        </div>
        <div>
          <h1 className="text-sm font-bold tracking-tight text-gradient">TSMOM</h1>
          <p className="text-[9px] text-muted-foreground uppercase tracking-[0.2em]">
            Quant Platform
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive =
            pathname === item.href || pathname?.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 relative",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
              )}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-primary glow-primary" />
              )}
              <item.icon className={cn("w-4 h-4 transition-transform duration-200", isActive ? "scale-110" : "group-hover:scale-105")} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Theme toggle */}
      <div className="px-3 py-4 border-t border-border/30">
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-muted-foreground hover:bg-accent/50 hover:text-foreground w-full transition-all duration-200"
        >
          {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          {theme === "dark" ? "Light Mode" : "Dark Mode"}
        </button>
        <div className="px-3 mt-3">
          <p className="text-[9px] text-muted-foreground/60 tracking-wider">
            v2.0.0 &middot; MOP Framework
          </p>
        </div>
      </div>
    </aside>
  );
}
