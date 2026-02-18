import {
  makeStyles,
  tokens,
  Badge,
  mergeClasses,
} from "@fluentui/react-components";
import ReactMarkdown from "react-markdown";
import type { ChatMessage, Decision } from "../types";
import { DECISION_COLORS } from "../styles/theme";

const useStyles = makeStyles({
  row: {
    display: "flex",
    marginBottom: "12px",
    paddingLeft: "16px",
    paddingRight: "16px",
  },
  rowUser: { justifyContent: "flex-end" },
  rowAssistant: { justifyContent: "flex-start" },
  rowSystem: { justifyContent: "center" },
  bubble: {
    maxWidth: "75%",
    padding: "10px 14px",
    borderRadius: "12px",
    fontSize: "14px",
    lineHeight: "1.5",
    wordBreak: "break-word",
  },
  bubbleUser: {
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
    borderBottomRightRadius: "4px",
  },
  bubbleAssistant: {
    backgroundColor: tokens.colorNeutralBackground3,
    color: tokens.colorNeutralForeground1,
    borderBottomLeftRadius: "4px",
  },
  bubbleSystem: {
    backgroundColor: "transparent",
    color: tokens.colorNeutralForeground3,
    fontSize: "12px",
    fontStyle: "italic",
  },
  ts: {
    fontSize: "10px",
    color: tokens.colorNeutralForeground4,
    marginTop: "4px",
  },
  badge: {
    marginTop: "6px",
  },
  image: {
    maxWidth: "200px",
    borderRadius: "8px",
    marginTop: "8px",
    cursor: "pointer",
  },
  markdown: {
    "& p": { margin: 0 },
    "& ul, & ol": { paddingLeft: "18px", margin: "4px 0" },
    "& code": {
      backgroundColor: "rgba(0,0,0,0.06)",
      padding: "1px 4px",
      borderRadius: "3px",
      fontSize: "13px",
    },
  },
});

interface MessageBubbleProps {
  message: ChatMessage;
  onImageClick?: (url: string) => void;
}

function decisionLabel(d: Decision): string {
  const map: Record<Decision, string> = {
    AUTO_APPROVE: "✅ Price Beat Approved",
    HUMAN_REVIEW: "🔍 Sent to Review",
    AUTO_REJECT: "❌ Rejected",
    NOT_LLPG: "ℹ️ Not a Price Claim",
    INCOMPLETE: "⚠️ More Info Needed",
    NO_MATCH: "🔎 No Product Match",
  };
  return map[d] ?? d;
}

export function MessageBubble({ message, onImageClick }: MessageBubbleProps) {
  const s = useStyles();
  const roleClass =
    message.role === "user"
      ? s.rowUser
      : message.role === "assistant"
      ? s.rowAssistant
      : s.rowSystem;
  const bubbleClass =
    message.role === "user"
      ? s.bubbleUser
      : message.role === "assistant"
      ? s.bubbleAssistant
      : s.bubbleSystem;

  const colors = message.decision
    ? DECISION_COLORS[message.decision]
    : undefined;

  return (
    <div className={mergeClasses(s.row, roleClass)}>
      <div className={mergeClasses(s.bubble, bubbleClass)}>
        <div className={s.markdown}>
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {message.imageUrl && (
          <img
            src={message.imageUrl}
            alt="attachment"
            className={s.image}
            onClick={() => onImageClick?.(message.imageUrl!)}
          />
        )}

        {message.decision && colors && (
          <div className={s.badge}>
            <Badge
              appearance="filled"
              style={{ backgroundColor: colors.bg, color: colors.fg }}
            >
              {decisionLabel(message.decision)}
            </Badge>
          </div>
        )}

        {message.beat_price != null && (
          <div style={{ marginTop: 4, fontWeight: 600, fontSize: 13 }}>
            Beat Price: ${message.beat_price.toFixed(2)}
          </div>
        )}

        <div className={s.ts}>
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      </div>
    </div>
  );
}
