import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import {
  LineChart,
  BarChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Tooltip as RTooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { useState } from "react";

import {
  fetchRegistryAgent,
  fetchTrustHistory,
  updateAgentLifecycle,
  pushTrustSignal,
  fetchBehaviorBaseline,
  fetchBehaviorDeviation,
  fetchBehaviorTimeline,
  TIER_TOKEN,
  fmtTime,
  trustToken,
  type AgentLifecycle,
  type TrustEvent,
  type BehaviorBaseline,
  type BehaviorDeviationReport,
  type BehaviorTimelineEntry,
} from "@/lib/sentinel";
import { StatusPill } from "@/components/sentinel/primitives";
import { AutonomyBadge, TrustScoreBadge } from "@/components/sentinel/autonomy-badge";
import { Modal, GhostBtn } from "@/components/sentinel/modal";
import { BehaviorDeviationRadar } from "@/components/sentinel/behavior-deviation";

export const Route = createFileRoute("/agents_/$id")({
  component: AgentDetailPage,
});


// ── Trust Timeline Chart ─────────────────────────────────────────────────────
function TrustTimeline({ events }: { events: TrustEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center rounded-[20px] border border-border/50 bg-white/20">
        <p className="text-[13px] text-muted-foreground">No trust events yet</p>
      </div>
    );
  }

  // Chart expects oldest-first
  const chartData = [...events].reverse().map((e) => ({
    time: fmtTime(e.timestamp),
    score: e.new_score,
    delta: e.delta,
    signal: e.signal_event,
  }));

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{payload: {time: string; signal: string; delta: number; score: number}}> }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div className="rounded-[12px] border border-border bg-white/90 p-3 shadow-lg text-[12px]">
        <p className="font-medium">{d.signal.replace(/_/g, " ")}</p>
        <p className="text-muted-foreground">{d.time}</p>
        <p style={{ color: d.delta >= 0 ? "var(--allow)" : "var(--deny)" }}>
          {d.delta >= 0 ? "+" : ""}{d.delta.toFixed(1)} → {d.score.toFixed(1)}
        </p>
      </div>
    );
  };

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.07)" />
          <XAxis dataKey="time" tick={{ fontSize: 10, fill: "var(--muted-foreground)" }} tickLine={false} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "var(--muted-foreground)" }} tickLine={false} />
          <Tooltip content={<CustomTooltip />} />
          {/* Tier threshold bands */}
          <ReferenceLine y={90} stroke="var(--allow)" strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: "FULL", position: "right", fontSize: 10, fill: "var(--allow)" }} />
          <ReferenceLine y={70} stroke="var(--hitl)" strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: "BOUNDED", position: "right", fontSize: 10, fill: "var(--hitl)" }} />
          <ReferenceLine y={40} stroke="var(--deny)" strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: "HITL", position: "right", fontSize: 10, fill: "var(--deny)" }} />
          <Line
            type="monotone"
            dataKey="score"
            stroke="var(--accent)"
            strokeWidth={2}
            dot={{ r: 4, fill: "var(--accent)", stroke: "white", strokeWidth: 2 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Trust event log table ────────────────────────────────────────────────────
function TrustEventLog({ events }: { events: TrustEvent[] }) {
  return (
    <div className="overflow-auto max-h-64">
      <table className="w-full text-[12px]">
        <thead>
          <tr className="border-b border-border/50">
            <th className="pb-2 text-left font-medium text-muted-foreground">Time</th>
            <th className="pb-2 text-left font-medium text-muted-foreground">Signal</th>
            <th className="pb-2 text-right font-medium text-muted-foreground">Delta</th>
            <th className="pb-2 text-right font-medium text-muted-foreground">Score</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/30">
          {events.map((e, i) => (
            <tr key={i} className="hover:bg-white/20 transition-colors">
              <td className="mono py-2 pr-4">{fmtTime(e.timestamp)}</td>
              <td className="py-2 pr-4 max-w-[180px] truncate" title={e.reason || e.signal_event}>
                {e.signal_event.replace(/_/g, " ")}
              </td>
              <td
                className="mono py-2 pr-4 text-right"
                style={{ color: e.delta >= 0 ? "var(--allow)" : "var(--deny)" }}
              >
                {e.delta >= 0 ? "+" : ""}{e.delta.toFixed(1)}
              </td>
              <td className="mono py-2 text-right">{e.new_score.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {events.length === 0 && (
        <p className="py-8 text-center text-[13px] text-muted-foreground">No trust events yet</p>
      )}
    </div>
  );
}

// ── Behavior Monitor Panel ───────────────────────────────────────────────────

const SEVERITY_COLOR: Record<string, string> = {
  NORMAL:   "var(--allow)",
  MILD:     "var(--hitl)",
  MODERATE: "var(--duplicate)",
  SEVERE:   "var(--deny)",
};

function BehaviorPanel({
  baseline,
  deviation,
  timeline,
}: {
  baseline: BehaviorBaseline | null;
  deviation: BehaviorDeviationReport | null;
  timeline: BehaviorTimelineEntry[];
}) {
  // ── Baseline not yet established ──
  if (!baseline || !baseline.baseline_locked) {
    const needed = baseline?.samples_needed ?? 10;
    const done   = 10 - needed;
    const pct    = Math.round((done / 10) * 100);
    return (
      <div className="glass rounded-[24px] p-6">
        <h2 className="text-[15px] font-medium mb-4">Behavior Monitor</h2>
        <div className="flex flex-col items-center gap-3 py-6 text-center">
          <p className="text-[13px] text-muted-foreground">
            Baseline not yet established — {needed} more actions needed.
          </p>
          <div className="w-full max-w-xs bg-border/30 rounded-full h-2 overflow-hidden">
            <div
              className="h-2 rounded-full transition-all"
              style={{ width: `${pct}%`, background: "var(--accent)" }}
            />
          </div>
          <p className="text-[11px] text-muted-foreground mono">{done}/10 actions recorded</p>
        </div>
      </div>
    );
  }

  // ── Deviation timeline chart ──
  const chartData = [...timeline].reverse().map((t) => ({
    time:  fmtTime(t.timestamp),
    score: t.deviation_score,
    color: SEVERITY_COLOR[t.severity] ?? "var(--allow)",
  }));

  const sev = deviation?.severity ?? "NORMAL";
  const sevColor = SEVERITY_COLOR[sev];

  return (
    <div className="glass rounded-[24px] p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-[15px] font-medium">Behavior Monitor</h2>
        {deviation && (
          <span
            className="rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-wider"
            style={{ background: `${sevColor}22`, color: sevColor }}
          >
            {sev} — Score {deviation.deviation_score}/100
          </span>
        )}
      </div>

      {/* Baseline stats grid */}
      <div>
        <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-3">Baseline Profile ({baseline.baseline_sample_size} samples)</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-[12px]">
          <BehStat k="Avg Amount" v={`₹${(baseline.avg_amount ?? 0).toLocaleString()}`} />
          <BehStat k="Avg Depth" v={String(baseline.avg_call_depth ?? 0)} />
          <BehStat k="Avg Velocity" v={`${baseline.avg_actions_per_minute?.toFixed(2) ?? 0} req/min`} />
          <BehStat k="Top Tools" v={(baseline.top_tools ?? []).join(", ") || "none"} />
          <BehStat k="Common Accounts" v={(baseline.common_accounts ?? []).slice(0, 3).join(", ") || "none"} />
        </div>
      </div>

      {/* Latest deviation report */}
      {deviation && deviation.flags.length > 0 && (
        <div>
          <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-3">Latest Deviation Flags</p>
          <div className="flex flex-wrap gap-2">
            {deviation.flags.map((f) => (
              <span
                key={f}
                className="rounded-full px-2.5 py-1 text-[11px] font-mono font-medium"
                style={{ background: `${sevColor}22`, color: sevColor }}
              >
                {f.replace(/_/g, " ")}
              </span>
            ))}
          </div>
          {deviation.trust_signal_emitted && (
            <p className="mt-3 text-[12px] text-muted-foreground">
              Signal emitted: <span className="font-mono" style={{ color: sevColor }}>{deviation.trust_signal_emitted.replace(/_/g, " ")}</span>
              {" · "}
              Trust Δ: <span style={{ color: "var(--deny)" }}>{deviation.trust_delta.toFixed(1)}</span>
              {" · "}
              Risk boost: <span style={{ color: "var(--deny)" }}>+{deviation.risk_boost}</span>
            </p>
          )}
        </div>
      )}

      {/* Deviation score timeline chart & Radar Chart */}
      {chartData.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-3">Deviation Score History</p>
            <div className="h-48 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.07)" />
                  <XAxis dataKey="time" tick={{ fontSize: 9, fill: "var(--muted-foreground)" }} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: "var(--muted-foreground)" }} tickLine={false} />
                  <RTooltip
                    formatter={(v: number) => [`${v}/100`, "Deviation Score"]}
                    contentStyle={{ fontSize: 11, borderRadius: 8 }}
                  />
                  <Bar dataKey="score" fill="var(--accent)" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          {deviation && (
            <div>
              <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-3">Behavior Deviation Radar</p>
              <div className="h-48 w-full">
                <BehaviorDeviationRadar deviation={deviation} />
              </div>
            </div>
          )}
        </div>
      )}

      {chartData.length === 0 && (
        <p className="text-center text-[13px] text-muted-foreground py-4">No deviation history yet — fire actions via Demo Sandbox.</p>
      )}
    </div>
  );
}

function BehStat({ k, v }: { k: string; v: string }) {
  return (
    <div className="rounded-[12px] border border-border/40 bg-white/20 px-3 py-2">
      <dt className="text-[10px] text-muted-foreground mb-0.5">{k}</dt>
      <dd className="mono text-[12px] font-medium truncate" title={v}>{v}</dd>
    </div>
  );
}

// ── Push Signal Modal (admin override) ───────────────────────────────────────
const SIGNAL_OPTIONS = [
  "ACTION_ALLOWED", "POLICY_PASSED", "HITL_APPROVED",
  "ACTION_DENIED_POLICY", "ACTION_DENIED_VELOCITY",
  "PROMPT_INJECTION_DETECTED", "CAPABILITY_VIOLATION",
  "HITL_REJECTED", "KILL_SWITCH_TRIGGERED",
];

function PushSignalModal({ agentId, onClose }: { agentId: string; onClose: () => void }) {
  const qc = useQueryClient();
  const [signal, setSignal] = useState(SIGNAL_OPTIONS[0]);
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    const res = await pushTrustSignal(agentId, signal, reason);
    setLoading(false);
    if (res) {
      toast.success(`Signal "${signal}" sent`);
      qc.invalidateQueries({ queryKey: ["agent", agentId] });
      qc.invalidateQueries({ queryKey: ["trustHistory", agentId] });
      onClose();
    } else {
      toast.error("Failed to push signal");
    }
  };

  return (
    <Modal title="Push Trust Signal" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="block text-[12px] font-semibold text-muted-foreground mb-1">Signal Event</label>
          <select
            value={signal}
            onChange={(e) => setSignal(e.target.value)}
            className="w-full rounded-[12px] border border-border bg-white/50 px-3 py-2.5 text-[13px] outline-none focus:border-accent"
          >
            {SIGNAL_OPTIONS.map((s) => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-[12px] font-semibold text-muted-foreground mb-1">Reason (optional)</label>
          <input
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Admin override — manual review..."
            className="w-full rounded-[12px] border border-border bg-white/50 px-3 py-2.5 text-[13px] outline-none focus:border-accent"
          />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <GhostBtn onClick={onClose}>Cancel</GhostBtn>
          <button onClick={submit} disabled={loading} className="btn-pill btn-primary text-[12px] disabled:opacity-40">
            {loading ? "Sending…" : "Push Signal"}
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ── Main detail page ─────────────────────────────────────────────────────────
function AgentDetailPage() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [showSignal, setShowSignal] = useState(false);

  const { data: agent, isLoading, isFetching } = useQuery({
    queryKey: ["agent", id],
    queryFn: () => fetchRegistryAgent(id),
    refetchInterval: 8_000,
  });

  const { data: history = [] } = useQuery({
    queryKey: ["trustHistory", id],
    queryFn: () => fetchTrustHistory(id, 100),
    refetchInterval: 8_000,
  });

  const { data: baseline = null } = useQuery({
    queryKey: ["behaviorBaseline", id],
    queryFn: () => fetchBehaviorBaseline(id),
    refetchInterval: 10_000,
  });

  const { data: deviation = null } = useQuery({
    queryKey: ["behaviorDeviation", id],
    queryFn: () => fetchBehaviorDeviation(id),
    refetchInterval: 10_000,
  });

  const { data: behaviorTimeline = [] } = useQuery({
    queryKey: ["behaviorTimeline", id],
    queryFn: () => fetchBehaviorTimeline(id, 100),
    refetchInterval: 10_000,
  });

  const mutate = useMutation({
    mutationFn: (status: AgentLifecycle) => updateAgentLifecycle(id, status),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["agent", id] });
      if (data?.trust_reset_to) toast.info("Trust reset to 50 on recovery.");
    },
    onError: () => toast.error("Status update failed"),
  });

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-[14px] text-muted-foreground">Loading agent…</p>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-4">
        <p className="text-[14px] text-muted-foreground">Agent not found.</p>
        <Link to="/agents" className="btn-pill btn-secondary text-[12px]">← Back to Registry</Link>
      </div>
    );
  }

  const isActive = agent.status === "ACTIVE";
  const isSuspended = agent.status === "SUSPENDED";
  const isQuarantined = agent.status === "QUARANTINED";
  const tokenColor = trustToken(agent.trust_score);

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <Link to="/agents" className="inline-flex items-center gap-1.5 text-[13px] text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="size-3.5" /> Agent Registry
      </Link>

      {/* Agent header card */}
      <div className="panel px-8 py-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-[24px] font-light tracking-[-0.02em]">{agent.name}</h1>
              <StatusPill token={isActive ? "allow" : isQuarantined ? "deny" : isSuspended ? "hitl" : "info"}>
                {agent.status}
              </StatusPill>
              <AutonomyBadge tier={agent.autonomy_tier} />
              {isFetching && <RefreshCw className="size-3.5 animate-spin text-muted-foreground" />}
            </div>
            <p className="mt-1 text-[13px] text-muted-foreground">{agent.owner} · {agent.purpose}</p>
            <p className="mono mt-1 text-[11px] text-muted-foreground">{agent.agent_id}</p>
          </div>

          {/* Big trust number */}
          <div className="text-right">
            <p className="text-[12px] uppercase tracking-wider text-muted-foreground mb-1">Trust Score</p>
            <p
              className="text-[52px] leading-none font-light tracking-[-0.04em]"
              style={{ color: `var(--${tokenColor})` }}
            >
              {agent.trust_score.toFixed(1)}
            </p>
            <p className="text-[12px] text-muted-foreground mt-1">/ 100</p>
          </div>
        </div>

        {/* Agent meta row */}
        <div className="mt-6 flex flex-wrap gap-6 border-t border-border/50 pt-5 text-[12px]">
          <Stat k="Model" v={agent.model} />
          <Stat k="Tx Limit" v={`₹${agent.financial_limit_per_tx.toLocaleString()}`} />
          <Stat k="Daily Budget" v={`₹${agent.daily_budget.toLocaleString()}`} />
          <Stat k="Registered" v={fmtTime(agent.created_at)} />
          <Stat k="Created By" v={agent.created_by} />
          <Stat k="Allowed Tools" v={agent.allowed_tools.join(", ") || "none"} />
        </div>

        {/* Control buttons */}
        <div className="mt-5 flex flex-wrap gap-2 border-t border-border/50 pt-5">
          <button
            onClick={() => setShowSignal(true)}
            className="btn-pill btn-secondary text-[12px]"
          >
            Push Trust Signal
          </button>
          {isActive && (
            <button
              onClick={() => { mutate.mutate("SUSPENDED"); toast.warning(`${agent.name} suspended`); }}
              className="btn-pill btn-secondary text-[12px]"
            >
              Suspend
            </button>
          )}
          {(isQuarantined || isSuspended) && (
            <button
              onClick={() => { mutate.mutate("ACTIVE"); toast.success(`${agent.name} reactivated`); }}
              className="btn-pill btn-secondary text-[12px]"
            >
              Recover
            </button>
          )}
          {agent.status !== "RETIRED" && (
            <button
              onClick={() => {
                mutate.mutate("RETIRED");
                toast.error(`${agent.name} retired`);
                navigate({ to: "/agents" });
              }}
              className="btn-pill btn-destructive text-[12px]"
            >
              Retire Agent
            </button>
          )}
        </div>
      </div>

      {/* Trust Timeline */}
      <div className="glass rounded-[24px] p-6">
        <h2 className="text-[15px] font-medium mb-4">Trust Timeline</h2>
        <TrustTimeline events={history} />
      </div>

      {/* Trust Event Log */}
      <div className="glass rounded-[24px] p-6">
        <h2 className="text-[15px] font-medium mb-4">Trust Event Log <span className="text-muted-foreground font-normal text-[13px]">({history.length} events)</span></h2>
        <TrustEventLog events={history} />
      </div>

      {/* Autonomy Decision */}
      {agent.autonomy_decision && (
        <div className="glass rounded-[24px] p-6">
          <h2 className="text-[15px] font-medium mb-4">Current Autonomy Decision</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <Stat2 k="Tier" v={<AutonomyBadge tier={agent.autonomy_decision.tier} />} />
            <Stat2 k="Requires HITL" v={<span style={{ color: agent.autonomy_decision.requires_hitl ? "var(--hitl)" : "var(--allow)" }}>{agent.autonomy_decision.requires_hitl ? "Yes" : "No"}</span>} />
            <Stat2 k="Blocked" v={<span style={{ color: agent.autonomy_decision.blocked ? "var(--deny)" : "var(--allow)" }}>{agent.autonomy_decision.blocked ? "Yes" : "No"}</span>} />
            <Stat2 k="Reason" v={<span className="text-muted-foreground">{agent.autonomy_decision.reason}</span>} />
          </div>
        </div>
      )}

      {/* Behavior Monitor */}
      <BehaviorPanel
        baseline={baseline}
        deviation={deviation}
        timeline={behaviorTimeline}
      />

      {showSignal && <PushSignalModal agentId={id} onClose={() => setShowSignal(false)} />}
    </div>
  );
}

function Stat({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-muted-foreground mb-0.5">{k}</dt>
      <dd className="mono font-medium">{v}</dd>
    </div>
  );
}

function Stat2({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-border/30 pb-2">
      <dt className="text-[12px] text-muted-foreground">{k}</dt>
      <dd className="text-[12px]">{v}</dd>
    </div>
  );
}
