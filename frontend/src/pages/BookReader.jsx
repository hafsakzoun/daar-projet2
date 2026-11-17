import { useEffect, useState } from "react";
import StarIcon from "../components/StarIcon.jsx";

const CHUNK = 40000;
const number = new Intl.NumberFormat("fr-FR");

export default function BookReader({ bookId, favorites, onToggleFavorite }) {
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    setError("");

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
    setOffset(nextOffset);
    window.scrollTo(0, 0);
  }

  const isFavorite = favorites.some((favorite) => favorite.id === bookId);
  const page = Math.floor(offset / CHUNK) + 1;
  const pages = data ? Math.max(1, Math.ceil(data.total / CHUNK)) : null;

  const pager = data && pages > 1 && (
    <nav className="pagination" aria-label="Pages du livre">
      <button
        type="button"
        className="btn"
        disabled={offset === 0}
        onClick={() => goTo(Math.max(0, offset - CHUNK))}
      >
        Précédent
      </button>
      <span>
        Partie {page} sur {pages}
      </span>
      <button
        type="button"
        className="btn"
        disabled={offset + CHUNK >= data.total}
        onClick={() => goTo(offset + CHUNK)}
      >
        Suivant
      </button>
    </nav>
  );

  return (
    <article className="page reader" aria-labelledby="reader-title">
      <a className="back-link" href="#/">
        ← Retour à la recherche
      </a>

      {error && <p role="alert">{error}</p>}
      {!data && !error && <p role="status">Chargement du texte…</p>}

      {data && (
        <>
          <header className="page-head page-head--split">
            <div>
              <h1 id="reader-title">{data.title}</h1>
              <p>
                {data.author} · {number.format(data.total)} caractères
              </p>
            </div>

            {/* Visible seulement quand on est connecté. */}
            {onToggleFavorite && (
              <button
                type="button"
                className="btn favorite-button"
                aria-pressed={isFavorite}
                onClick={() => onToggleFavorite(data)}
              >
                <StarIcon filled={isFavorite} />
                {isFavorite ? "Dans tes favoris" : "Ajouter aux favoris"}
              </button>
            )}
          </header>
          {/* Les fichiers Gutenberg commencent souvent par des lignes vides. */}
          <pre className="reader-text">
            {offset === 0 ? data.text.replace(/^\s+/, "") : data.text}
          </pre>
          {pager}
        </>
      )}
    </article>
  );
}
