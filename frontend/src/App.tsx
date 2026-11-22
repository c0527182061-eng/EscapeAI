
import { useEffect, useRef, useState } from "react";
import "./App.css";
import { ActionMusic } from "./actionMusic";
type Game = {
  session_id: string;
  finished: boolean;
  room_number: number;
  room_name: string;
  puzzle: string;
  difficulty: number;
  total_puzzles: number;
  completed_puzzles: number;
  score: number;
  attempts: number;
  hints_used: number;
  feedback: string;
  hint: string;
  last_answer_correct: boolean;
};

const API = "http://localhost:8000/api/game";

const rooms = [
  { icon: "⚗", title: "המעבדה הנטושה", color: "#4dffb5" },
  { icon: "◈", title: "הכספת הסודית", color: "#ffcc73" },
  { icon: "⌘", title: "הארכיון המוצפן", color: "#b8a0ff" },
  { icon: "⚡", title: "חדר הבקרה", color: "#69d9ff" },
  { icon: "⛧", title: "דלת היציאה", color: "#ff6179" },
];

function App() {
  const [game, setGame] = useState<Game | null>(null);
  const [answer, setAnswer] = useState("");
  const [count, setCount] = useState(10);
  const [seconds, setSeconds] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [flash, setFlash] = useState(false);
  const [shake, setShake] = useState(false);
  const [muted, setMuted] = useState(false);
  const [showIntro, setShowIntro] = useState(false);
  const audioRef = useRef<AudioContext | null>(null);
const musicRef = useRef<ActionMusic | null>(null);
useEffect(() => {
  return () => musicRef.current?.dispose();
}, []);

useEffect(() => {
  if (muted || game?.finished) {
    musicRef.current?.stop();
  } else if (game) {
    musicRef.current?.start();
  }
}, [muted, game?.finished, game?.session_id]);

  const sound = (
    frequency = 180,
    duration = 0.2,
    type: OscillatorType = "sine"
  ) => {
    if (muted) return;
    try {
      const ctx = audioRef.current ?? new AudioContext();
      audioRef.current = ctx;
      if (ctx.state === "suspended") void ctx.resume();

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(frequency, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(
        Math.max(35, frequency / 2),
        ctx.currentTime + duration
      );
      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(
        0.001,
        ctx.currentTime + duration
      );
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + duration);
    } catch {
      // Audio may be unavailable
    }
  };

  useEffect(() => {
    if (!game || game.finished) return;
    const timer = window.setInterval(() => {
      setSeconds(s => s + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [game?.session_id, game?.finished]);

  const request = async (path: string, body: object): Promise<Game> => {
    const response = await fetch(`${API}/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => null);
      throw new Error(data?.detail || "החיבור לשרת נכשל");
    }
    return response.json();
  };

  const start = async () => {
    setBusy(true);
    setError("");
    
    sound(90, 0.8, "sawtooth");
    if (!muted) {
  musicRef.current ??= new ActionMusic();
  musicRef.current.start();
}
    try {
      const data = await request("start", { total_puzzles: count });
      setGame(data);
      setSeconds(0);
      setMessage("");
      setAnswer("");
      setShowIntro(true);
      window.setTimeout(() => setShowIntro(false), 2500);
    } catch (e) {
      setError(e instanceof Error ? e.message : "שגיאה");
    } finally {
      setBusy(false);
    }
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!game || !answer.trim() || busy) return;
    setBusy(true);
    setError("");
    setMessage("");
    sound(380, 0.12, "square");

    try {
      const result = await request("answer", {
        session_id: game.session_id,
        answer,
      });

      setGame(result);
      setAnswer("");

      if (result.last_answer_correct) {
        sound(700, 0.45);
        setFlash(true);
        window.setTimeout(() => setFlash(false), 500);
        setMessage("✓ המנעול נפרץ. הגישה אושרה.");
      } else {
        sound(75, 0.55, "sawtooth");
        setShake(true);
        window.setTimeout(() => setShake(false), 550);
        setMessage(result.hint || result.feedback || "גישה נדחתה.");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "שגיאה");
    } finally {
      setBusy(false);
    }
  };

  const reset = () => {
    setGame(null);
    setMessage("");
    setError("");
    musicRef.current?.stop();
    setSeconds(0);
    setAnswer("");
  };
useEffect(() => {
  if (!game) return;

  window.scrollTo({
    top: 0,
    behavior: "smooth"
  });
}, [game?.completed_puzzles, game?.room_number]);
  const time = `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
  const room = rooms[(game?.room_number ?? 1) - 1] || rooms[0];
  const progress = game
    ? (game.completed_puzzles / game.total_puzzles) * 100
    : 0;

  return (
    <div className={`app ${shake ? "shake" : ""}`}>
      <div className="noise" />
      <div className="scanlines" />
      <div className="vignette" />
      {flash && <div className="flash" />}
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <header className="topbar">
        <div className="brand"><span>◈</span> ESCAPE<span>AI</span></div>
        <div className="top-status">
          <span className="live-dot" />
          SYSTEM {game ? "ACTIVE" : "STANDBY"}
        </div>
        <button className="sound-btn" onClick={() => setMuted(!muted)}>
          {muted ? "🔇 SOUND OFF" : "♫ SOUND ON"}
        </button>
      </header>

      {!game ? (
        <main className="start-screen">
          <div className="warning">⚠ CLASSIFIED // ACCESS RESTRICTED ⚠</div>
          <div className="hero-symbol">⛧</div>
          <p className="eyebrow">AN AI-POWERED ESCAPE EXPERIENCE</p>
          <h1 className="glitch" data-text="ESCAPE AI">ESCAPE AI</h1>
          <p className="hero-hebrew">חמישה חדרים. אינספור סודות. דרך אחת החוצה.</p>
          <p className="hero-description">
            הדלת ננעלה מאחוריך. המערכת התעוררה.
            <br />
            כל תשובה מקרבת אותך לחופש. כל טעות עולה בזמן.
          </p>

          <section className="start-panel">
            <div className="panel-label">INITIALIZE ESCAPE PROTOCOL</div>
            <label htmlFor="count">כמה חידות תעז להתמודד איתן?</label>
            <div className="count-picker">
              <button onClick={() => setCount(c => Math.max(5, c - 1))}>−</button>
              <strong>{count}</strong>
              <button onClick={() => setCount(c => Math.min(15, c + 1))}>+</button>
            </div>
            <div className="count-caption">MIN 05 — MAX 15</div>
            <button className="primary-btn" onClick={start} disabled={busy}>
              {busy ? "מתחבר למערכת..." : "▶ היכנס אם אתה מעז"}
            </button>
          </section>
          {error && <p className="error">{error}</p>}
          <p className="bottom-warning">THERE IS NO TURNING BACK</p>
        </main>
      ) : game.finished ? (
        <main className="end-screen">
          <div className="victory-icon">◈</div>
          <p className="eyebrow">ESCAPE PROTOCOL COMPLETE</p>
          <h1>הצלחת לברוח!</h1>
          <p>כל המנעולים נפתחו. המערכת הובסה.</p>
          <div className="end-stats">
            <div><strong>{game.score}</strong><span>נקודות</span></div>
            <div><strong>{time}</strong><span>זמן</span></div>
            <div><strong>{game.completed_puzzles}</strong><span>חידות</span></div>
          </div>
          <button className="primary-btn" onClick={reset}>↻ משחק חדש</button>
        </main>
      ) : (
        <main className="game-layout" style={{ "--room-color": room.color } as React.CSSProperties}>
          <aside className="sidebar">
            <div className="sidebar-title">FACILITY MAP</div>
            {rooms.map((r, i) => (
              <div key={i} className={`room-item ${game.room_number === i + 1 ? "active" : ""}`}>
                <span className="room-icon">{r.icon}</span>
                <div>
                  <small>SECTOR 0{i + 1}</small>
                  <strong>{r.title}</strong>
                </div>
                {game.room_number === i + 1 && <span className="current-marker">●</span>}
              </div>
            ))}
            <div className="sidebar-footer">⚠ AI SURVEILLANCE ACTIVE</div>
          </aside>

          <section className="game-content">
            <div className="hud">
              <div className="hud-box"><small>זמן שחלף</small><strong>{time}</strong></div>
              <div className="hud-box"><small>ניקוד</small><strong>{game.score}</strong></div>
              <div className="hud-box"><small>רמת קושי</small><strong>{"◆".repeat(game.difficulty)}</strong></div>
              <div className="hud-box"><small>ניסיונות</small><strong>{game.attempts}</strong></div>
            </div>

            <div className="progress-head">
              <span>ESCAPE PROGRESS</span>
              <span>{game.completed_puzzles} / {game.total_puzzles}</span>
            </div>
            <div className="progress-track">
              <div style={{ width: `${progress}%` }} />
            </div>

            <div className="room-stage">
              <div className="room-aura" />
              <div className="room-emblem">{room.icon}</div>
              <div className="sector-label">SECTOR 0{game.room_number} // SECURITY LEVEL {game.difficulty}</div>
              <h2>{game.room_name}</h2>
              <p>מערכת האבטחה זיהתה נוכחות לא מורשית.</p>
              <div className="lock-row">
                <span>⌁</span><span>◈</span><span>⌁</span>
              </div>
            </div>

            <div className="puzzle-card">
              <div className="puzzle-header">
                <span><span className="live-dot" /> ENCRYPTED CHALLENGE</span>
                <span>PUZZLE {String(game.completed_puzzles + 1).padStart(2, "0")}</span>
              </div>
              <div className="puzzle-body">
                <div className="puzzle-icon">⌬</div>
                <h3>פענח את הקוד</h3>
                <p className="puzzle-text">{game.puzzle}</p>
              </div>

              <form onSubmit={submit}>
                <label htmlFor="answer">ENTER ACCESS CODE</label>
                <div className="answer-row">
                  <input
                    id="answer"
                    dir="auto"
                    value={answer}
                    onChange={e => setAnswer(e.target.value)}
                    placeholder="הקלד את התשובה..."
                    autoComplete="off"
                    disabled={busy}
                  />
                  <button disabled={busy || !answer.trim()}>
                    {busy ? "בודק..." : "אמת קוד ←"}
                  </button>
                </div>
              </form>

              {(message || error) && (
                <div className={`feedback ${error ? "bad" : game.last_answer_correct ? "good" : "bad"}`}>
                  {error || message}
                </div>
              )}

              <div className="puzzle-footer">
                <span>◉ AI VALIDATION ONLINE</span>
                <span>רמזים שנוצלו: {game.hints_used}</span>
              </div>
            </div>
          </section>
        </main>
      )}

      {showIntro && game && !game.finished && (
        <div className="intro-overlay">
          <div className="intro-icon">⚠</div>
          <div>ACCESS GRANTED</div>
          <h2>{game.room_name}</h2>
          <p>THE SYSTEM IS WATCHING YOU</p>
        </div>
      )}
    </div>
  );
}

export default App;
