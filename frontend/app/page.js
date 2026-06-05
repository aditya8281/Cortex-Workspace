"use client";

import { useEffect, useMemo, useState } from "react";
import { Badge, Button, Card } from "../src/shared/ui";

function formatPercent(value) {
  return `${Math.round(value || 0)}%`;
}

function formatGb(value) {
  return `${Number(value || 0).toFixed(1)} GB`;
}

function formatTimestamp(value) {
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

function Sparkline({ values = [], tone = "cyan" }) {
  const width = 240;
  const height = 72;
  const max = Math.max(100, ...values, 1);
  const points = values.length
    ? values
        .map((value, index) => {
          const x = values.length === 1 ? width / 2 : (index / (values.length - 1)) * width;
          const y = height - (value / max) * (height - 8) - 4;
          return `${x.toFixed(1)},${y.toFixed(1)}`;
        })
        .join(" ")
    : `0,${height - 4} ${width},${height - 4}`;

  const stroke = tone === "green" ? "#39FF88" : "#00F5FF";

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-[72px] w-full">
      <polyline
        fill="none"
        stroke={stroke}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
}

function HealthRing({ value = 0, state = "healthy" }) {
  const size = 128;
  const stroke = 10;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(Math.max(value, 0), 100) / 100) * circumference;

  const tone =
    state === "critical" ? "#FF4D4D" : state === "warning" ? "#FBBF24" : "#39FF88";

  return (
    <div className="relative flex items-center justify-center">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={tone}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          className="drop-shadow-[0_0_16px_rgba(0,245,255,0.15)]"
        />
      </svg>
      <div className="absolute text-center">
        <div className="font-mono text-2xl text-cortex-text">{Math.round(value)}%</div>
        <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
          {state}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, detail, values, tone = "cyan" }) {
  return (
    <Card className="flex flex-col gap-cortex-12">
      <div className="flex items-center justify-between gap-cortex-12">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">{title}</p>
          <div className="mt-cortex-8 text-3xl font-medium text-cortex-text">{value}</div>
        </div>
        <Badge variant={tone === "green" ? "green" : tone === "warning" ? "warning" : "cyan"}>
          live
        </Badge>
      </div>
      <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
        <Sparkline values={values} tone={tone} />
      </div>
      {detail ? <p className="text-sm text-cortex-text-muted">{detail}</p> : null}
    </Card>
  );
}

