import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip
} from "recharts";
import type { BehaviorDeviationReport } from "@/lib/sentinel";

export function BehaviorDeviationRadar({ deviation }: { deviation: BehaviorDeviationReport | null }) {
  const flags = deviation?.flags || [];
  
  // Calculate a 0-100 score for each axis based on the presence of specific flags.
  // Base noise is 10. Max is 100.
  const data = [
    {
      subject: "Amount",
      A: flags.includes("amount_extreme") ? 100 : (flags.includes("amount_spike") ? 75 : 10),
      fullMark: 100,
    },
    {
      subject: "Velocity",
      A: flags.includes("velocity_surge") ? 90 : 10,
      fullMark: 100,
    },
    {
      subject: "Complexity",
      A: flags.includes("depth_increase") ? 80 : 10,
      fullMark: 100,
    },
    {
      subject: "Tooling",
      A: flags.includes("tool_drift") ? 85 : 10,
      fullMark: 100,
    },
    {
      subject: "Targets",
      A: flags.includes("new_account_target") ? 95 : 10,
      fullMark: 100,
    },
    {
      subject: "Limits",
      A: flags.includes("near_limit_cluster") ? 85 : 10,
      fullMark: 100,
    },
  ];

  const SEVERITY_COLOR: Record<string, string> = {
    NORMAL:   "var(--allow)",
    MILD:     "var(--hitl)",
    MODERATE: "var(--duplicate)",
    SEVERE:   "var(--deny)",
  };

  const sev = deviation?.severity ?? "NORMAL";
  const color = SEVERITY_COLOR[sev] ?? "var(--accent)";

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="rgba(255,255,255,0.1)" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
          <Tooltip 
            contentStyle={{ backgroundColor: "rgba(0,0,0,0.8)", border: "1px solid var(--border)", borderRadius: "8px", fontSize: "12px" }}
            itemStyle={{ color: color }}
          />
          <Radar
            name="Deviation"
            dataKey="A"
            stroke={color}
            fill={color}
            fillOpacity={0.4}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
