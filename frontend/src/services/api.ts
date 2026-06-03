const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export type Track = {
  id: string | number;
  title: string;
  artist: string;
  album: string;
  duration: number;
  stream_url: string;
  image_url: string;
  genre: string;
  source: 'jamendo' | 'youtube' | string;
  external_url?: string;
};

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  search: (q: string) => request<{ tracks: Track[] }>(`/api/search?q=${encodeURIComponent(q)}`),
  trending: () => request<{ tracks: Track[] }>('/api/trending'),
  genre: (genre: string) => request<{ tracks: Track[] }>(`/api/genres/${encodeURIComponent(genre)}`),
};
