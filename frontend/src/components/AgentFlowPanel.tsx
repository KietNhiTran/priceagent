import { useState } from "react";
import {
  makeStyles,
  tokens,
  Text,
  Badge,
  Divider,
} from "@fluentui/react-components";
import {
  ChevronDown24Regular,
  ChevronRight24Regular,
} from "@fluentui/react-icons";
import { motion, AnimatePresence } from "framer-motion";
import type { AgentStep, AgentTrace } from "../types";
import { AGENT_PIPELINE } from "../types";
import { STATUS_COLORS } from "../styles/theme";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    overflowY: "auto",
    padding: "16px",
  },
  header: {
    fontWeight: 600,
    fontSize: "16px",
    marginBottom: "12px",
  },
  timeline: {
    position: "relative",
    paddingLeft: "24px",
  },
  line: {
    position: "absolute",
    top: 0,
    bottom: 0,
    left: "11px",
    width: "2px",
    backgroundColor: tokens.colorNeutralStroke2,
  },
  stepCard: {
    position: "relative",
    marginBottom: "12px",
    padding: "10px 14px",
    borderRadius: "8px",
    backgroundColor: tokens.colorNeutralBackground2,
    cursor: "pointer",
    userSelect: "none",
  },
  stepDot: {
    position: "absolute",
    left: "-19px",
    top: "14px",
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    border: "2px solid white",
  },
  stepHeader: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  stepMeta: {
    display: "flex",
    gap: "8px",
    fontSize: "11px",
    marginTop: "4px",
    color: tokens.colorNeutralForeground3,
  },
  detail: {
    marginTop: "8px",
    padding: "8px",
    borderRadius: "6px",
    backgroundColor: tokens.colorNeutralBackground3,
    fontSize: "12px",
    whiteSpace: "pre-wrap",
    maxHeight: "200px",
    overflowY: "auto",
  },
  traceInfo: {
    marginTop: "16px",
    padding: "12px",
    borderRadius: "8px",
    backgroundColor: tokens.colorNeutralBackground2,
    fontSize: "12px",
  },
});

interface AgentFlowPanelProps {
  steps: AgentStep[];
  trace: AgentTrace | null;
}

function StepCard({ step }: { step: AgentStep }) {
  const s = useStyles();
  const [expanded, setExpanded] = useState(false);
  const color = STATUS_COLORS[step.status];
  const label =
    AGENT_PIPELINE.find((a) => a.name === step.agent_name)?.label ??
    step.agent_name;

  return (
    <motion.div
      className={s.stepCard}
      onClick={() => setExpanded(!expanded)}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25 }}
    >
      <div className={s.stepDot} style={{ backgroundColor: color }} />

      <div className={s.stepHeader}>
        {expanded ? <ChevronDown24Regular /> : <ChevronRight24Regular />}
        <Text weight="semibold">{label}</Text>
        <Badge
          appearance="outline"
          style={{ borderColor: color, color }}
          size="small"
        >
          {step.status}
        </Badge>
        {step.inference_mode && (
          <Badge
            appearance="tint"
            size="small"
            color={step.inference_mode === "real" ? "success" : "warning"}
          >
            {step.inference_mode === "real" ? "🤖 AI" : "📁 Fallback"}
          </Badge>
        )}
      </div>

      <div className={s.stepMeta}>
        {step.duration_ms != null && <span>{step.duration_ms}ms</span>}
        {step.output_summary && (
          <span>
            {step.output_summary.length > 80
              ? step.output_summary.slice(0, 80) + "…"
              : step.output_summary}
          </span>
        )}
      </div>

      <AnimatePresence>
        {expanded && step.raw_json && (
          <motion.div
            className={s.detail}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {JSON.stringify(step.raw_json, null, 2)}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function AgentFlowPanel({ steps, trace }: AgentFlowPanelProps) {
  const s = useStyles();

  return (
    <div className={s.root}>
      <div className={s.header}>Agent Flow</div>

      {steps.length === 0 ? (
        <Text
          size={200}
          style={{
            color: tokens.colorNeutralForeground3,
            textAlign: "center",
            marginTop: "40px",
          }}
        >
          Send a message to see the agent pipeline in action.
        </Text>
      ) : (
        <div className={s.timeline}>
          <div className={s.line} />
          {steps.map((step) => (
            <StepCard key={step.step_id} step={step} />
          ))}
        </div>
      )}

      {trace && (
        <>
          <Divider style={{ margin: "16px 0 8px" }} />
          <div className={s.traceInfo}>
            <Text weight="semibold">Trace Summary</Text>
            <div style={{ marginTop: 6 }}>
              <div>Trace ID: {trace.trace_id}</div>
              <div>Total: {trace.total_duration_ms}ms</div>
              <div>Decision: {trace.final_decision}</div>
              {trace.decision?.beat_price != null && (
                <div>Beat Price: ${trace.decision.beat_price.toFixed(2)}</div>
              )}
              {trace.decision?.reason_code && (
                <div>Reason: {trace.decision.reason_code}</div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
