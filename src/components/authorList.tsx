import { useEffect, useState } from "react";
import { useAuthors } from "../hooks/useApi";
import { List, ListItemButton, ListItemText } from "@mui/material";

export const AuthorList = () => {
  const { authors, loading, error } = useAuthors();
  const [sortedAuthors, setSortedAuthors] = useState<string[]>([]);

  useEffect(() => {
    setSortedAuthors([...(authors ?? [])].sort());
  }, [authors]);

  if (error) return <p>Error: {error}</p>;
  if (loading) return <p>Loading...</p>;

  if (!sortedAuthors.length) return <p>No authors</p>;

  return (
    <List dense>
      {sortedAuthors.map((a) => (
        <ListItemButton key={a} onClick={() => console.log("clicked", a)}>
          <ListItemText primary={a} />
        </ListItemButton>
      ))}
    </List>
  );
};
