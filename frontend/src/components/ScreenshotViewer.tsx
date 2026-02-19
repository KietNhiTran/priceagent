import { makeStyles, tokens } from "@fluentui/react-components";

const useStyles = makeStyles({
  overlay: {
    position: "fixed",
    inset: 0,
    backgroundColor: "rgba(0,0,0,0.8)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 9999,
    cursor: "pointer",
  },
  image: {
    maxWidth: "90vw",
    maxHeight: "90vh",
    borderRadius: "8px",
    boxShadow: tokens.shadow64,
  },
});

interface ScreenshotViewerProps {
  url: string;
  onClose: () => void;
}

export function ScreenshotViewer({ url, onClose }: ScreenshotViewerProps) {
  const s = useStyles();

  return (
    <div className={s.overlay} onClick={onClose}>
      <img
        src={url}
        alt="Screenshot"
        className={s.image}
        onClick={(e) => e.stopPropagation()}
      />
    </div>
  );
}
