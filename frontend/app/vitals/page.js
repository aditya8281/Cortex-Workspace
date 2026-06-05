"use client";

import { useEffect, useRef, useState } from "react";
import { Badge, Button, Card, Loader } from "../../src/shared/ui";

function formatPercent(value) {
  return `${Math.round(value || 0)}%`;
}

function formatGb(value) {
  return `${Number(value || 0).toFixed(1)} GB`;
}

function formatClock(value) {
  if (!value) return "live";
  try {
    return new Intl.DateTimeFormat("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(new Date(value));
  } catch {
    return "live";
  }
}

function toneForLevel(level) {
  switch ((level || "").toUpperCase()) {
    case "ERROR":
    case "CRITICAL":
      return "error";
    case "WARNING":
      return "warning";
    case "DEBUG":
      return "neutral";
    case "INFO":
    default:
      return "cyan";
  }
}

function MiniSparkline({ values = [], tone = "cyan" }) {
  const width = 220;
  const height = 54;
  const max = Math.max(100, ...values, 1);
  const points = values.length
    ? values
        .map((value, index) => {
          const x = values.length === 1 ? width / 2 : (index / (values.length - 1)) * width;
          const y = height - (value / max) * (height - 8) - 4;
          return `${x.toFixed(1)},${y.toFixed(1)}`;
        })
        .join(" ")
    : `0,${height - 6} ${width},${height - 6}`;

  const stroke = tone === "green" ? "#39FF88" : tone === "warning" ? "#FBBF24" : "#00F5FF";

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-[54px] w-full">
      <polyline fill="none" stroke={stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" points={points} />
    </svg>
  );
}

function Metric({ title, value, detail, values, tone }) {
  return (
    <div className="grid gap-cortex-8 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
      <div className="flex items-start justify-between gap-cortex-12">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-cortex-text-muted">{title}</p>
          <div className="mt-cortex-8 text-2xl font-medium text-cortex-text">{value}</div>
        </div>
        <Badge variant={tone}>{tone === "green" ? "stable" : "live"}</Badge>
      </div>
      <MiniSparkline values={values} tone={tone} />
      {detail ? <p className="font-mono text-[11px] leading-5 text-cortex-text-muted">{detail}</p> : null}
    </div>
  );
}

function LogRow({ entry }) {
  const tone = toneForLevel(entry.level);
  const badgeVariant = tone === "error" ? "error" : tone === "warning" ? "warning" : tone === "green" ? "green" : "cyan";

  return (
    <div className="grid gap-cortex-8 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
      <div className="flex flex-wrap items-center gap-cortex-8">
        <Badge variant={badgeVariant}>{entry.level || "INFO"}</Badge>
        <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
          {formatClock(entry.timestamp)}
        </span>
        <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
          {entry.logger || "root"}
        </span>
        <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
          {entry.module || "system"}
        </span>
      </div>
      <div className="font-mono text-sm leading-6 text-cortex-text">{entry.message || "No message"}</div>
      {entry.pathname ? (
        <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
          {entry.pathname}:{entry.lineno}
        </div>
      ) : null}
    </div>
  );
}

export default function VitalsPage() {
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [history, setHistory] = useState({ cpu: [], ram: [], health: [] });
  const [updatedAt, setUpdatedAt] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const streamRef = useRef(null);

  async function loadVitals() {
    try {
      const [statusResponse, logsResponse] = await Promise.all([
        fetch("/api/system/status", { cache: "no-store" }),
        fetch("/api/system/logs?limit=80", { cache: "no-store" }),
      ]);

      const statusData = await statusResponse.json();
      const logsData = await logsResponse.json();

      if (!statusResponse.ok) {
        throw new Error(statusData?.error || statusData?.detail || "System status request failed");
      }

      if (!logsResponse.ok) {
        throw new Error(logsData?.error || logsData?.detail || "System logs request failed");
      }

      setStatus(statusData);
      setLogs(Array.isArray(logsData?.entries) ? logsData.entries : []);
      setHistory((current) => ({
        cpu: [...current.cpu.slice(-11), statusData.cpu?.usage_percent || 0],
        ram: [...current.ram.slice(-11), statusData.ram?.usage_percent || 0],
        health: [...current.health.slice(-11), statusData.health?.value || 0],
      }));
      setUpdatedAt(statusData.timestamp);
      setError("");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Vitals request failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadVitals();
    const timer = window.setInterval(loadVitals, 4000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (streamRef.current) {
      streamRef.current.scrollTop = streamRef.current.scrollHeight;
    }
  }, [logs]);

  const cpuUsage = status?.cpu?.usage_percent || 0;
  const ramUsage = status?.ram?.usage_percent || 0;
  const healthState = status?.health?.state || "healthy";
  const healthValue = status?.health?.value || 0;
  const processes = status?.processes || [];

  return (
    <section className="grid gap-cortex-16">
      <div className="flex items-start justify-between gap-cortex-16">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-cyan">Vitals</p>
          <h1 className="mt-cortex-8 text-2xl font-medium text-cortex-text">System Logs Console</h1>
          <p className="mt-cortex-8 max-w-2xl text-sm leading-6 text-cortex-text-muted">
            Linux-style monitor for live logs, system load, and runtime pressure. Data first, decoration last.
          </p>
        </div>
        <div className="flex items-center gap-cortex-12">
          <Badge variant={healthState === "critical" ? "error" : healthState === "warning" ? "warning" : "green"}>
            {healthState}
          </Badge>
          <Badge variant="neutral">{updatedAt ? formatClock(updatedAt) : "live"}</Badge>
          <Button variant="secondary" size="sm" onClick={loadVitals} disabled={loading}>
            {loading ? (
              <span className="inline-flex items-center gap-cortex-8">
                <Loader className="h-3.5 w-3.5" />
                Syncing
              </span>
            ) : (
              "Refresh"
            )}
          </Button>
        </div>
      </div>

      {error ? (
        <Card className="border-cortex-error/45 bg-cortex-error/10 text-cortex-error">
          <div className="font-mono text-sm">Error: {error}</div>
        </Card>
      ) : null}

      <div className="grid gap-cortex-16 xl:grid-cols-[minmax(0,1.4fr)_360px]">
        <Card className="flex min-h-[760px] flex-col gap-cortex-16">
          <div className="flex items-center justify-between gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Streaming logs</p>
              <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Tail -f console</h2>
            </div>
            <Badge variant="cyan">{logs.length} entries</Badge>
          </div>

          <div
            ref={streamRef}
            className="flex min-h-0 flex-1 flex-col gap-cortex-8 overflow-auto rounded-cortex border border-cortex-border bg-cortex-bg-secondary/60 p-cortex-12"
          >
            {logs.length > 0 ? (
              logs.map((entry, index) => (
                <LogRow key={`${entry.timestamp}-${entry.logger}-${index}`} entry={entry} />
              ))
            ) : (
              <div className="flex h-full min-h-[320px] items-center justify-center font-mono text-sm text-cortex-text-muted">
                {loading ? "Collecting system logs..." : "No logs captured yet."}
              </div>
            )}
          </div>
        </Card>

        <div className="grid gap-cortex-16">
          <Card className="grid gap-cortex-12">
            <div className="flex items-center justify-between gap-cortex-12">
              <div>
                <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">System metrics</p>
                <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Load panel</h2>
              </div>
              <Badge variant={healthState === "critical" ? "error" : healthState === "warning" ? "warning" : "green"}>
                {formatPercent(healthValue)}
              </Badge>
            </div>

            <Metric
              title="CPU"
              value={formatPercent(cpuUsage)}
              detail={`Cores ${status?.cpu?.cores || 1} · load ${status?.cpu?.load_average?.join(" / ") || "0.00 / 0.00 / 0.00"}`}
              values={history.cpu}
              tone="cyan"
            />
            <Metric
              title="RAM"
              value={formatPercent(ramUsage)}
              detail={`${formatGb(status?.ram?.used_gb)} used of ${formatGb(status?.ram?.total_gb)}`}
              values={history.ram}
              tone="green"
            />
          </Card>

          <Card className="grid gap-cortex-12">
            <div className="flex items-center justify-between gap-cortex-12">
              <div>
                <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Active processes</p>
                <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Top consumers</h2>
              </div>
              <Badge variant="neutral">{processes.length} tracked</Badge>
            </div>

            <div className="grid gap-cortex-8">
              {processes.length > 0 ? (
                processes.slice(0, 6).map((process) => (
                  <div
                    key={`${process.pid}-${process.name}`}
                    className="grid gap-cortex-8 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12"
                  >
                    <div className="flex items-start justify-between gap-cortex-12">
                      <div className="min-w-0">
                        <div className="truncate font-mono text-sm text-cortex-text">{process.name}</div>
                        <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
                          pid {process.pid} · ppid {process.ppid}
                        </div>
                      </div>
                      <Badge variant="cyan">{process.cpu_percent.toFixed(1)}%</Badge>
                    </div>
                    <div className="h-1 overflow-hidden rounded-cortex bg-cortex-bg">
                      <div
                        className="h-full rounded-cortex bg-cortex-cyan"
                        style={{ width: `${Math.min(process.cpu_percent, 100)}%` }}
                      />
                    </div>
                    <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
                      mem {process.memory_percent.toFixed(1)}%
                    </div>
                  </div>
                ))
              ) : (
                <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12 font-mono text-sm text-cortex-text-muted">
                  No process telemetry available.
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
