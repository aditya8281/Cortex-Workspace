"use client";

import { Brain, Construction } from "lucide-react";
import { motion } from "framer-motion";

export default function MemoryPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col items-center gap-6"
      >
        <div className="relative">
          <Brain className="h-20 w-20 text-cyan-400/50" />
          <Construction className="absolute -bottom-1 -right-1 h-6 w-6 text-amber-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Memory — Coming Soon</h1>
          <p className="mt-2 max-w-md text-sm text-neutral-400">
            AI-powered knowledge base, embeddings, and intelligent retrieval
            are under development. Check back soon.
          </p>
        </div>
      </motion.div>
    </div>
  );
}
