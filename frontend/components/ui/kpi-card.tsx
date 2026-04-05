"use client";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { type LucideIcon } from "lucide-react";

interface KpiCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: "up" | "down" | "neutral";
  className?: string;
  delay?: number;
}

export function KpiCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  className,
  delay = 0,
}: KpiCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.5, delay, type: "spring", stiffness: 100 }}
    >
      <Card
        className={cn(
          "relative overflow-hidden border-gradient",
          trend === "up" && "glow-profit",
          trend === "down" && "glow-loss",
          className
        )}
      >
        {/* Ambient glow */}
        <div
          className={cn(
            "absolute -top-8 -right-8 w-24 h-24 rounded-full blur-2xl opacity-10",
            trend === "up" && "bg-emerald-500",
            trend === "down" && "bg-red-500",
            trend === "neutral" && "bg-primary"
          )}
        />
        <CardContent className="p-4 relative">
          <div className="flex items-start justify-between">
            <div className="space-y-1.5">
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-[0.15em]">
                {title}
              </p>
              <p
                className={cn(
                  "text-2xl font-bold tracking-tight font-mono",
                  trend === "up" && "text-emerald-400 glow-text-profit",
                  trend === "down" && "text-red-400 glow-text-loss"
                )}
              >
                {value}
              </p>
              {subtitle && (
                <p className="text-[11px] text-muted-foreground">{subtitle}</p>
              )}
            </div>
            {Icon && (
              <div
                className={cn(
                  "p-2.5 rounded-xl",
                  trend === "up" && "bg-emerald-500/10 ring-1 ring-emerald-500/20",
                  trend === "down" && "bg-red-500/10 ring-1 ring-red-500/20",
                  trend === "neutral" && "bg-primary/10 ring-1 ring-primary/20"
                )}
              >
                <Icon
                  className={cn(
                    "w-4 h-4",
                    trend === "up" && "text-emerald-400",
                    trend === "down" && "text-red-400",
                    trend === "neutral" && "text-primary"
                  )}
                />
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
