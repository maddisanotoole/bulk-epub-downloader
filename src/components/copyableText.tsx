import { useState } from "react";
import { ListItemText, Box } from "@mui/material";
import { SxProps, Theme } from "@mui/material/styles";

type CopyableTextProps = {
  text: string;
  children?: React.ReactNode;
  style?: React.CSSProperties;
  sx?: SxProps<Theme>;
  onClick?: (e: React.MouseEvent) => void;
};

export const CopyableText = ({
  text,
  children,
  style,
  sx,
  onClick,
}: CopyableTextProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
    onClick?.(e);
  };

  return (
    <ListItemText
      style={{ ...style, cursor: "pointer" }}
      onClick={handleCopy}
      sx={{
        "&:hover": { backgroundColor: "rgba(0, 0, 0, 0.04)" },
        position: "relative",
        ...sx,
      }}
    >
      {children}
      {copied && (
        <Box
          component="span"
          sx={{ ml: 1, fontSize: "0.75rem", color: "success.main" }}
        >
          ✓ Copied
        </Box>
      )}
    </ListItemText>
  );
};
