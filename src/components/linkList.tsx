import { useEffect, useState } from "react";
import { DatabaseHelper } from "../databaseHelper";

export const LinkList = () => {
  console.log("Accessing LinkList");
  const db = new DatabaseHelper();
  const [loading, setLoading] = useState<boolean>(true);
  const [authors, setAuthors] = useState<String[]>([]);
  useEffect(() => {
    setLoading(true);
    const fetchAuthors = async () => {
      const allAuthors = await db.getAllAuthors();

      console.log("Fetched authors:", allAuthors);
      setAuthors(allAuthors.sort());
      setLoading(false);
    };
    fetchAuthors();
  }, []);

  if (loading) {
    return <p>Loading...</p>;
  }

  if (authors.length === 0) {
    return <p>No authors</p>;
  }
  return authors.map((author) => {
    return <div>${author}</div>;
  });
};
