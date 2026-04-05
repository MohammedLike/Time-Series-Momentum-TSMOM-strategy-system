"use client";

import { motion } from "framer-motion";

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="relative">
        <motion.div
          className="w-10 h-10 border-2 border-primary/20 border-t-primary rounded-full"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
        <div className="absolute inset-0 w-10 h-10 rounded-full blur-md bg-primary/20" />
      </div>
    </div>
  );
}

export function LoadingCard() {
  return (
    <div className="rounded-xl border border-border/50 bg-card/60 backdrop-blur-xl p-4 overflow-hidden">
      <div className="h-3 w-20 shimmer rounded-full mb-4" />
      <div className="h-7 w-28 shimmer rounded-lg mb-2" />
      <div className="h-2.5 w-16 shimmer rounded-full" />
    </div>
  );
}

export function LoadingGrid({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3">
      {Array.from({ length: count }).map((_, i) => (
        <LoadingCard key={i} />
      ))}
    </div>
  );
}

export function LoadingChart() {
  return (
    <div className="rounded-xl border border-border/50 bg-card/60 backdrop-blur-xl p-6">
      <div className="h-3 w-32 shimmer rounded-full mb-6" />
      <div className="h-[300px] rounded-xl overflow-hidden shimmer flex items-center justify-center">
        <div className="relative">
          <motion.div
            className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          />
        </div>
      </div>
    </div>
  );
}
