import { useEffect, useState, useMemo } from "react";
import { useLinks } from "../hooks/useApi";
import {
  Avatar,
  Box,
  Button,
  Checkbox,
  List,
  ListItemAvatar,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import { Image as ImageIcon } from "@mui/icons-material";

type BookListProps = {
  filterByAuthor?: string;
  checked: string[];
  setChecked: (checked: string[]) => void;
  hideDownloaded: boolean;
  hideNonEnglish: boolean;
  onSelectAll: (allBookUrls: string[]) => void;
  onUnselectAll: () => void;
  onBookTitlesUpdate: (titles: Map<string, string>) => void;
};

export const BookList = ({
  filterByAuthor,
  checked,
  setChecked,
  hideDownloaded,
  hideNonEnglish,
  onSelectAll,
  onUnselectAll,
  onBookTitlesUpdate,
}: BookListProps) => {
  const { links, loading, error } = useLinks(filterByAuthor);

  const filteredLinks = useMemo(() => {
    let filtered = links;

    if (hideDownloaded) {
      filtered = filtered.filter((link) => !link.downloaded);
    }

    if (hideNonEnglish) {
      filtered = filtered.filter(
        (link) => !link.language || link.language.toLowerCase() === "english",
      );
    }

    return filtered;
  }, [links, hideDownloaded, hideNonEnglish]);

  // Update book titles map whenever links change
  useEffect(() => {
    const titlesMap = new Map<string, string>();
    links.forEach((link) => {
      titlesMap.set(link.bookUrl, link.title || "Unknown Book");
    });
    onBookTitlesUpdate(titlesMap);
  }, [links, onBookTitlesUpdate]);

  const handleToggle = (value: string) => () => {
    const currentIndex = checked.indexOf(value);
    const newChecked = [...checked];

    if (currentIndex === -1) {
      newChecked.push(value);
    } else {
      newChecked.splice(currentIndex, 1);
    }

    setChecked(newChecked);
  };

  if (error) return <p>Error: {error}</p>;
  if (loading) return <p>Loading...</p>;

  if (!filteredLinks.length) return <p>No books</p>;

  const allBookUrls = filteredLinks.map((l) => l.bookUrl);
  const allSelected =
    allBookUrls.length > 0 && allBookUrls.every((url) => checked.includes(url));

  return (
    <>
      <Box sx={{ mb: 2, display: "flex", gap: 2 }}>
        <Button
          variant="outlined"
          onClick={() =>
            allSelected ? onUnselectAll() : onSelectAll(allBookUrls)
          }
          size="small"
        >
          {allSelected ? "Unselect All" : "Select All"}
        </Button>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            color: "text.secondary",
          }}
        >
          Showing {filteredLinks.length} book
          {filteredLinks.length !== 1 ? "s" : ""}
        </Box>
      </Box>
      <List dense>
        {filteredLinks.map((l) => (
          <ListItemButton key={l.url} onClick={handleToggle(l.bookUrl)}>
            <ListItemIcon>
              <Checkbox
                edge="start"
                checked={checked.includes(l.bookUrl)}
                tabIndex={-1}
                disableRipple
              />
            </ListItemIcon>
            <ListItemAvatar>
              <Avatar
                src={l.imageUrl}
                style={{ borderRadius: "0%", height: "150px", width: "90px" }}
              >
                <ImageIcon></ImageIcon>
              </Avatar>
            </ListItemAvatar>
            <ListItemText style={{ paddingLeft: "25px", width: "25%" }}>
              {l.title}
            </ListItemText>
            <ListItemText style={{ paddingLeft: "5px", width: "10%" }}>
              {l.bookAuthor ?? l.author}
            </ListItemText>

            <ListItemText style={{ paddingLeft: "5px", width: "10%" }}>
              {l.date}
            </ListItemText>

            <ListItemText style={{ paddingLeft: "5px", width: "30%" }}>
              {l.genre}
            </ListItemText>

            <ListItemText style={{ paddingLeft: "5px", width: "5%" }}>
              {l.language}
            </ListItemText>
          </ListItemButton>
        ))}
      </List>
    </>
  );
};
