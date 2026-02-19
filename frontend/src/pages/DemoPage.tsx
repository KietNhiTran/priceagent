import { useMemo } from "react";
import {
  makeStyles,
  tokens,
  Text,
  Tooltip,
  Badge,
} from "@fluentui/react-components";
import { useWebSocket } from "../hooks/useWebSocket";
import { ChatPanel } from "../components/ChatPanel";
import { AgentFlowPanel } from "../components/AgentFlowPanel";
import { AgentOrchestrationBar } from "../components/AgentOrchestrationBar";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    backgroundColor: tokens.colorNeutralBackground1,
    color: tokens.colorNeutralForeground1,
  },
  topBar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "8px 20px",
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    backgroundColor: tokens.colorNeutralBackground2,
  },
  brand: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  logo: {
    width: "28px",
    height: "28px",
    borderRadius: "6px",
    backgroundColor: "#1B5E20",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "white",
    fontWeight: 700,
    fontSize: "14px",
  },
  body: {
    flex: 1,
    display: "flex",
    overflow: "hidden",
  },
  chatColumn: {
    flex: "0 0 45%",
    minWidth: "360px",
  },
  flowColumn: {
    flex: 1,
    minWidth: "300px",
  },
});

export function DemoPage() {
  const s = useStyles();
  const { connected, messages, steps, currentTrace, sendMessage } =
    useWebSocket();

  const isProcessing = useMemo(() => {
    return steps.some((s) => s.status === "running");
  }, [steps]);

  return (
    <div className={s.root}>
      {/* Top branding bar */}
      <div className={s.topBar}>
        <div className={s.brand}>
          <div className={s.logo}>DM</div>
          <Text weight="semibold" size={400}>
            LLPG Reactive Price Beat Agent
          </Text>
          <Badge appearance="outline" size="small" color="informative">
            MVP Demo
          </Badge>
        </div>
        <Tooltip content={connected ? "WebSocket connected" : "Disconnected"} relationship="label">
          <Badge
            appearance="filled"
            color={connected ? "success" : "danger"}
            size="small"
          >
            {connected ? "Connected" : "Offline"}
          </Badge>
        </Tooltip>
      </div>

      {/* Orchestration progress bar */}
      <AgentOrchestrationBar steps={steps} />

      {/* Main body: chat + agent flow */}
      <div className={s.body}>
        <div className={s.chatColumn}>
          <ChatPanel
            messages={messages}
            connected={connected}
            isProcessing={isProcessing}
            onSend={sendMessage}
          />
        </div>
        <div className={s.flowColumn}>
          <AgentFlowPanel steps={steps} trace={currentTrace} />
        </div>
      </div>
    </div>
  );
}
