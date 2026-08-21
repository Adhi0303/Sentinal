import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Plus, RefreshCw, Search } from "lucide-react";
import { toast } from "sonner";

import {
  fetchRegistryAgents,
  registerNewAgent,
  updateAgentLifecycle,
  TIER_TOKEN,
  TIER_LABEL,
  type RegistryAgent,
  type AgentLifecycle,
  type RegisterAgentPayload,
} from "@/lib/sentinel";
import { StatusPill } from "@/components/sentinel/primitives";
import { AutonomyBadge, TrustScoreBadge } from "@/components/sentinel/autonomy-badge";
import { Modal, GhostBtn } from "@/components/sentinel/modal";
import { fmtTime } from "@/lib/sentinel";

export const Route = createFileRoute("/agents")({
  head: () => ({
    meta: [
      { title: "Agent Registry — Sentinel Control Plane" },
      { name: "description", content: "Register, manage, and monitor every AI agent. View live trust scores and autonomy tiers." },
    ],
  }),
  component: AgentsPage,
});

const ALLOWED_TOOLS_OPTIONS = [
  "get_payment", "get_order", "initiate_refund",
  "get_settlement", "get_payout", "modify_payout",
  "create_user", "modify_settlement",
];

const MODEL_OPTIONS = ["gpt-4o", "claude-3.5-sonnet", "gemini-1.5-pro"];

const STATUS_FILTERS: Array<{ label: string; value: string }> = [
  { label: "All", value: "" },
  { label: "Active", value: "ACTIVE" },
  { label: "Suspended", value: "SUSPENDED" },
  { label: "HITL", value: "HITL" },
  { label: "Quarantined", value: "QUARANTINED" },
  { label: "Retired", value: "RETIRED" },
];

