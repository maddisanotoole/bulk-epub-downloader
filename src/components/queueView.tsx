import { useState } from "react";
import {
  useQueue,
  useCancelQueueItem,
  useDeleteCompletedQueue,
} from "../hooks/useApi";
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Typography,
  Button,
  Tooltip,
  CircularProgress,
} from "@mui/material";
import {
  Refresh as RefreshIcon,
  Cancel as CancelIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  DownloadDone as DownloadingIcon,
} from "@mui/icons-material";

export const QueueView = () => {
  const { queue, loading, error, refetch } = useQueue(true);
  const { cancelItem, cancelling } = useCancelQueueItem();
  const { deleteCompleted, deleting } = useDeleteCompletedQueue();
  const [cancellingId, setCancellingId] = useState<number | null>(null);

  const handleCancel = async (queueId: number) => {
    setCancellingId(queueId);
    try {
      await cancelItem(queueId);
      refetch();
    } catch (err) {
      console.error("Failed to cancel:", err);
    } finally {
      setCancellingId(null);
    }
  };

  const handleDeleteCompleted = async () => {
    try {
      await deleteCompleted();
      refetch();
    } catch (err) {
      console.error("Failed to delete completed:", err);
    }
  };

  const getStatusChip = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
        return (
          <Chip
            icon={<CheckCircleIcon />}
            label="Completed"
            color="success"
            size="small"
          />
        );
      case "failed":
        return (
          <Chip
            icon={<ErrorIcon />}
            label="Failed"
            color="error"
            size="small"
          />
        );
      case "in_progress":
        return (
          <Chip
            icon={<DownloadingIcon />}
            label="Downloading"
            color="primary"
            size="small"
          />
        );
      case "pending":
      default:
        return (
          <Chip
            icon={<PendingIcon />}
            label="Pending"
            color="default"
            size="small"
          />
        );
    }
  };

  const formatDate = (isoDate?: string) => {
    if (!isoDate) return "—";
    const date = new Date(isoDate);
    return date.toLocaleString();
  };

  if (error) return <Typography color="error">Error: {error}</Typography>;

  return (
    <Box>
      <Box
        sx={{ display: "flex", justifyContent: "space-between", mb: 2, mt: 4 }}
      >
        <Typography variant="h5">Download Queue</Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button
            startIcon={<DeleteIcon />}
            onClick={handleDeleteCompleted}
            disabled={
              deleting ||
              queue.filter((q) => q.status === "completed").length === 0
            }
            color="error"
            variant="outlined"
            size="small"
          >
            {deleting ? "Deleting..." : "Clear Completed"}
          </Button>
          <Button
            startIcon={<RefreshIcon />}
            onClick={refetch}
            disabled={loading}
            size="small"
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {loading && queue.length === 0 ? (
        <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
          <CircularProgress />
        </Box>
      ) : queue.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: "center" }}>
          <Typography color="text.secondary">
            Queue is empty. Download some books to see them here!
          </Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Book Title</TableCell>
                <TableCell>Author</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Retry Count</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Started</TableCell>
                <TableCell>Completed</TableCell>
                <TableCell>Error</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {queue.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.id}</TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {item.bookTitle}
                    </Typography>
                  </TableCell>
                  <TableCell>{item.bookAuthor || "—"}</TableCell>
                  <TableCell>{getStatusChip(item.status)}</TableCell>
                  <TableCell>
                    {item.retryCount > 0 ? (
                      <Chip
                        label={item.retryCount}
                        size="small"
                        color="warning"
                      />
                    ) : (
                      "0"
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {formatDate(item.createdAt)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {formatDate(item.startedAt)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {formatDate(item.completedAt)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {item.errorMessage && (
                      <Tooltip title={item.errorMessage}>
                        <Typography
                          variant="caption"
                          color="error"
                          sx={{
                            maxWidth: 200,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            display: "block",
                          }}
                        >
                          {item.errorMessage}
                        </Typography>
                      </Tooltip>
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {item.status === "pending" && (
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleCancel(item.id)}
                        disabled={cancelling && cancellingId === item.id}
                      >
                        {cancelling && cancellingId === item.id ? (
                          <CircularProgress size={20} />
                        ) : (
                          <CancelIcon />
                        )}
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Box sx={{ mt: 2 }}>
        <Typography variant="caption" color="text.secondary">
          Auto-refreshing every 5 seconds • Total items: {queue.length}
        </Typography>
      </Box>
    </Box>
  );
};
