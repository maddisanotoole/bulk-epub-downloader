import { useAuthors } from "../hooks/useApi";
import { List, ListItemButton, ListItemText } from "@mui/material";

export const AuthorList = () => {
  const { authors, loading, error } = useAuthors();

  if (error) return <p>Error: {error}</p>;
  if (loading) return <p>Loading...</p>;

  if (Object.keys(authors).length === 0) return <p>No authors</p>;

  return (
    <List dense>
      {Object.entries(authors).map(([slug, name]) => (
        <ListItemButton key={slug} onClick={() => console.log("clicked", slug)}>
          <ListItemText primary={name} />
        </ListItemButton>
      ))}
    </List>
  );
};
