import { useEffect, useMemo, useRef, useState } from 'react';
import { Moon, Search, Sun, Heart, Menu, Sparkles, TrendingUp, X } from 'lucide-react';
import { useTheme } from './hooks/useTheme';
import { api, type Track } from './services/api';
import AudioPlayer from './components/AudioPlayer';

const genres = ['all', 'rock', 'jazz', 'electronic', 'chill', 'classical', 'hip hop'];

function formatTime(seconds: number) {
  if (!Number.isFinite(seconds) || seconds <= 0) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export default function App() {
  const { theme, toggleTheme } = useTheme();
  const [tracks, setTracks] = useState<Track[]>([]);
  const [search, setSearch] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [trendingSearches, setTrendingSearches] = useState<Array<{ term: string; count: number; trend: 'up' | 'down' | 'steady' }>>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [activeGenre, setActiveGenre] = useState('all');
  const [currentTrack, setCurrentTrack] = useState<Track | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [volume, setVolume] = useState(0.8);
  const [liked, setLiked] = useState<Array<string | number>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const audioRef = useRef<HTMLAudioElement>(null);
  const searchCardRef = useRef<HTMLDivElement>(null);
  const searchTimeoutRef = useRef<ReturnType<typeof window.setTimeout> | null>(null);
  const suggestionTimeoutRef = useRef<ReturnType<typeof window.setTimeout> | null>(null);

  const currentIndex = useMemo(() => {
    if (!currentTrack) return -1;
    return tracks.findIndex((track) => track.id === currentTrack.id);
  }, [currentTrack, tracks]);

  useEffect(() => {
    const load = async () => {
      try {
        setError('');
        setLoading(true);
        const data = await api.trending();
        setTracks(data.tracks);
        setCurrentTrack(data.tracks[0] ?? null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load music');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  useEffect(() => {
    const loadTrendingSearches = async () => {
      try {
        const response = await api.trendingSearches();
        setTrendingSearches(response.trending);
      } catch {
        setTrendingSearches([]);
      }
    };
    loadTrendingSearches();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchCardRef.current && !searchCardRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.volume = volume;
    if (isPlaying) {
      void audio.play().catch(() => setIsPlaying(false));
    } else {
      audio.pause();
    }
  }, [isPlaying, volume, currentTrack]);

  const selectTracks = async (loader: () => Promise<{ tracks: Track[] }>) => {
    try {
      setError('');
      setLoading(true);
      const data = await loader();
      setTracks(data.tracks);
      setCurrentTrack(data.tracks[0] ?? null);
      setIsPlaying(false);
      setProgress(0);
      setElapsed(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tracks');
    } finally {
      setLoading(false);
    }
  };

  const performSearch = async (query: string) => {
    const trimmed = query.trim();
    if (!trimmed) {
      await selectTracks(() => api.trending());
      return;
    }

    await selectTracks(() => api.search(trimmed));
    setShowSuggestions(false);
  };

  const fetchSuggestions = async (query: string) => {
    if (query.trim().length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    setIsLoadingSuggestions(true);
    try {
      const response = await api.suggestions(query);
      setSuggestions(response.suggestions);
      setShowSuggestions(response.suggestions.length > 0);
    } catch {
      setSuggestions([]);
      setShowSuggestions(false);
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  const handleSearchChange = (value: string) => {
    setSearch(value);

    if (searchTimeoutRef.current) window.clearTimeout(searchTimeoutRef.current);
    if (suggestionTimeoutRef.current) window.clearTimeout(suggestionTimeoutRef.current);

    searchTimeoutRef.current = window.setTimeout(() => {
      void performSearch(value);
    }, 300);

    suggestionTimeoutRef.current = window.setTimeout(() => {
      void fetchSuggestions(value);
    }, 100);
  };

  const selectSuggestion = (value: string) => {
    setSearch(value);
    setShowSuggestions(false);
    void performSearch(value);
  };

  const clearSearch = () => {
    setSearch('');
    setSuggestions([]);
    setShowSuggestions(false);
    void performSearch('');
  };

  const loadGenre = async (genre: string) => {
    setActiveGenre(genre);
    if (genre === 'all') {
      await selectTracks(() => api.trending());
      return;
    }
    await selectTracks(() => api.genre(genre));
  };

  const playTrack = (track: Track) => {
    setCurrentTrack(track);
    setIsPlaying(true);
    setProgress(0);
    setElapsed(0);
  };

  const toggleLiked = (id: string | number) => {
    setLiked((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  };

  const prevTrack = () => {
    if (currentIndex <= 0) return;
    playTrack(tracks[currentIndex - 1]);
  };

  const nextTrack = () => {
    if (currentIndex < 0 || currentIndex >= tracks.length - 1) return;
    playTrack(tracks[currentIndex + 1]);
  };

  return (
    <div className="app" data-theme={theme}>
      <header className="topbar">
        <div>
          <div className="brand">SONEXA</div>
          <div className="tagline">Feel the music, live the vibe.</div>
        </div>
        <div className="topbar-actions">
          <button className="icon-button" onClick={toggleTheme} aria-label="Toggle theme">
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button className="icon-button mobile-only" aria-label="Menu">
            <Menu size={18} />
          </button>
        </div>
      </header>

      <main className="content">
        <section className="hero">
          <div>
            <p className="eyebrow"><Sparkles size={14} /> Ashwin's powered</p>
            <h1>Unlimited free music with a polished dark/light experience.</h1>
            <p className="hero-copy">Search any genre, play tracks instantly, and switch themes with one click.</p>
          </div>
          <div className="search-card" ref={searchCardRef}>
            <div className="search-row">
              <Search size={18} />
              <input
                value={search}
                onChange={(e) => handleSearchChange(e.target.value)}
                onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                onKeyDown={(e) => e.key === 'Enter' && void performSearch(search)}
                placeholder="Search songs, artists, or moods"
              />
              {search ? (
                <button onClick={clearSearch} aria-label="Clear search" className="clear-search-button">
                  <X size={16} />
                </button>
              ) : null}
              <button onClick={() => void performSearch(search)}>Search</button>
            </div>
            {showSuggestions ? (
              <div className="suggestions-dropdown">
                {isLoadingSuggestions ? <div className="suggestions-loading">Loading...</div> : null}
                {suggestions.map((suggestion, index) => (
                  <button key={`${suggestion}-${index}`} className="suggestion-item" onClick={() => selectSuggestion(suggestion)}>
                    <Search size={16} />
                    <span>{suggestion}</span>
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </section>

        <section className="trending-searches">
          <div className="trending-searches-header">
            <TrendingUp size={18} />
            <h2>Trending Searches</h2>
          </div>
          <div className="trending-searches-list">
            {trendingSearches.slice(0, 8).map((item) => (
              <button key={item.term} className="trending-search-chip" onClick={() => selectSuggestion(item.term)}>
                <TrendingUp size={14} />
                {item.term}
              </button>
            ))}
          </div>
        </section>

        <section className="chips">
          {genres.map((genre) => (
            <button
              key={genre}
              className={genre === activeGenre ? 'chip active' : 'chip'}
              onClick={() => void loadGenre(genre)}
            >
              {genre}
            </button>
          ))}
        </section>

        {error ? <div className="state error">{error}</div> : null}
        {loading ? <div className="state">Loading music...</div> : null}

        <section className="track-grid">
          {tracks.map((track) => (
            <article key={track.id} className="track-card" onClick={() => playTrack(track)}>
              <img src={track.image_url} alt={track.title} />
              <div className="track-meta">
                <h3>{track.title}</h3>
                <p>{track.artist}</p>
                <p>{track.source ? track.source.toUpperCase() : ''}</p>
              </div>
              <div className="track-footer">
                <span>{formatTime(track.duration)}</span>
                <button
                  className="icon-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleLiked(track.id);
                  }}
                  aria-label="Like track"
                >
                  <Heart size={16} fill={liked.includes(track.id) ? 'currentColor' : 'none'} />
                </button>
              </div>
            </article>
          ))}
        </section>
      </main>

      <AudioPlayer
        track={currentTrack}
        isPlaying={isPlaying}
        progress={progress}
        volume={volume}
        currentTime={formatTime(elapsed)}
        duration={currentTrack ? formatTime(currentTrack.duration) : '0:00'}
        onTogglePlay={() => setIsPlaying((current) => !current)}
        onSeek={(value) => {
          const audio = audioRef.current;
          if (!audio || !Number.isFinite(audio.duration) || audio.duration <= 0) return;
          audio.currentTime = (value / 100) * audio.duration;
          setProgress(value);
          setElapsed(audio.currentTime);
        }}
        onVolume={setVolume}
        onPrev={prevTrack}
        onNext={nextTrack}
        onEnded={() => setIsPlaying(false)}
        onTimeUpdate={(currentTime, duration, value) => {
          setElapsed(currentTime);
          setProgress(value);
          if (Number.isFinite(duration) && duration > 0 && audioRef.current) {
            audioRef.current.volume = volume;
          }
        }}
        audioRef={audioRef}
      />
    </div>
  );
}