export default function Page() {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");
  const [history, setHistory] = useState({ cpu: [], ram: [], health: [] });
  const [updatedAt, setUpdatedAt] = useState(null);

  async function loadStatus() {
    try {
      const response = await fetch("/api/system/status", { cache: "no-store" });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error || "System status request failed");
      }

      setStatus(data);
      setUpdatedAt(data.timestamp);
      setError("");
      setHistory((current) => ({
        cpu: [...current.cpu.slice(-11), data.cpu?.usage_percent || 0],
        ram: [...current.ram.slice(-11), data.ram?.usage_percent || 0],
        health: [...current.health.slice(-11), data.health?.value || 0],
      }));
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "System status request failed");
    }
  }

  useEffect(() => {
    loadStatus();
    const timer = window.setInterval(loadStatus, 5000);
    return () => window.clearInterval(timer);
  }, []);

  const cpuUsage = status?.cpu?.usage_percent || 0;
  const ramUsage = status?.ram?.usage_percent || 0;
  const healthValue = status?.health?.value || 0;
  const healthState = status?.health?.state || "healthy";
  const processes = useMemo(() => status?.processes || [], [status]);
  const isCritical = healthState === "critical";

  return (
    <section className="grid gap-cortex-16">
      <div className="flex items-start justify-between gap-cortex-16">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-cyan">Dashboard</p>
          <h1 className="mt-cortex-8 text-2xl font-medium text-cortex-text">Mission Control Cockpit</h1>
          <p className="mt-cortex-8 max-w-2xl text-sm leading-6 text-cortex-text-muted">
            Live system telemetry for CPU, RAM, and active processes. Minimal graphs only. Data first.
          </p>
        </div>
        <div className="flex items-center gap-cortex-12">
          <Badge variant={isCritical ? "error" : healthState === "warning" ? "warning" : "green"}>
            {healthState}
          </Badge>
          <Button variant="secondary" size="sm" onClick={loadStatus}>
            Refresh
          </Button>
        </div>
      </div>

      {error ? (
        <Card className="border-cortex-error/45 bg-cortex-error/10 text-cortex-error">
          <div className="font-mono text-sm">Error: {error}</div>
        </Card>
      ) : null}

      <div className="grid gap-cortex-16 xl:grid-cols-[minmax(0,1.3fr)_360px]">
        <div className="grid gap-cortex-16">
          <div className="grid gap-cortex-16 md:grid-cols-2">
            <MetricCard
              title="CPU"
              value={formatPercent(cpuUsage)}
              detail={`CPU utilization on ${status?.cpu?.cores || 1} cores`}
              values={history.cpu}
              tone="cyan"
            />
            <MetricCard
              title="RAM"
              value={formatPercent(ramUsage)}
              detail={`${formatGb(status?.ram?.used_gb)} used of ${formatGb(status?.ram?.total_gb)}`}
              values={history.ram}
              tone="green"
            />
          </div>

          <Card className="flex flex-col gap-cortex-16">
            <div className="flex items-center justify-between gap-cortex-12">
              <div>
                <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">
                  Active processes
                </p>
                <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">
                  Top runtime consumers
                </h2>
              </div>
              <Badge variant="neutral">{processes.length} tracked</Badge>
            </div>

            <div className="grid gap-cortex-8">
              {processes.length > 0 ? (
                processes.map((process) => (
                  <div
                    key={`${process.pid}-${process.name}`}
                    className="grid gap-cortex-8 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12 md:grid-cols-[1fr_120px_120px]"
                  >
                    <div className="min-w-0">
                      <div className="truncate font-mono text-sm text-cortex-text">{process.name}</div>
                      <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
                        pid {process.pid} · ppid {process.ppid}
                      </div>
                    </div>
                    <div className="font-mono text-sm text-cortex-text-muted md:text-right">
                      CPU {process.cpu_percent.toFixed(1)}%
                    </div>
                    <div className="font-mono text-sm text-cortex-text-muted md:text-right">
                      MEM {process.memory_percent.toFixed(1)}%
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

        <div className="grid gap-cortex-16">
          <Card className="flex flex-col items-center gap-cortex-16">
            <div className="flex w-full items-center justify-between gap-cortex-12">
              <div>
                <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">
                  System health
                </p>
                <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Indicator ring</h2>
              </div>
              <Badge variant={healthState === "critical" ? "error" : healthState === "warning" ? "warning" : "green"}>
                ring
              </Badge>
            </div>

            <HealthRing value={healthValue} state={healthState} />

            <div className="grid w-full gap-cortex-8 text-sm text-cortex-text-muted">
              <div className="flex items-center justify-between gap-cortex-12 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 px-cortex-12 py-cortex-12">
                <span>Load avg</span>
                <span className="font-mono">{(status?.cpu?.load_average || [0, 0, 0]).join(" / ")}</span>
              </div>
              <div className="flex items-center justify-between gap-cortex-12 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 px-cortex-12 py-cortex-12">
                <span>Updated</span>
                <span className="font-mono">{formatTimestamp(updatedAt)}</span>
              </div>
              <div className="flex items-center justify-between gap-cortex-12 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 px-cortex-12 py-cortex-12">
                <span>OS</span>
                <span className="font-mono">{status?.os?.system || "n/a"}</span>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between gap-cortex-12">
              <div>
                <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">
                  Health trace
                </p>
                <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Minimal line graph</h2>
              </div>
              <Badge variant="neutral">historical</Badge>
            </div>
            <div className="mt-cortex-12 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
              <Sparkline values={history.health} tone="green" />
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
