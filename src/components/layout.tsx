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
import AddIcon from "@mui/icons-material/Add";
import { AuthorList } from "./authorList";
import { BookList } from "./bookList";
import { AddAuthor } from "./addAuthor";
import { Notification } from "./notification";
import {
  useDownload,
  useDeleteAuthor,
  useAuthors,
  useCleanupAuthors,
  useDeleteAllAuthors,
} from "../hooks/useApi";

const drawerWidth = 260;

export function Layout() {
  const [showAuthorDrawer, setShowAuthorDrawer] = useState(false);
  const [filterByAuthor, setFilterByAuthor] = useState<string | undefined>(
    undefined,
  );
  const [checked, setChecked] = useState<string[]>([]);
  const [hideDownloaded, setHideDownloaded] = useState(true);
  const [hideNonEnglish, setHideNonEnglish] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [cleanupDialogOpen, setCleanupDialogOpen] = useState(false);
  const [deleteAllDialogOpen, setDeleteAllDialogOpen] = useState(false);
  const [refreshAuthors, setRefreshAuthors] = useState(0);
  const [showAddAuthor, setShowAddAuthor] = useState(false);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [bookTitles, setBookTitles] = useState<Map<string, string>>(new Map());
  const { download, downloading, progress, failures } = useDownload();
  const { deleteAuthor, deleting } = useDeleteAuthor();
  const { cleanupAuthors, cleaning } = useCleanupAuthors();
  const { deleteAllAuthors, deleting: deletingAll } = useDeleteAllAuthors();
  const { authors } = useAuthors(refreshAuthors > 0);

  const handleDownload = async () => {
    if (checked.length > 0) {
      const toDownload = checked;
      setChecked([]);
      await download(toDownload, bookTitles);
      if (failures.length > 0) {
        setNotificationOpen(true);
      }
    }
  };

  const handleSelectAll = (allBookUrls: string[]) => {
    setChecked(allBookUrls);
  };

  const handleUnselectAll = () => {
    setChecked([]);
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

  const handleCleanupClick = () => {
    setCleanupDialogOpen(true);
  };

  const handleConfirmCleanup = async () => {
    try {
      const result = await cleanupAuthors();
      setCleanupDialogOpen(false);
      setFilterByAuthor(undefined);
      setChecked([]);
      setRefreshAuthors((prev) => prev + 1);
      console.log(
        `Cleanup complete: ${result.authors_deleted} author(s) deleted`,
      );
      window.location.reload();
    } catch (err) {
      console.error("Failed to cleanup authors", err);
    }
  };

  const handleDeleteAllClick = () => {
    setDeleteAllDialogOpen(true);
  };

  const handleConfirmDeleteAll = async () => {
    try {
      const result = await deleteAllAuthors();
      setDeleteAllDialogOpen(false);
      setFilterByAuthor(undefined);
      setChecked([]);
      console.log(
        `Deleted all: ${result.authors_deleted} author(s), ${result.books_deleted} book(s)`,
      );
      window.location.reload();
    } catch (err) {
      console.error("Failed to delete all authors", err);
    }
  };

  const handleAuthorAdded = () => {
    setRefreshAuthors((prev) => prev + 1);
  };

  const handleBookTitlesUpdate = (titles: Map<string, string>) => {
    setBookTitles(titles);
  };

  const handleCloseNotification = () => {
    setNotificationOpen(false);
  };

  const drawer = (
    <Box sx={{ width: drawerWidth, p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Authors
      </Typography>
      <AuthorList setFilterByAuthor={setFilterByAuthor} />
      <Box sx={{ mt: 2, display: "flex", flexDirection: "column", gap: 1 }}>
        <Button
          variant="outlined"
          color="warning"
          size="small"
          fullWidth
          onClick={handleCleanupClick}
          disabled={cleaning}
        >
          {cleaning ? "Cleaning..." : "Cleanup Downloaded"}
        </Button>
        <Button
          variant="outlined"
          color="error"
          size="small"
          fullWidth
          onClick={handleDeleteAllClick}
          disabled={deletingAll}
        >
          {deletingAll ? "Deleting..." : "Delete All"}
        </Button>
      </Box>
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
            onClick={() => {
              setShowAuthorDrawer(!showAuthorDrawer);

              if (!showAuthorDrawer) {
                setShowAddAuthor(false);
              }
            }}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap sx={{ flexGrow: 1 }}>
            Book Downloader
          </Typography>
          <Button
            color="inherit"
            startIcon={<AddIcon />}
            onClick={() => {
              setShowAddAuthor(!showAddAuthor);
            }}
            sx={{ mr: 2 }}
          >
            {showAddAuthor ? "View Books" : "Add Author"}
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
            {downloading &&
              ` - ${progress.completed}/${progress.total}${progress.failed > 0 ? ` (${progress.failed} failed)` : ""}`}
          </Button>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="temporary"
        open={showAuthorDrawer}
        onClose={() => setShowAuthorDrawer(false)}
        sx={{
          display: { xs: "none", sm: "block" },
          "& .MuiDrawer-paper": { width: drawerWidth, boxSizing: "border-box" },
        }}
      >
        {drawer}
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        {showAddAuthor ? (
          <AddAuthor onAuthorAdded={handleAuthorAdded} />
        ) : (
          <>
            <Box sx={{ mb: 2, display: "flex", gap: 2, alignItems: "center" }}>
              {filterByAuthor && (
                <Box sx={{ mr: 2 }}>
                  <Typography
                    variant="subtitle1"
                    component="span"
                    sx={{ mr: 2 }}
                  >
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
              onBookTitlesUpdate={handleBookTitlesUpdate}
            />
          </>
        )}
      </Box>
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
      <Dialog
        open={cleanupDialogOpen}
        onClose={() => setCleanupDialogOpen(false)}
      >
        <DialogTitle>Cleanup Downloaded Authors</DialogTitle>
        <DialogContent>
          <Typography>
            This will delete all authors who have no undownloaded books (all
            their books have been downloaded). This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCleanupDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleConfirmCleanup}
            variant="contained"
            color="warning"
            disabled={cleaning}
          >
            {cleaning ? "Cleaning..." : "Cleanup"}
          </Button>
        </DialogActions>
      </Dialog>
      <Dialog
        open={deleteAllDialogOpen}
        onClose={() => setDeleteAllDialogOpen(false)}
      >
        <DialogTitle>Delete All Authors and Books</DialogTitle>
        <DialogContent>
          <Typography>
            <strong>WARNING:</strong> This will permanently delete ALL authors
            and ALL books from the database, regardless of download status. This
            action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteAllDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleConfirmDeleteAll}
            variant="contained"
            color="error"
            disabled={deletingAll}
          >
            {deletingAll ? "Deleting..." : "Delete All"}
          </Button>
        </DialogActions>
      </Dialog>
      <Notification
        open={notificationOpen}
        onClose={handleCloseNotification}
        failures={failures}
      />
    </Box>
  );
}
