import { useEffect, useState } from "react";
import { Authors, Link } from "../types";

const API_BASE = "http://localhost:8000";

let cachedAuthors: Authors | null = null;

export function useAuthors(refresh: boolean = false) {
  const [authors, setAuthors] = useState<Authors>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        if (!refresh && cachedAuthors) {
          setAuthors(cachedAuthors);
        } else {
          const res = await fetch(`${API_BASE}/authors`, {
            signal: controller.signal,
          });
          if (!res.ok) throw new Error(`Authors request failed: ${res.status}`);
          const data = (await res.json()) as Authors;
          setAuthors(data);
          cachedAuthors = data;
        }
      } catch (err: any) {
        if (err.name === "AbortError") return;
        setError(err.message ?? "Failed to fetch authors");
      } finally {
        setLoading(false);
      }
    };
    run();
    return () => controller.abort();
  }, []);

  return { authors, loading, error } as const;
}

export function useLinks(filterByAuthor?: string) {
  const [links, setLinks] = useState<Link[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const search = filterByAuthor
          ? `?author=${encodeURIComponent(filterByAuthor)}`
          : "";
        const res = await fetch(`${API_BASE}/links${search}`, {
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`Links request failed: ${res.status}`);
        const data = (await res.json()) as Link[];
        setLinks(data);
      } catch (err: any) {
        if (err.name === "AbortError") return;
        setError(err.message ?? "Failed to fetch links");
      } finally {
        setLoading(false);
      }
    };
    run();
    return () => controller.abort();
  }, [filterByAuthor]);

  return { links, loading, error } as const;
}
