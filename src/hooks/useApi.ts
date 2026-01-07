import { useEffect, useState } from "react";
import { Link } from "../types";

const API_BASE = "http://localhost:8000";

export function useAuthors() {
  const [authors, setAuthors] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/authors`, {
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`Authors request failed: ${res.status}`);
        const data = (await res.json()) as string[];
        setAuthors(data.sort());
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

export function useLinks(author?: string) {
  const [links, setLinks] = useState<Link[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const search = author ? `?author=${encodeURIComponent(author)}` : "";
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
  }, [author]);

  return { links, loading, error } as const;
}
