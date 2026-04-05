"use client";

import { Badge } from "@/components/ui/badge";

interface HeaderProps {
  title: string;
  description?: string;
  badge?: string;
  children?: React.ReactNode;
}

export function Header({ title, description, badge, children }: HeaderProps) {
  return (
    <div className="flex items-start justify-between mb-8">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight text-gradient">{title}</h1>
          {badge && (
            <Badge variant="secondary" className="text-[9px] uppercase tracking-[0.2em] border border-primary/20 bg-primary/5">
              {badge}
            </Badge>
          )}
        </div>
        {description && (
          <p className="text-sm text-muted-foreground mt-1.5">{description}</p>
        )}
      </div>
      {children && <div className="flex items-center gap-2">{children}</div>}
    </div>
  );
}
