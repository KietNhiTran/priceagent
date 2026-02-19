import { createLightTheme, createDarkTheme } from "@fluentui/react-components";
import type { BrandVariants, Theme } from "@fluentui/react-components";

/**
 * Endeavour Group brand colours (approximated from Dan Murphy's palette).
 * Primary: deep forest green (#1B5E20), accent: warm gold.
 */
const endeavourBrand: BrandVariants = {
  10: "#020D03",
  20: "#0A1F0D",
  30: "#112E14",
  40: "#173C1A",
  50: "#1B4A1F",
  60: "#1F5924",
  70: "#236829",
  80: "#2E7D32",
  90: "#43A047",
  100: "#66BB6A",
  110: "#81C784",
  120: "#A5D6A7",
  130: "#C8E6C9",
  140: "#E8F5E9",
  150: "#F1F8E9",
  160: "#FAFFF5",
};

export const lightTheme: Theme = {
  ...createLightTheme(endeavourBrand),
};

export const darkTheme: Theme = {
  ...createDarkTheme(endeavourBrand),
};

// Override background so it's not tinted green
darkTheme.colorNeutralBackground1 = "#1a1a2e";
darkTheme.colorNeutralBackground2 = "#16213e";
darkTheme.colorNeutralBackground3 = "#0f3460";

/* Decision badge colours */
export const DECISION_COLORS: Record<string, { bg: string; fg: string }> = {
  AUTO_APPROVE: { bg: "#E8F5E9", fg: "#1B5E20" },
  SEND_TO_REVIEW: { bg: "#FFF3E0", fg: "#E65100" },
  AUTO_REJECT: { bg: "#FFEBEE", fg: "#B71C1C" },
  NOT_LLPG: { bg: "#E3F2FD", fg: "#0D47A1" },
  INCOMPLETE: { bg: "#FFF9C4", fg: "#F57F17" },
  NO_MATCH: { bg: "#F3E5F5", fg: "#4A148C" },
};

/* Step status colours for the agent flow panel */
export const STATUS_COLORS: Record<string, string> = {
  pending: "#9E9E9E",
  running: "#1976D2",
  completed: "#2E7D32",
  failed: "#C62828",
};
