/**
 * Vault page — Windows Explorer-style encrypted file manager.
 * Composed from extracted sub-components and useVaultState hook.
 */
"use client";

import { motion } from "framer-motion";
import useVaultState from "./useVaultState";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import VaultLockScreen from "./VaultLockScreen";
import VaultLayout from "./VaultLayout";
import VaultModals from "./VaultModals";

export default function VaultPage() {
  const vault = useVaultState();

  // Loading state
  if (vault.authLoading || !vault.user || !vault.status) {
    return (
      <DashboardShell>
        <div className="flex h-[75vh] w-full items-center justify-center">
          <motion.div
            className="flex flex-col items-center gap-3"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
          >
            <div className="relative">
              <div className="absolute inset-0 rounded-full bg-accent/10 blur-xl animate-pulse" />
              <div className="relative h-10 w-10 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            </div>
            <p className="text-sm text-text-muted font-medium font-mono">Loading Secure Vault...</p>
          </motion.div>
        </div>
      </DashboardShell>
    );
  }

  // Lock screen
  if (vault.status.locked) {
    return (
      <DashboardShell>
        <VaultLockScreen vault={vault} />
      </DashboardShell>
    );
  }

  // Unlocked workspace
  return (
    <DashboardShell>
      <motion.div
        className="flex w-full flex-col gap-3"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        onClick={vault.handlePanelClick}
      >
        <VaultLayout vault={vault} />
        <VaultModals vault={vault} />
      </motion.div>
    </DashboardShell>
  );
}
