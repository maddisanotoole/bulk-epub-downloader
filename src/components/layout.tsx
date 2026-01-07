import { useState } from "react";
import {
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  Toolbar,
  AppBar,
  Typography,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import { AuthorList } from "./authorList";
import { BookList } from "./bookList";

const drawerWidth = 260;

export function Layout() {
  const [open, setOpen] = useState(false);

  const drawer = (
    <Box sx={{ width: drawerWidth, p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Authors
      </Typography>
      <AuthorList />
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
            sx={{ mr: 12, display: { sm: "none" } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap>
            Book Downloader
          </Typography>
        </Toolbar>
      </AppBar>

      {/* <Drawer
        variant="permanent"
        sx={{
          display: { xs: "none", sm: "block" },
          "& .MuiDrawer-paper": { width: drawerWidth, boxSizing: "border-box" },
        }}
        open
      >
        {drawer}
      </Drawer> */}
      <Drawer
        variant="temporary"
        open={open}
        onClose={() => setOpen(false)}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: "block", sm: "none" },
          "& .MuiDrawer-paper": { width: drawerWidth, boxSizing: "border-box" },
        }}
      >
        {drawer}
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        <BookList></BookList>
      </Box>
    </Box>
  );
}
