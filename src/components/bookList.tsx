import { useEffect, useMemo } from "react";
import { useLinks } from "../hooks/useApi";
import {
  Avatar,
  Checkbox,
  List,
  ListItemAvatar,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import { Image as ImageIcon } from "@mui/icons-material";
import { CopyableText } from "./copyableText";

type BookListProps = {
  filterByAuthor?: string;
  checked: string[];
  setChecked: (checked: string[]) => void;
  hideDownloaded: boolean;
  selectedLanguage: string;
  onSelectAll: (allBookUrls: string[]) => void;
  onUnselectAll: () => void;
  onBookTitlesUpdate: (titles: Map<string, string>) => void;
  searchQuery: string;
  onFilteredCountUpdate: (
    count: number,
    allUrls: string[],
    allSelected: boolean,
  ) => void;
  onAvailableLanguagesUpdate: (languages: string[]) => void;
};

export const BookList = ({
  filterByAuthor,
  checked,
  setChecked,
  hideDownloaded,
  selectedLanguage,
  onSelectAll,
  onUnselectAll,
  onBookTitlesUpdate,
  searchQuery,
  onFilteredCountUpdate,
  onAvailableLanguagesUpdate,
}: BookListProps) => {
  const { links, loading, error } = useLinks(filterByAuthor);

  const filteredLinks = useMemo(() => {
    let filtered = links;

    if (hideDownloaded) {
      filtered = filtered.filter((link) => !link.downloaded);
    }

    if (selectedLanguage !== "All") {
      filtered = filtered.filter(
        (link) =>
          link.language &&
          link.language.toLowerCase() === selectedLanguage.toLowerCase(),
      );
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (link) =>
          link.title?.toLowerCase().includes(query) ||
          link.bookAuthor?.toLowerCase().includes(query) ||
          link.author?.toLowerCase().includes(query) ||
          link.genre?.toLowerCase().includes(query) ||
          link.description?.toLowerCase().includes(query),
      );
    }

    return filtered;
  }, [links, hideDownloaded, selectedLanguage, searchQuery]);

  // Update book titles map whenever links change
  useEffect(() => {
    const titlesMap = new Map<string, string>();
    links.forEach((link) => {
      titlesMap.set(link.bookUrl, link.title || "Unknown Book");
    });
    onBookTitlesUpdate(titlesMap);
  }, [links, onBookTitlesUpdate]);

  useEffect(() => {
    const languagesSet = new Set<string>();
    links.forEach((link) => {
      if (link.language && link.language.trim()) {
        languagesSet.add(link.language);
      }
    });
    const uniqueLanguages = Array.from(languagesSet).sort();
    onAvailableLanguagesUpdate(uniqueLanguages);
  }, [links, onAvailableLanguagesUpdate]);

  useEffect(() => {
    const allBookUrls = filteredLinks.map((l) => l.bookUrl);
    const allSelected =
      allBookUrls.length > 0 &&
      allBookUrls.every((url) => checked.includes(url));
    onFilteredCountUpdate(filteredLinks.length, allBookUrls, allSelected);
  }, [filteredLinks, checked, onFilteredCountUpdate]);

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

  return (
    <>
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
            <CopyableText
              text={l.title || ""}
              style={{ paddingLeft: "25px", width: "25%" }}
            >
              {l.title}
            </CopyableText>
            <CopyableText
              text={l.bookAuthor ?? l.author ?? ""}
              style={{ paddingLeft: "5px", width: "10%" }}
            >
              {l.bookAuthor ?? l.author}
            </CopyableText>

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
