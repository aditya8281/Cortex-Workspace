/**
 * Vault page — Windows Explorer-style encrypted file manager.
 * Composed from extracted sub-components and useVaultState hook.
 */
"use client";

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
        <div className="flex h-[75vh] w-full items-center justify-center animate-fade-in">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            <p className="text-sm text-text-muted font-medium">Loading Secure Vault...</p>
          </div>
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
      <div className="flex w-full flex-col gap-3 animate-fade-in" onClick={vault.handlePanelClick}>
        <VaultLayout vault={vault} />
        <VaultModals vault={vault} />
      </div>
    </DashboardShell>
  );
}