// ── Register Form (3-step) ───────────────────────────────────────────────────
function RegisterForm({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState<Partial<RegisterAgentPayload>>({
    model: "gpt-4o",
    allowed_tools: [],
    blocked_tools: [],
    financial_limit_per_tx: 5000,
    daily_budget: 100000,
  });
  const [loading, setLoading] = useState(false);

  const set = (k: keyof RegisterAgentPayload, v: unknown) =>
    setForm((p) => ({ ...p, [k]: v }));

  const toggleTool = (tool: string) =>
    setForm((p) => {
      const cur = p.allowed_tools ?? [];
      return {
        ...p,
        allowed_tools: cur.includes(tool) ? cur.filter((t) => t !== tool) : [...cur, tool],
      };
    });

  const handleSubmit = async () => {
    if (!form.name || !form.owner || !form.purpose) return;
    setLoading(true);
    const result = await registerNewAgent(form as RegisterAgentPayload);
    setLoading(false);
    if (result) {
      toast.success(`Agent "${result.name}" registered!`, {
        description: `ID: ${result.agent_id} · Trust: ${result.trust_score} · Tier: ${result.autonomy_tier}`,
      });
      qc.invalidateQueries({ queryKey: ["registryAgents"] });
      onClose();
    } else {
      toast.error("Registration failed", { description: "Check that the backend is running." });
    }
  };

  return (
    <Modal title={`Register Agent — Step ${step} of 3`} onClose={onClose}>
      {step === 1 && (
        <div className="space-y-4">
          <div>
            <label className="block text-[12px] font-semibold text-muted-foreground mb-1">Agent Name *</label>
            <input
              value={form.name ?? ""}
              onChange={(e) => set("name", e.target.value)}
              placeholder="ZoopCart Refund Agent"
              className="w-full rounded-[12px] border border-border bg-white/50 px-3 py-2.5 text-[13px] outline-none focus:border-accent"
            />
          </div>
          <div>
            <label className="block text-[12px] font-semibold text-muted-foreground mb-1">Owner / Merchant *</label>
            <input
              value={form.owner ?? ""}
              onChange={(e) => set("owner", e.target.value)}
              placeholder="ZoopCart"
              className="w-full rounded-[12px] border border-border bg-white/50 px-3 py-2.5 text-[13px] outline-none focus:border-accent"
            />
          </div>
          <div>
            <label className="block text-[12px] font-semibold text-muted-foreground mb-1">Purpose *</label>
            <textarea
              value={form.purpose ?? ""}
              onChange={(e) => set("purpose", e.target.value)}
              rows={3}
              placeholder="Automatically process customer refund requests..."
              className="w-full rounded-[12px] border border-border bg-white/50 px-3 py-2.5 text-[13px] outline-none focus:border-accent resize-none"
            />
          </div>
          <div>
            <label className="block text-[12px] font-semibold text-muted-foreground mb-1">Model</label>
            <select
              value={form.model}
              onChange={(e) => set("model", e.target.value)}
              className="w-full rounded-[12px] border border-border bg-white/50 px-3 py-2.5 text-[13px] outline-none focus:border-accent"
            >
              {MODEL_OPTIONS.map((m) => <option key={m}>{m}</option>)}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <GhostBtn onClick={onClose}>Cancel</GhostBtn>
            <button
              disabled={!form.name || !form.owner || !form.purpose}
              onClick={() => setStep(2)}
              className="btn-pill btn-primary text-[12px] disabled:opacity-40"
            >
              Next: Capabilities →
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <div>
            <label className="block text-[12px] font-semibold text-muted-foreground mb-2">Allowed Tools</label>
            <div className="grid grid-cols-2 gap-2">
              {ALLOWED_TOOLS_OPTIONS.map((tool) => {
                const checked = (form.allowed_tools ?? []).includes(tool);
                return (
                  <label
                    key={tool}
                    className={`flex items-center gap-2 rounded-[10px] border px-3 py-2 cursor-pointer text-[12px] transition-all ${
                      checked ? "border-accent bg-accent/10 text-accent" : "border-border hover:border-accent/50"
                    }`}
                  >
                    <input type="checkbox" checked={checked} onChange={() => toggleTool(tool)} className="sr-only" />
                    <span className={`size-3.5 rounded border flex-shrink-0 flex items-center justify-center ${checked ? "bg-accent border-accent" : "border-muted-foreground"}`}>
                      {checked && <span className="text-white text-[9px] leading-none">✓</span>}
                    </span>
                    <span className="mono">{tool}</span>
                  </label>
                );
              })}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[12px] font-semibold text-muted-foreground mb-1">Tx Limit (₹)</label>
              <input
                type="number"
                value={form.financial_limit_per_tx}
                onChange={(e) => set("financial_limit_per_tx", Number(e.target.value))}
                className="w-full rounded-[12px] border border-border bg-white/50 px-3 py-2.5 text-[13px] outline-none focus:border-accent"
              />
            </div>
            <div>
              <label className="block text-[12px] font-semibold text-muted-foreground mb-1">Daily Budget (₹)</label>
              <input
                type="number"
                value={form.daily_budget}
                onChange={(e) => set("daily_budget", Number(e.target.value))}
                className="w-full rounded-[12px] border border-border bg-white/50 px-3 py-2.5 text-[13px] outline-none focus:border-accent"
              />
            </div>
          </div>
          <div className="flex justify-between gap-2 pt-2">
            <GhostBtn onClick={() => setStep(1)}>← Back</GhostBtn>
            <button onClick={() => setStep(3)} className="btn-pill btn-primary text-[12px]">
              Next: Review →
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <p className="text-[13px] text-muted-foreground">Review your agent configuration before registering.</p>
          <div className="rounded-[14px] border border-border bg-white/40 p-4 space-y-2 text-[13px]">
            <Row k="Name" v={form.name!} />
            <Row k="Owner" v={form.owner!} />
            <Row k="Purpose" v={form.purpose!} />
            <Row k="Model" v={form.model!} />
            <Row k="Allowed Tools" v={(form.allowed_tools ?? []).join(", ") || "none"} />
            <Row k="Tx Limit" v={`₹${form.financial_limit_per_tx?.toLocaleString()}`} />
            <Row k="Daily Budget" v={`₹${form.daily_budget?.toLocaleString()}`} />
          </div>
          <p className="text-[12px] text-muted-foreground">Agent will start with trust score 100 and FULL autonomy.</p>
          <div className="flex justify-between gap-2 pt-2">
            <GhostBtn onClick={() => setStep(2)}>← Back</GhostBtn>
            <button
              disabled={loading}
              onClick={handleSubmit}
              className="btn-pill btn-primary text-[12px] disabled:opacity-40"
            >
              {loading ? "Registering…" : "Register Agent"}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-muted-foreground shrink-0">{k}</dt>
      <dd className="mono text-right truncate">{v}</dd>
    </div>
  );
}

// ── Agent row card ───────────────────────────────────────────────────────────
function AgentCard({ agent }: { agent: RegistryAgent }) {
  const qc = useQueryClient();
  const isActive = agent.status === "ACTIVE";
  const isQuarantined = agent.status === "QUARANTINED";
  const isSuspended = agent.status === "SUSPENDED";

  const mutate = useMutation({
    mutationFn: (status: AgentLifecycle) => updateAgentLifecycle(agent.agent_id, status),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["registryAgents"] });
      if (data?.trust_reset_to) toast.info("Trust reset to 50 on recovery.");
    },
    onError: () => toast.error("Status update failed"),
  });

  return (
    <article className="glass rounded-[20px] p-5 hover-lift transition-all">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0">
          <Link to="/agents/$id" params={{ id: agent.agent_id }}>
            <h2 className="text-[14px] font-medium text-foreground hover:text-accent transition-colors truncate">
              {agent.name}
            </h2>
          </Link>
          <p className="text-[12px] text-muted-foreground">{agent.owner}</p>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <StatusPill token={isActive ? "allow" : isQuarantined ? "deny" : isSuspended ? "hitl" : "info"}>
            {agent.status}
          </StatusPill>
          <AutonomyBadge tier={agent.autonomy_tier} />
        </div>
      </div>

      <p className="text-[12px] text-muted-foreground line-clamp-2 mb-3">{agent.purpose}</p>

      <div className="mb-4">
        <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-1.5">Trust Score</p>
        <TrustScoreBadge score={agent.trust_score} />
      </div>

      <div className="border-t border-border/50 pt-3 flex flex-wrap gap-2">
        {isActive && (
          <button
            onClick={() => { mutate.mutate("SUSPENDED"); toast.warning(`${agent.name} suspended`); }}
            className="btn-pill btn-secondary text-[11px]"
          >
            Suspend
          </button>
        )}
        {(isQuarantined || isSuspended) && (
          <button
            onClick={() => { mutate.mutate("ACTIVE"); toast.success(`${agent.name} reactivated`); }}
            className="btn-pill btn-secondary text-[11px]"
          >
            Recover
          </button>
        )}
        {agent.status !== "RETIRED" && (
          <button
            onClick={() => { mutate.mutate("RETIRED"); toast.error(`${agent.name} retired`); }}
            className="btn-pill btn-destructive text-[11px]"
          >
            Retire
          </button>
        )}
        <Link
          to="/agents/$id"
          params={{ id: agent.agent_id }}
          className="btn-pill btn-secondary text-[11px] ml-auto"
        >
          Details →
        </Link>
      </div>
    </article>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────
function AgentsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [showRegister, setShowRegister] = useState(false);
  const qc = useQueryClient();

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["registryAgents", statusFilter],
    queryFn: () => fetchRegistryAgents(statusFilter || undefined),
    refetchInterval: 5000,
  });

  const agents = (data?.agents ?? []).filter((a) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return a.name.toLowerCase().includes(q) || a.owner.toLowerCase().includes(q) || a.agent_id.toLowerCase().includes(q);
  });

  const dist = data?.fleet_distribution;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-[22px] font-normal tracking-[-0.01em]">Agent Registry</h1>
          <p className="text-[13px] text-muted-foreground">
            {data?.count ?? "—"} registered agents
            {dist && ` · Avg trust: ${(dist.fleet_avg_trust ?? 100).toFixed(1)}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => qc.invalidateQueries({ queryKey: ["registryAgents"] })}
            className="grid size-9 place-items-center rounded-full glass hover-lift text-muted-foreground hover:text-foreground"
            title="Refresh"
          >
            <RefreshCw className={`size-4 ${isFetching ? "animate-spin" : ""}`} />
          </button>
          <button
            onClick={() => setShowRegister(true)}
            className="btn-pill btn-primary text-[12px]"
          >
            <Plus className="size-4" /> Register Agent
          </button>
        </div>
      </header>

      {/* Fleet distribution strip */}
      {dist && (
        <div className="grid grid-cols-4 gap-3">
          {(["FULL", "BOUNDED", "HITL", "QUARANTINE"] as const).map((tier) => (
            <div key={tier} className="glass-chip rounded-[16px] p-4">
              <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-1">
                {tier === "HITL" ? "NEEDS APPROVAL" : tier}
              </p>
              <p
                className="text-[28px] font-light leading-none"
                style={{ color: `var(--${TIER_TOKEN[tier]})` }}
              >
                {dist[tier]}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, owner, ID…"
            className="pl-9 pr-4 py-2 rounded-full border border-border bg-white/50 text-[13px] outline-none focus:border-accent w-64"
          />
        </div>
        <div className="flex gap-1">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setStatusFilter(f.value)}
              className={`rounded-full border px-3 py-1.5 text-[12px] transition-all ${
                statusFilter === f.value
                  ? "bg-white/80 border-transparent text-primary shadow-sm"
                  : "border-border/50 text-muted-foreground hover:bg-white/40"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Agent cards grid */}
      {isLoading ? (
        <div className="py-20 text-center text-[14px] text-muted-foreground">Loading registry…</div>
      ) : agents.length === 0 ? (
        <div className="py-20 text-center">
          <p className="text-[14px] text-muted-foreground mb-3">No agents found.</p>
          <button onClick={() => setShowRegister(true)} className="btn-pill btn-primary text-[12px]">
            <Plus className="size-4" /> Register your first agent
          </button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {agents.map((a) => <AgentCard key={a.agent_id} agent={a} />)}
        </div>
      )}

      {showRegister && <RegisterForm onClose={() => setShowRegister(false)} />}
    </div>
  );
}
