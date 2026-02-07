import { useEffect, useState } from "react";
import { Authors, Link, QueueItem } from "../types";

const API_BASE = "http://localhost:8000";

let cachedAuthors: Authors | null = null;

export interface DownloadFailure {
  bookUrl: string;
  bookTitle: string;
  error: string;
}

export function useDownload() {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState({
    completed: 0,
    total: 0,
    failed: 0,
  });
  const [failures, setFailures] = useState<DownloadFailure[]>([]);

  const download = async (
    bookUrls: string[],
    bookTitles: Map<string, string>,
    destination?: string,
  ) => {
    setDownloading(true);
    setError(null);
    setFailures([]);
    setProgress({ completed: 0, total: bookUrls.length, failed: 0 });

    const failedDownloads: DownloadFailure[] = [];

    try {
      const books = bookUrls.map((bookUrl) => ({
        bookUrl,
        bookTitle: bookTitles.get(bookUrl) || "Unknown Book",
        bookAuthor: undefined,
      }));

      const body: any = { books };
      if (destination) {
        body.destination = destination;
      }

      const res = await fetch(`${API_BASE}/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          data.detail || `Request failed with status: ${res.status}`,
        );
      }

      let completed = 0;
      let failed = 0;

      if (data.results) {
        for (const result of data.results) {
          if (result.success && !result.error) {
            completed++;
          } else {
            failed++;
            failedDownloads.push({
              bookUrl: result.bookUrl,
              bookTitle: result.bookTitle,
              error: result.error || result.message || "Unknown error",
            });
          }
        }
      }

      setProgress({ completed, total: bookUrls.length, failed });
      setFailures(failedDownloads);

      if (failedDownloads.length > 0) {
        setError(`${failedDownloads.length} download(s) failed`);
      }
    } catch (err: any) {
      setError(err.message ?? "Network error");
      for (const bookUrl of bookUrls) {
        failedDownloads.push({
          bookUrl,
          bookTitle: bookTitles.get(bookUrl) || "Unknown Book",
          error: err.message ?? "Network error",
        });
      }
      setFailures(failedDownloads);
      setProgress({
        completed: 0,
        total: bookUrls.length,
        failed: bookUrls.length,
      });
    } finally {
      setDownloading(false);
    }
  };

  return { download, downloading, error, progress, failures } as const;
}

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

export function useDeleteAuthor() {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deleteAuthor = async (authorSlug: string) => {
    setDeleting(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_BASE}/authors/${encodeURIComponent(authorSlug)}`,
        {
          method: "DELETE",
        },
      );
      if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
      const data = await res.json();
      cachedAuthors = null;
      return data;
    } catch (err: any) {
      setError(err.message ?? "Failed to delete author");
      throw err;
    } finally {
      setDeleting(false);
    }
  };

  return { deleteAuthor, deleting, error } as const;
}

export function useAddAuthor() {
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const addAuthor = async (authorName: string) => {
    setAdding(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(`${API_BASE}/scrape-authors`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ authors: authorName }),
      });
      if (!res.ok) throw new Error(`Add author failed: ${res.status}`);
      const data = await res.json();

      if (data.error) {
        throw new Error(data.error);
      }

      cachedAuthors = null;
      const results: string[] = [];
      for (const result of data.results) {
        results.push(`${result.books_added} book(s) for ${result.author}`);
      }

      setSuccess(`Successfully added ${results.join(", ")}`);
      return data;
    } catch (err: any) {
      setError(err.message ?? "Failed to add author");
      throw err;
    } finally {
      setAdding(false);
    }
  };

  return { addAuthor, adding, error, success } as const;
}

export function useCleanupAuthors() {
  const [cleaning, setCleaning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cleanupAuthors = async () => {
    setCleaning(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/authors/cleanup`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error(`Cleanup failed: ${res.status}`);
      const data = await res.json();
      cachedAuthors = null;
      return data;
    } catch (err: any) {
      setError(err.message ?? "Failed to cleanup authors");
      throw err;
    } finally {
      setCleaning(false);
    }
  };

  return { cleanupAuthors, cleaning, error } as const;
}

export function useDeleteAllAuthors() {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deleteAllAuthors = async () => {
    setDeleting(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/authors/all`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error(`Delete all failed: ${res.status}`);
      const data = await res.json();
      cachedAuthors = null;
      return data;
    } catch (err: any) {
      setError(err.message ?? "Failed to delete all authors");
      throw err;
    } finally {
      setDeleting(false);
    }
  };

  return { deleteAllAuthors, deleting, error } as const;
}

export function useQueue(autoRefresh = false) {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQueue = async () => {
    try {
      const res = await fetch(`${API_BASE}/queue`);
      if (!res.ok) throw new Error(`Failed to fetch queue: ${res.status}`);
      const data = await res.json();
      setQueue(data);
      setError(null);
    } catch (err: any) {
      setError(err.message ?? "Failed to fetch queue");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();

    if (autoRefresh) {
      const interval = setInterval(fetchQueue, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  return { queue, loading, error, refetch: fetchQueue } as const;
}

export function useCancelQueueItem() {
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cancelItem = async (queueId: number) => {
    setCancelling(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/queue/${queueId}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `Cancel failed: ${res.status}`);
      }
      return await res.json();
    } catch (err: any) {
      setError(err.message ?? "Failed to cancel queue item");
      throw err;
    } finally {
      setCancelling(false);
    }
  };

  return { cancelItem, cancelling, error } as const;
}

export function useDeleteCompletedQueue() {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deleteCompleted = async () => {
    setDeleting(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/queue/completed/all`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `Delete failed: ${res.status}`);
      }
      return await res.json();
    } catch (err: any) {
      setError(err.message ?? "Failed to delete completed items");
      throw err;
    } finally {
      setDeleting(false);
    }
  };

  return { deleteCompleted, deleting, error } as const;
}

export function useDeleteAllQueue() {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deleteAll = async () => {
    setDeleting(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/queue/all`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `Delete failed: ${res.status}`);
      }
      return await res.json();
    } catch (err: any) {
      setError(err.message ?? "Failed to delete all queue items");
      throw err;
    } finally {
      setDeleting(false);
    }
  };

  return { deleteAll, deleting, error } as const;
}

export function useDeletePendingQueue() {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deletePending = async () => {
    setDeleting(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/queue/pending/all`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `Delete failed: ${res.status}`);
      }
      return await res.json();
    } catch (err: any) {
      setError(err.message ?? "Failed to delete pending items");
      throw err;
    } finally {
      setDeleting(false);
    }
  };

  return { deletePending, deleting, error } as const;
}
