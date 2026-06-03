import { Pause, Play, SkipBack, SkipForward, Volume2 } from 'lucide-react';
import type { Track } from '../services/api';
import type { RefObject } from 'react';

type Props = {
  track: Track | null;
  isPlaying: boolean;
  progress: number;
  volume: number;
  currentTime: string;
  duration: string;
  onTogglePlay: () => void;
  onSeek: (value: number) => void;
  onVolume: (value: number) => void;
  onPrev: () => void;
  onNext: () => void;
  onEnded: () => void;
  onTimeUpdate: (currentTime: number, duration: number, progress: number) => void;
  audioRef: RefObject<HTMLAudioElement>;
};

export default function AudioPlayer({
  track,
  isPlaying,
  progress,
  volume,
  currentTime,
  duration,
  onTogglePlay,
  onSeek,
  onVolume,
  onPrev,
  onNext,
  onEnded,
  onTimeUpdate,
  audioRef,
}: Props) {
  if (!track) return null;

  const isYoutube = track.source === 'youtube';

  return (
    <div className="player-shell">
      {!isYoutube ? (
        <audio
          ref={audioRef}
          src={track.stream_url}
          onEnded={onEnded}
          onTimeUpdate={() => {
            const audio = audioRef.current;
            if (!audio || !Number.isFinite(audio.duration) || audio.duration <= 0) return;
            onTimeUpdate(audio.currentTime, audio.duration, (audio.currentTime / audio.duration) * 100);
          }}
        />
      ) : null}
      <div className="player-track">
        <img src={track.image_url} alt={track.title} />
        <div>
          <strong>{track.title}</strong>
          <span>{track.artist}</span>
          <small className="track-source">{track.source?.toUpperCase?.() ?? 'UNKNOWN'}</small>
        </div>
      </div>
      {isYoutube ? (
        <div className="youtube-player">
          {isPlaying ? (
            <iframe
              title={track.title}
              src={track.stream_url}
              allow="autoplay; encrypted-media"
              referrerPolicy="strict-origin-when-cross-origin"
            />
          ) : (
            <button className="play-button youtube-trigger" onClick={onTogglePlay}>
              <Play size={18} />
              Play YouTube
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="player-controls">
            <button onClick={onPrev} aria-label="Previous track"><SkipBack size={18} /></button>
            <button onClick={onTogglePlay} className="play-button" aria-label={isPlaying ? 'Pause' : 'Play'}>
              {isPlaying ? <Pause size={18} /> : <Play size={18} />}
            </button>
            <button onClick={onNext} aria-label="Next track"><SkipForward size={18} /></button>
          </div>
          <div className="player-progress">
            <span>{currentTime}</span>
            <input type="range" min={0} max={100} value={progress} onChange={(e) => onSeek(Number(e.target.value))} />
            <span>{duration}</span>
          </div>
          <div className="player-volume">
            <Volume2 size={16} />
            <input type="range" min={0} max={1} step={0.01} value={volume} onChange={(e) => onVolume(Number(e.target.value))} />
          </div>
        </>
      )}
    </div>
  );
}
