import { useState } from "react";
import {
  makeStyles,
  tokens,
  Text,
  Button,
} from "@fluentui/react-components";
import {
  ChevronDown24Regular,
  ChevronRight24Regular,
} from "@fluentui/react-icons";
import type { AgentTrace } from "../types";

const useStyles = makeStyles({
  root: {
    padding: "12px",
    borderRadius: "8px",
    backgroundColor: tokens.colorNeutralBackground2,
    margin: "8px 16px",
    fontSize: "12px",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    cursor: "pointer",
    userSelect: "none",
  },
  json: {
    marginTop: "8px",
    padding: "8px",
    borderRadius: "6px",
    backgroundColor: tokens.colorNeutralBackground3,
    whiteSpace: "pre-wrap",
    maxHeight: "400px",
    overflowY: "auto",
    fontFamily: "'Cascadia Code', 'Consolas', monospace",
    fontSize: "11px",
    lineHeight: "1.5",
  },
});

export function TraceViewer({ trace }: { trace: AgentTrace }) {
  const s = useStyles();
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={s.root}>
      <div className={s.header} onClick={() => setExpanded(!expanded)}>
        <Button
          appearance="subtle"
          size="small"
          icon={expanded ? <ChevronDown24Regular /> : <ChevronRight24Regular />}
        />
        <Text weight="semibold">Trace: {trace.trace_id.slice(0, 8)}…</Text>
        <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
          {trace.total_duration_ms}ms · {trace.steps.length} steps
        </Text>
      </div>

      {expanded && (
        <div className={s.json}>{JSON.stringify(trace, null, 2)}</div>
      )}
    </div>
  );
}
