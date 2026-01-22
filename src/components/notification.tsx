import { Alert, Snackbar, Link, Box, Typography } from "@mui/material";
import { DownloadFailure } from "../types";

type NotificationProps = {
  open: boolean;
  onClose: () => void;
  failures: DownloadFailure[];
};

export const Notification = ({
  open,
  onClose,
  failures,
}: NotificationProps) => {
  if (failures.length === 0) return null;

  const message =
    failures.length === 1
      ? `Failed to download: ${failures[0].bookTitle}`
      : `${failures.length} downloads failed`;

  return (
    <Snackbar
      open={open}
      autoHideDuration={8000}
      onClose={onClose}
      anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
    >
      <Alert
        onClose={onClose}
        severity="error"
        sx={{ width: "100%", maxWidth: 500 }}
      >
        <Typography variant="body2" fontWeight="bold" gutterBottom>
          {message}
        </Typography>
        {failures.length <= 3 ? (
          <Box component="ul" sx={{ margin: 0, paddingLeft: 2 }}>
            {failures.map((failure, index) => (
              <li key={index}>
                <Typography variant="body2">
                  <strong>{failure.bookTitle}</strong>: {failure.error}
                </Typography>
              </li>
            ))}
          </Box>
        ) : (
          <>
            <Box component="ul" sx={{ margin: 0, paddingLeft: 2 }}>
              {failures.slice(0, 2).map((failure, index) => (
                <li key={index}>
                  <Typography variant="body2">
                    <strong>{failure.bookTitle}</strong>: {failure.error}
                  </Typography>
                </li>
              ))}
            </Box>
            <Typography variant="body2" sx={{ mt: 1 }}>
              ...and {failures.length - 2} more
            </Typography>
          </>
        )}
      </Alert>
    </Snackbar>
  );
};
