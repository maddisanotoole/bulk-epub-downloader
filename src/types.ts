export type Authors = Record<string, string>;

export type Author = {
  slug: string;
  name: string;
};

export interface DownloadFailure {
  bookUrl: string;
  bookTitle: string;
  error: string;
}

export type Link = {
  url: string;
  author: string;
  article: string;
  downloaded: boolean;
  title: string;
  bookAuthor: string;
  date: string;
  language: string;
  genre: string;
  imageUrl: string;
  bookUrl: string;
  description: string;
  hasEpub: boolean;
  hasPdf: boolean;
};

export type QueueItem = {
  id: number;
  bookTitle: string;
  bookUrl: string;
  bookAuthor?: string;
  status: string;
  retryCount: number;
  errorMessage?: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
};
