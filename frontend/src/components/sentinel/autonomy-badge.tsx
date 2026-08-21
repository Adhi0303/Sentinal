import { Shield, Lock, UserCheck, Ban } from "lucide-react";
import { StatusPill } from "./primitives";
import type { AutonomyTier } from "@/lib/sentinel";
import { TIER_TOKEN, TIER_LABEL } from "@/lib/sentinel";

const TIER_ICON: Record<AutonomyTier, React.ElementType> = {
  FULL:       Shield,
  BOUNDED:    Lock,
  HITL:       UserCheck,
  QUARANTINE: Ban,
};

interface AutonomyBadgeProps {
  tier: AutonomyTier;
  className?: string;
  showIcon?: boolean;
}

/**
 * <AutonomyBadge tier="BOUNDED" />
 * Renders a colored pill indicating the agent's current autonomy tier.
 */
export function AutonomyBadge({ tier, className, showIcon = true }: AutonomyBadgeProps) {
  const Icon = TIER_ICON[tier];
  return (
    <StatusPill token={TIER_TOKEN[tier]} className={className}>
      {showIcon && <Icon className="inline-block size-3 mr-1 -mt-px" />}
      {TIER_LABEL[tier]}
    </StatusPill>
  );
}

/**
 * Trust score badge: numeric score with a color-coded progress bar.
 * 90-100: green, 70-89: amber, 40-69: orange, 0-39: red
 */
export function TrustScoreBadge({ score, className }: { score: number; className?: string }) {
  const token =
    score >= 90 ? "allow" : score >= 70 ? "hitl" : score >= 40 ? "duplicate" : "deny";

  return (
    <div className={`flex items-center gap-2 ${className ?? ""}`}>
      <div className="relative h-1.5 w-16 rounded-full bg-white/30 overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
          style={{ width: `${score}%`, backgroundColor: `var(--${token})` }}
        />
      </div>
      <span
        className="mono text-[13px] font-medium tabular-nums"
        style={{ color: `var(--${token})` }}
      >
        {score.toFixed(1)}
      </span>
    </div>
  );
}
