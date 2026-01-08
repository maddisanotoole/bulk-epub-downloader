import { useEffect, useState } from "react";
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

export const BookList = () => {
  const { links, loading, error } = useLinks();
  const [checked, setChecked] = useState<string[]>([]);
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

  if (!links.length) return <p>No books</p>;

  return (
    <List dense>
      {links.map((l) => (
        <ListItemButton key={l.url} onClick={handleToggle(l.url)}>
          <ListItemIcon>
            <Checkbox
              edge="start"
              checked={checked.includes(l.url)}
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
          <ListItemText style={{ paddingLeft: "5px", width: "25%" }}>
            {l.title}
          </ListItemText>
          <ListItemText style={{ paddingLeft: "5px", width: "10%" }}>
            {l.bookAuthor}
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
  );
};
