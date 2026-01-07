import { useEffect, useState } from "react";
import { useLinks } from "../hooks/useApi";
import { List, ListItemButton, ListItemText } from "@mui/material";

export const BookList = () => {
  const { links, loading, error } = useLinks();

  if (error) return <p>Error: {error}</p>;
  if (loading) return <p>Loading...</p>;

  if (!links.length) return <p>No books</p>;

  return (
    <List dense>
      {links.map((l) => (
        <ListItemButton key={l.url} onClick={() => console.log("clicked", l)}>
          <div dangerouslySetInnerHTML={{ __html: l.article }} />
        </ListItemButton>
      ))}
    </List>
  );
};
