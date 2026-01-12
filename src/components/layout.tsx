import { useState } from "react";
import {
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  Toolbar,
  AppBar,
  Typography,
  Button,
  CircularProgress,
  TextField,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Checkbox,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import DownloadIcon from "@mui/icons-material/Download";
import FolderIcon from "@mui/icons-material/Folder";
import { AuthorList } from "./authorList";
import { BookList } from "./bookList";
import { useDownload, useDeleteAuthor, useAuthors } from "../hooks/useApi";

const drawerWidth = 260;

export function Layout() {
  const [open, setOpen] = useState(false);
  const [filterByAuthor, setFilterByAuthor] = useState<string | undefined>(
    undefined
  );
  const [checked, setChecked] = useState<string[]>([]);
  const [destination, setDestination] = useState<string | undefined>(undefined);
  const [folderDialogOpen, setFolderDialogOpen] = useState(false);
  const [tempDestination, setTempDestination] = useState("");
  const [hideDownloaded, setHideDownloaded] = useState(true);
  const [hideNonEnglish, setHideNonEnglish] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [refreshAuthors, setRefreshAuthors] = useState(0);
  const { download, downloading, progress } = useDownload();
  const { deleteAuthor, deleting } = useDeleteAuthor();
  const { authors } = useAuthors(refreshAuthors > 0);

  const handleDownload = async () => {
    if (checked.length > 0) {
      await download(checked, destination);
    }
  };

  const handleSelectAll = (allBookUrls: string[]) => {
    setChecked(allBookUrls);
  };

  const handleUnselectAll = () => {
    setChecked([]);
  };

  const handleSaveDestination = () => {
    setDestination(tempDestination || undefined);
    setFolderDialogOpen(false);
  };

  const handleSelectFolder = async () => {
    try {
      // @ts-ignore - File System Access API
      if ("showDirectoryPicker" in window) {
        // @ts-ignore
        const dirHandle = await window.showDirectoryPicker();
        const path = dirHandle.name;
        setTempDestination(path);
      } else {
        alert(
          "Folder picker not supported in this browser. Please enter path manually."
        );
      }
    } catch (err) {
      console.log("Folder selection cancelled or failed", err);
    }
  };

  const handleDeleteAuthorClick = () => {
    if (filterByAuthor) {
      setDeleteDialogOpen(true);
    }
  };

  const handleConfirmDelete = async () => {
    if (filterByAuthor) {
      try {
        await deleteAuthor(filterByAuthor);
        setDeleteDialogOpen(false);
        setFilterByAuthor(undefined);
        setChecked([]);
        setRefreshAuthors((prev) => prev + 1);
      } catch (err) {
        console.error("Failed to delete author", err);
      }
    }
  };

  const drawer = (
    <Box sx={{ width: drawerWidth, p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Authors
      </Typography>
      <AuthorList setFilterByAuthor={setFilterByAuthor} />
    </Box>
  );

  return (
    <Box sx={{ display: "flex" }}>
      <CssBaseline />
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setOpen(!open)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap sx={{ flexGrow: 1 }}>
            Book Downloader
          </Typography>
          <Button
            color="inherit"
            startIcon={<FolderIcon />}
            onClick={() => {
              setTempDestination(destination || "");
              setFolderDialogOpen(true);
            }}
            sx={{ mr: 2 }}
          >
            {destination ? "Custom Folder" : "Downloads"}
          </Button>
          <Button
            color="inherit"
            startIcon={
              downloading ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                <DownloadIcon />
              )
            }
            onClick={handleDownload}
            disabled={checked.length === 0 || downloading}
          >
            Download Selected ({checked.length})
            {downloading && ` - ${progress.completed}/${progress.total}`}
          </Button>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="temporary"
        open={open}
        onClose={() => setOpen(false)}
        sx={{
          display: { xs: "none", sm: "block" },
          "& .MuiDrawer-paper": { width: drawerWidth, boxSizing: "border-box" },
        }}
      >
        {drawer}
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        <Box sx={{ mb: 2, display: "flex", gap: 2, alignItems: "center" }}>
          {filterByAuthor && (
            <Box sx={{ mr: 2 }}>
              <Typography variant="subtitle1" component="span" sx={{ mr: 2 }}>
                Viewing: {authors[filterByAuthor] || filterByAuthor}
              </Typography>
              <Button
                variant="outlined"
                color="error"
                size="small"
                onClick={handleDeleteAuthorClick}
                disabled={deleting}
                sx={{ mr: 2 }}
              >
                {deleting ? "Deleting..." : "Delete Author"}
              </Button>
              <Button
                variant="outlined"
                size="small"
                onClick={() => setFilterByAuthor(undefined)}
              >
                Clear Filter
              </Button>
            </Box>
          )}
          <FormControlLabel
            control={
              <Checkbox
                checked={hideDownloaded}
                onChange={(e) => setHideDownloaded(e.target.checked)}
              />
            }
            label="Hide downloaded books"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={hideNonEnglish}
                onChange={(e) => setHideNonEnglish(e.target.checked)}
              />
            }
            label="English only"
          />
        </Box>
        <BookList
          filterByAuthor={filterByAuthor}
          checked={checked}
          setChecked={setChecked}
          hideDownloaded={hideDownloaded}
          hideNonEnglish={hideNonEnglish}
          onSelectAll={handleSelectAll}
          onUnselectAll={handleUnselectAll}
        />
      </Box>

      <Dialog
        open={folderDialogOpen}
        onClose={() => setFolderDialogOpen(false)}
      >
        <DialogTitle>Set Download Destination</DialogTitle>
        <DialogContent>
          <Box
            sx={{ display: "flex", gap: 2, alignItems: "flex-start", mt: 1 }}
          >
            <TextField
              autoFocus
              margin="dense"
              label="Folder Path (leave empty for Downloads)"
              type="text"
              fullWidth
              variant="outlined"
              value={tempDestination}
              onChange={(e) => setTempDestination(e.target.value)}
              placeholder="e.g., C:\Users\YourName\Documents\Books"
              helperText="Leave empty to use the Downloads folder"
            />
            <Button
              variant="outlined"
              onClick={handleSelectFolder}
              sx={{ mt: 1, minWidth: "120px" }}
            >
              Browse...
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFolderDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveDestination} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Author</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete{" "}
            {filterByAuthor && authors[filterByAuthor]
              ? authors[filterByAuthor]
              : filterByAuthor}{" "}
            and all their books? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleConfirmDelete}
            variant="contained"
            color="error"
            disabled={deleting}
          >
            {deleting ? "Deleting..." : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
