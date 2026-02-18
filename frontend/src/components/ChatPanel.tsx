import { useEffect, useRef, useState } from "react";
import {
  makeStyles,
  tokens,
  Input,
  Button,
  Spinner,
} from "@fluentui/react-components";
import { Send24Regular } from "@fluentui/react-icons";
import { MessageBubble } from "./MessageBubble";
import { ScreenshotViewer } from "./ScreenshotViewer";
import type { ChatMessage } from "../types";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    borderRight: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  header: {
    padding: "16px",
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    fontWeight: 600,
    fontSize: "16px",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  dot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
  },
  messages: {
    flex: 1,
    overflowY: "auto",
    paddingTop: "12px",
    paddingBottom: "12px",
  },
  inputArea: {
    display: "flex",
    gap: "8px",
    padding: "12px 16px",
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
    alignItems: "center",
  },
  input: {
    flex: 1,
  },
  typing: {
    padding: "4px 16px",
    fontSize: "12px",
    color: tokens.colorNeutralForeground3,
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
});

interface ChatPanelProps {
  messages: ChatMessage[];
  connected: boolean;
  isProcessing: boolean;
  onSend: (text: string) => void;
}

export function ChatPanel({
  messages,
  connected,
  isProcessing,
  onSend,
}: ChatPanelProps) {
  const s = useStyles();
  const bottomRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState("");
  const [lightboxUrl, setLightboxUrl] = useState<string | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={s.root}>
      {/* Header */}
      <div className={s.header}>
        <div
          className={s.dot}
          style={{ backgroundColor: connected ? "#2E7D32" : "#C62828" }}
        />
        LLPG Price Beat Agent
      </div>

      {/* Messages */}
      <div className={s.messages}>
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onImageClick={setLightboxUrl}
          />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Typing indicator */}
      {isProcessing && (
        <div className={s.typing}>
          <Spinner size="tiny" />
          Agent is processing…
        </div>
      )}

      {/* Input */}
      <div className={s.inputArea}>
        <Input
          className={s.input}
          placeholder={
            connected
              ? "Paste a competitor URL or describe a price claim…"
              : "Connecting…"
          }
          value={input}
          disabled={!connected || isProcessing}
          onChange={(_, d) => setInput(d.value)}
          onKeyDown={handleKeyDown}
        />
        <Button
          appearance="primary"
          icon={<Send24Regular />}
          disabled={!connected || isProcessing || !input.trim()}
          onClick={handleSend}
        />
      </div>

      {/* Screenshot lightbox */}
      {lightboxUrl && (
        <ScreenshotViewer url={lightboxUrl} onClose={() => setLightboxUrl(null)} />
      )}
    </div>
  );
}
