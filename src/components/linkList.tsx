import { useEffect, useState } from "react";
import { useAuthors } from "../hooks/useApi";

export const LinkList = () => {
  const { authors, loading, error } = useAuthors();
  const [sortedAuthors, setSortedAuthors] = useState<string[]>([]);

  useEffect(() => {
    setSortedAuthors([...(authors ?? [])].sort());
  }, [authors]);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error}</p>;
  if (!sortedAuthors.length) return <p>No authors</p>;

  return (
    <div>
      <h3>Authors</h3>
      {sortedAuthors.map((author) => (
        <div key={author}>{author}</div>
      ))}
    </div>
  );
};
