/**
 * Cognition API Client — v1.06 Cognition & Execution Core
 *
 * Covers: Planning, Error Analysis, Hypothesis, Confidence
 * Backend routes: /api/v1/cognition/*
 */
import { apiFetch } from "@/shared/api/client";

// ── Types ──────────────────────────────────────────────────────────────────

export interface TaskPlan {
  id: number;
  user_id: number;
  goal: string;
  steps: TaskStep[];
  current_step: number;
  status: string;
  confidence: number | null;
  created_at: string;
  updated_at: string | null;
  completed_at: string | null;
  estimated_duration_ms: number | null;
  actual_duration_ms: number | null;
}

export interface TaskStep {
  step: number;
  description: string;
  status: string;
  depends_on?: number[];
  tool?: string;
  params?: Record<string, unknown>;
  result?: Record<string, unknown>;
  error?: string;
}

export interface TaskPlanListResponse {
  items: TaskPlan[];
  total: number;
  page: number;
  page_size: number;
}

export interface ErrorAnalysis {
  id: number;
  user_id: number;
  error_type: string;
  error_message: string | null;
  fingerprint: string | null;
  context: Record<string, unknown> | null;
  root_cause: string | null;
  resolution: string | null;
  prevention: string | null;
  severity: string;
  resolved: number;
  resolution_method: string | null;
  related_analysis_id: number | null;
  created_at: string;
  resolved_at: string | null;
}

export interface ErrorPatterns {
  total_errors: number;
  most_common: string | null;
  patterns: Array<{
    error_type: string;
    count: number;
    trend: string;
  }>;
}

export interface Hypothesis {
  id: number;
  user_id: number;
  hypothesis: string;
  evidence_for: Array<{ text: string; weight: number; timestamp: string }>;
  evidence_against: Array<{ text: string; weight: number; timestamp: string }>;
  confidence: number;
  confidence_history: Array<{ value: number; timestamp: string; trigger: string }>;
  status: string;
  source: string | null;
  related_plan_id: number | null;
  related_hypothesis_id: number | null;
  created_at: string;
  updated_at: string | null;
  resolved_at: string | null;
  resolution_reason: string | null;
}

export interface ConfidenceResult {
  task_type: string;
  confidence: number;
  recommendation: string;
  risk_level: string;
  factors: string[];
}

// ── Planning ───────────────────────────────────────────────────────────────

export const planning = {
  createPlan: (goal: string, steps?: TaskStep[]) =>
    apiFetch<TaskPlan>("/cognition/planning/plan", {
      method: "POST",
      body: { goal, steps: steps || null },
    }),

  getPlan: (planId: number) =>
    apiFetch<TaskPlan>(`/cognition/planning/plan/${planId}`),

  listPlans: (params?: { status?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.limit) qs.set("limit", String(params.limit));
    return apiFetch<TaskPlanListResponse>(`/cognition/planning/plans?${qs}`);
  },

  executeStep: (planId: number, stepIndex: number, result?: Record<string, unknown>) =>
    apiFetch<TaskPlan>(`/cognition/planning/plan/${planId}/step/${stepIndex}`, {
      method: "POST",
      body: result ? { result } : undefined,
    }),

  skipStep: (planId: number, stepIndex: number, reason?: string) =>
    apiFetch<TaskPlan>(
      `/cognition/planning/plan/${planId}/step/${stepIndex}/skip${reason ? `?reason=${encodeURIComponent(reason)}` : ""}`,
      { method: "POST" },
    ),

  cancelPlan: (planId: number) =>
    apiFetch<TaskPlan>(`/cognition/planning/plan/${planId}/cancel`, {
      method: "POST",
    }),

  getNextSteps: (planId: number) =>
    apiFetch<{ plan_id: number; ready_steps: number[] }>(
      `/cognition/planning/plan/${planId}/next-steps`,
    ),
};

// ── Error Analysis ─────────────────────────────────────────────────────────

