import { useEffect, useState } from "react";
import StarIcon from "../components/StarIcon.jsx";
import NeighborGraph from "../components/NeighborGraph.jsx";

const CHUNK = 12000;
const PREFERENCES_KEY = "lisiere-reader-preferences";

function initialPreferences() {
  try {
    const saved = JSON.parse(localStorage.getItem(PREFERENCES_KEY));
    return {
      size: [16, 18, 20, 22, 24, 26, 28].includes(saved?.size) ? saved.size : 20,
      theme: ["paper", "cream", "night"].includes(saved?.theme) ? saved.theme : "paper",
      original: saved?.original === true,
    };
  } catch {
    return { size: 20, theme: "paper", original: false };
  }
}

export default function BookReader({ bookId, favorites, onToggleFavorite }) {
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [preferences, setPreferences] = useState(initialPreferences);
  const [neighborsOpen, setNeighborsOpen] = useState(true);
  const [jump, setJump] = useState("1");

  useEffect(() => {
    try {
      localStorage.setItem(PREFERENCES_KEY, JSON.stringify(preferences));
    } catch {
      // La lecture reste disponible si le navigateur interdit le stockage.
    }
  }, [preferences]);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch(
          `/api/v1/books/${bookId}/text?offset=${offset}&limit=${CHUNK}`,
          { signal: controller.signal },
        );
        const body = await response.json();
        if (!response.ok) {
          throw new Error(body?.detail || "Impossible de charger le texte.");
        }
        if (!controller.signal.aborted) setData(body);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(
          err instanceof TypeError || err instanceof SyntaxError
            ? "Le serveur est indisponible."
            : err.message,
        );
      }
    }

    load();
    return () => controller.abort();
  }, [bookId, offset]);

  function goTo(nextOffset) {
    if (nextOffset === offset) {
      window.scrollTo(0, 0);
      return;
    }
    setJump(String(Math.floor(nextOffset / CHUNK) + 1));
    setNeighborsOpen(false);
    setData(null);
    setError("");
    setOffset(nextOffset);
    window.scrollTo(0, 0);
  }

  function resize(amount) {
    setPreferences((previous) => ({
      ...previous,
      size: Math.min(28, Math.max(16, previous.size + amount)),
    }));
  }

  const isFavorite = favorites.some((favorite) => favorite.id === bookId);
  const part = Math.floor(offset / CHUNK) + 1;
  const parts = data ? Math.max(1, Math.ceil(data.total / CHUNK)) : 1;

  function pager(label) {
    return (
      <nav className="reader-pagination" aria-label={label}>
        <button
          type="button"
          className="btn btn--small"
          disabled={offset === 0}
          onClick={() => goTo(Math.max(0, offset - CHUNK))}
        >
          ← Précédent
        </button>
        <span role="status">Partie {part} sur {parts}</span>
        <button
          type="button"
          className="btn btn--small"
          disabled={offset + CHUNK >= data.total}
          onClick={() => goTo(offset + CHUNK)}
        >
          Suivant →
        </button>
      </nav>
    );
  }

  return (
    <article className={`page reader reader--${preferences.theme}`} aria-labelledby={data ? "reader-title" : undefined}>
      <div className="reader-topline">
        <a className="back-link" href="#/">← Retour à la recherche</a>
        {data && onToggleFavorite && (
          <button
            type="button"
            className="btn btn--small favorite-button"
            aria-pressed={isFavorite}
            onClick={() => onToggleFavorite(data)}
          >
            <StarIcon filled={isFavorite} />
            {isFavorite ? "Dans tes favoris" : "Ajouter aux favoris"}
          </button>
        )}
      </div>

      {error && <p role="alert">{error}</p>}
      {!data && !error && <p role="status">Ouverture du livre…</p>}

      {data && (
        <>
          <div className="reader-toolbar" role="group" aria-label="Réglages de lecture">
            <div className="reader-size-control">
              <span>Taille du texte</span>
              <button type="button" disabled={preferences.size === 16} onClick={() => resize(-2)} aria-label="Réduire la taille du texte">A−</button>
              <output aria-live="polite" aria-label="Taille du texte en pixels">{preferences.size}</output>
              <button type="button" disabled={preferences.size === 28} onClick={() => resize(2)} aria-label="Augmenter la taille du texte">A+</button>
            </div>
            <label className="reader-theme-control">
              <span>Ambiance</span>
              <select value={preferences.theme} onChange={(event) => setPreferences((previous) => ({ ...previous, theme: event.target.value }))}>
                <option value="paper">Papier</option>
                <option value="cream">Crème</option>
                <option value="night">Nuit</option>
              </select>
            </label>
            <label className="reader-original-control">
              <input type="checkbox" checked={preferences.original} onChange={(event) => setPreferences((previous) => ({ ...previous, original: event.target.checked }))} />
              <span>Conserver les sauts de ligne du texte original</span>
            </label>
          </div>

          <details className="reader-neighbors" open={neighborsOpen} onToggle={(event) => setNeighborsOpen(event.currentTarget.open)}>
            <summary>Livres voisins · Graphe de Jaccard</summary>
            {neighborsOpen && <NeighborGraph book={data} />}
          </details>

          {pager("Navigation avant le texte")}
          <progress className="reader-progress" value={Math.min(offset + data.length, data.total)} max={data.total || 1} aria-label={`Partie ${part} sur ${parts}`} />

          <form className="reader-jump" onSubmit={(event) => {
            event.preventDefault();
            const target = Number(jump);
            if (Number.isInteger(target) && target >= 1 && target <= parts) goTo((target - 1) * CHUNK);
          }}>
            <label htmlFor="reader-part">Aller à la partie</label>
            <input id="reader-part" type="number" inputMode="numeric" min="1" max={parts} step="1" required value={jump} onChange={(event) => setJump(event.target.value)} />
            <span>sur {parts}</span>
            <button type="submit" className="btn btn--small">Aller</button>
          </form>

          <section className="reader-sheet" style={{ "--reader-font-size": `${preferences.size}px` }} aria-label="Texte du livre">
            <header className="reader-book-header">
              <p className="reader-eyebrow">Lisière · Le temps de lire</p>
              <h1 id="reader-title">{data.title}</h1>
              <p className="reader-author">{data.author}</p>
            </header>
            {preferences.original ? (
              <pre className="reader-text reader-text--original">{offset === 0 ? data.text.replace(/^\s+/, "") : data.text}</pre>
            ) : (
              <div className="reader-text">
                {data.text.trim().split(/\n[ \t]*\n+/).map((paragraph, index) => <p key={index}>{paragraph}</p>)}
              </div>
            )}
            <footer className="reader-sheet-footer">{part} / {parts}</footer>
          </section>

          {pager("Navigation après le texte")}
          {offset + CHUNK >= data.total && <p className="reader-end">Vous êtes arrivé à la fin du livre.</p>}
        </>
      )}
    </article>
  );
}
