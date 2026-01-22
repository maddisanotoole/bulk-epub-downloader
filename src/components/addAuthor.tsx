import { useState } from "react";
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  CircularProgress,
  Alert,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import { useAddAuthor } from "../hooks/useApi";

interface AddAuthorProps {
  onAuthorAdded: () => void;
}

export function AddAuthor({ onAuthorAdded }: AddAuthorProps) {
  const [authorName, setAuthorName] = useState("");
  const { addAuthor, adding, error, success } = useAddAuthor();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authorName.trim()) return;

    const result = await addAuthor(authorName);
    if (result?.success) {
      setAuthorName("");
      onAuthorAdded();
    }
  };

  return (
    <Paper elevation={2} sx={{ p: 3, maxWidth: 600, mx: "auto", mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Add New Author
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Enter one or more author names to scrape their books from OceanOfPDF.
        Separate multiple authors with commas (e.g., "j k rowling, stephen king,
        rawnie sabor").
      </Typography>
      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          fullWidth
          label="Author Name(s)"
          placeholder="e.g., j k rowling, stephen king"
          value={authorName}
          onChange={(e) => setAuthorName(e.target.value)}
          disabled={adding}
          sx={{ mb: 2 }}
        />
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}
        <Button
          type="submit"
          variant="contained"
          fullWidth
          disabled={!authorName.trim() || adding}
          startIcon={
            adding ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              <AddIcon />
            )
          }
        >
          {adding ? "Scraping..." : "Add Author"}
        </Button>
      </Box>
    </Paper>
  );
}