export const errors = {
  analyze: (errorType: string, errorMessage: string, context: Record<string, unknown>) =>
    apiFetch<ErrorAnalysis>("/cognition/errors/analyze", {
      method: "POST",
      body: { error_type: errorType, error_message: errorMessage, context },
    }),

  getPatterns: (days: number = 30) =>
    apiFetch<ErrorPatterns>(`/cognition/errors/patterns?days=${days}`),

  list: (params?: { severity?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.severity) qs.set("severity", params.severity);
    if (params?.limit) qs.set("limit", String(params.limit));
    return apiFetch<ErrorAnalysis[]>(`/cognition/errors/analyses?${qs}`);
  },

  get: (analysisId: number) =>
    apiFetch<ErrorAnalysis>(`/cognition/errors/analysis/${analysisId}`),

  resolve: (analysisId: number, method: string = "manual") =>
    apiFetch<ErrorAnalysis>(
      `/cognition/errors/analysis/${analysisId}/resolve?resolution_method=${method}`,
      { method: "POST" },
    ),
};

// ── Hypothesis ─────────────────────────────────────────────────────────────

export const hypothesis = {
  generate: (hypothesis: string, evidenceFor?: Array<{ text: string; weight: number }>, evidenceAgainst?: Array<{ text: string; weight: number }>, source?: string) =>
    apiFetch<Hypothesis>("/cognition/hypothesis/generate", {
      method: "POST",
      body: {
        hypothesis,
        evidence_for: evidenceFor || [],
        evidence_against: evidenceAgainst || [],
        source,
      },
    }),

  listActive: () =>
    apiFetch<Hypothesis[]>("/cognition/hypothesis/active"),

  listHighConfidence: (threshold: number = 0.7) =>
    apiFetch<Hypothesis[]>(`/cognition/hypothesis/high-confidence?threshold=${threshold}`),

  get: (hypothesisId: number) =>
    apiFetch<Hypothesis>(`/cognition/hypothesis/${hypothesisId}`),

  addEvidence: (hypothesisId: number, evidence: string, supports: boolean, weight: number = 1.0) =>
    apiFetch<Hypothesis>(
      `/cognition/hypothesis/${hypothesisId}/evidence?evidence=${encodeURIComponent(evidence)}&supports=${supports}&weight=${weight}`,
      { method: "POST" },
    ),

  resolve: (hypothesisId: number, status: "confirmed" | "rejected", reason?: string) =>
    apiFetch<Hypothesis>(
      `/cognition/hypothesis/${hypothesisId}/resolve?status=${status}${reason ? `&reason=${encodeURIComponent(reason)}` : ""}`,
      { method: "POST" },
    ),

  merge: (hypothesisId: number, otherId: number) =>
    apiFetch<Hypothesis>(
      `/cognition/hypothesis/merge?hypothesis_id=${hypothesisId}&other_id=${otherId}`,
      { method: "POST" },
    ),
};

// ── Confidence ─────────────────────────────────────────────────────────────

export const confidence = {
  estimate: (taskType: string, context?: Record<string, unknown>) =>
    apiFetch<ConfidenceResult>("/cognition/confidence/estimate", {
      method: "POST",
      body: { task_type: taskType, context: context || {} },
    }),

  combine: (scores: number[], weights?: number[]) => {
    const qs = new URLSearchParams();
    scores.forEach((s) => qs.append("confidences", String(s)));
    if (weights) weights.forEach((w) => qs.append("weights", String(w)));
    return apiFetch<{ confidence: number; method: string; input_scores: number[]; input_weights: number[]; factors: string[] }>(
      `/cognition/confidence/combine?${qs}`,
      { method: "POST" },
    );
  },

  getCalibration: (days: number = 30) =>
    apiFetch<{ total_predictions: number; calibrated_count: number; calibration_score: number; by_task_type: Record<string, { total: number; calibrated: number; score: number }> }>(
      `/cognition/confidence/calibration?days=${days}`,
    ),
};
