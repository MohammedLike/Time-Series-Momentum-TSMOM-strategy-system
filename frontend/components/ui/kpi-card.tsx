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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className={cn("relative overflow-hidden", className)}>
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                {title}
              </p>
              <p
                className={cn(
                  "text-2xl font-bold tracking-tight font-mono",
                  trend === "up" && "text-emerald-400",
                  trend === "down" && "text-red-400"
                )}
              >
                {value}
              </p>
              {subtitle && (
                <p className="text-xs text-muted-foreground">{subtitle}</p>
              )}
            </div>
            {Icon && (
              <div
                className={cn(
                  "p-2 rounded-md",
                  trend === "up" && "bg-emerald-500/10",
                  trend === "down" && "bg-red-500/10",
                  trend === "neutral" && "bg-muted"
                )}
              >
                <Icon
                  className={cn(
                    "w-4 h-4",
                    trend === "up" && "text-emerald-400",
                    trend === "down" && "text-red-400",
                    trend === "neutral" && "text-muted-foreground"
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
