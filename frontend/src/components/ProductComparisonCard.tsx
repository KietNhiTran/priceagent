import { makeStyles, tokens, Text, Badge } from "@fluentui/react-components";
import type { ProductComparison } from "../types";
import { DECISION_COLORS } from "../styles/theme";

const useStyles = makeStyles({
  card: {
    display: "grid",
    gridTemplateColumns: "1fr auto 1fr",
    gap: "16px",
    padding: "16px",
    borderRadius: "12px",
    backgroundColor: tokens.colorNeutralBackground2,
    margin: "12px 16px",
  },
  product: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  label: { fontSize: "11px", color: tokens.colorNeutralForeground3 },
  name: { fontWeight: 600, fontSize: "14px" },
  price: { fontSize: "22px", fontWeight: 700 },
  vs: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: 600,
    color: tokens.colorNeutralForeground3,
    fontSize: "14px",
  },
  footer: {
    gridColumn: "1 / -1",
    display: "flex",
    alignItems: "center",
    gap: "12px",
    paddingTop: "8px",
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
  },
});

export function ProductComparisonCard({
  comparison,
}: {
  comparison: ProductComparison;
}) {
  const s = useStyles();
  const colors = DECISION_COLORS[comparison.decision] ?? {
    bg: "#E0E0E0",
    fg: "#333",
  };

  return (
    <div className={s.card}>
      {/* Our product */}
      <div className={s.product}>
        <span className={s.label}>Dan Murphy's</span>
        <span className={s.name}>{comparison.our_product}</span>
        <span style={{ fontSize: 11, color: tokens.colorNeutralForeground3 }}>
          SKU: {comparison.our_sku}
        </span>
        <span className={s.price}>${comparison.our_price.toFixed(2)}</span>
      </div>

      {/* VS separator */}
      <div className={s.vs}>VS</div>

      {/* Competitor product */}
      <div className={s.product} style={{ textAlign: "right" }}>
        <span className={s.label}>{comparison.competitor_name}</span>
        <span className={s.name}>{comparison.competitor_product}</span>
        <span className={s.price}>
          ${comparison.competitor_price.toFixed(2)}
        </span>
      </div>

      {/* Footer */}
      <div className={s.footer}>
        <Badge
          appearance="filled"
          style={{ backgroundColor: colors.bg, color: colors.fg }}
        >
          {comparison.decision.replace("_", " ")}
        </Badge>

        {comparison.beat_price != null && (
          <Text weight="semibold" size={400}>
            Beat Price: ${comparison.beat_price.toFixed(2)}
          </Text>
        )}

        {comparison.rsa_floor != null && (
          <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
            RSA Floor: ${comparison.rsa_floor.toFixed(2)}
            {comparison.rsa_compliant != null &&
              (comparison.rsa_compliant ? " ✅" : " ⚠️")}
          </Text>
        )}
      </div>
    </div>
  );
}
