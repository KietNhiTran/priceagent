import { makeStyles, tokens } from "@fluentui/react-components";
import { motion } from "framer-motion";
import type { AgentStep } from "../types";
import { AGENT_PIPELINE } from "../types";
import { STATUS_COLORS } from "../styles/theme";

const useStyles = makeStyles({
  bar: {
    display: "flex",
    alignItems: "center",
    gap: "4px",
    padding: "10px 20px",
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    overflowX: "auto",
  },
  step: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "4px 10px",
    borderRadius: "16px",
    fontSize: "12px",
    fontWeight: 500,
    whiteSpace: "nowrap",
  },
  dot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
  },
  connector: {
    width: "16px",
    height: "2px",
    backgroundColor: tokens.colorNeutralStroke2,
  },
});

interface AgentOrchestrationBarProps {
  steps: AgentStep[];
}

export function AgentOrchestrationBar({ steps }: AgentOrchestrationBarProps) {
  const s = useStyles();

  function getStatus(agentName: string): AgentStep | undefined {
    return steps.find((st) => st.agent_name === agentName);
  }

  return (
    <div className={s.bar}>
      {AGENT_PIPELINE.map((agent, i) => {
        const step = getStatus(agent.name);
        const status = step?.status ?? "pending";
        const color = STATUS_COLORS[status];

        return (
          <div key={agent.name} style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <motion.div
              className={s.step}
              style={{
                backgroundColor:
                  status === "running" ? `${color}18` : "transparent",
                border: `1.5px solid ${color}`,
                color,
              }}
              animate={
                status === "running"
                  ? { scale: [1, 1.05, 1], opacity: [1, 0.8, 1] }
                  : {}
              }
              transition={
                status === "running"
                  ? { repeat: Infinity, duration: 1.2 }
                  : {}
              }
            >
              <div className={s.dot} style={{ backgroundColor: color }} />
              {agent.label}
              {step?.duration_ms != null && (
                <span style={{ fontSize: 10, opacity: 0.7 }}>
                  {step.duration_ms}ms
                </span>
              )}
            </motion.div>
            {i < AGENT_PIPELINE.length - 1 && <div className={s.connector} />}
          </div>
        );
      })}
    </div>
  );
}
