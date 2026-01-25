import { useAuthors } from "../hooks/useApi";
import { List, ListItemButton, ListItemText } from "@mui/material";

export const AuthorList = ({
  setFilterByAuthor,
}: {
  setFilterByAuthor: (slug: string) => void;
}) => {
  const { authors, loading, error } = useAuthors();

  if (error) return <p>Error: {error}</p>;
  if (loading) return <p>Loading...</p>;

  if (Object.keys(authors).length === 0)
    return <p style={{ paddingTop: "20px" }}>No authors</p>;

  return (
    <List dense>
      {Object.entries(authors).map(([slug, name]) => (
        <ListItemButton key={slug} onClick={() => setFilterByAuthor(slug)}>
          <ListItemText primary={name} />
        </ListItemButton>
      ))}
    </List>
  );
};
