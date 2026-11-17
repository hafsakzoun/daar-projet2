import { useEffect, useState } from "react";
import BookRecommendations from "./BookRecommendations.jsx";
import RecommendationsDrawer from "./RecommendationsDrawer.jsx";
import StarIcon from "./StarIcon.jsx";

const PAGE_SIZE = 20;
const number = new Intl.NumberFormat("fr-FR");

export default function Results({
  query,
  mode,
  offset,
  onPageChange,
  favorites,
  onToggleFavorite,
  sort,
  onSortChange,
}) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [selectedBook, setSelectedBook] = useState(null);

  useEffect(() => {
    // Le parent remonte ce composant (prop key) à chaque nouvelle
    // recherche ou page : l'état part donc toujours de zéro.
    const controller = new AbortController();
    const params = new URLSearchParams({ limit: PAGE_SIZE, offset });
    const endpoint = query
      ? mode === "regex"
        ? "search/regex"
        : "search"
      : "books";

    if (query) {
      params.set("q", query);
      params.set("sort", sort);
    }

    async function loadResults() {
      try {
        const response = await fetch(`/api/v1/${endpoint}?${params}`, {
          signal: controller.signal,
        });
        const body = await response.json();

        if (!response.ok) {
          throw new Error(
            typeof body?.detail === "string"
              ? body.detail
              : "La requête a échoué.",
          );
        }

        if (!Array.isArray(body?.results)) {
          throw new Error("Réponse inattendue du serveur.");
        }

        if (!controller.signal.aborted) setData(body);
      } catch (err) {
        if (controller.signal.aborted) return;

        const message =
          err instanceof SyntaxError || err instanceof TypeError
            ? "Le serveur est indisponible. Réessaie dans un instant."
            : err.message;

        setError(message);
      }
    }

    loadResults();
    return () => controller.abort();
  }, [query, mode, offset, sort]);

  return (
    <section className="results" aria-labelledby="results-title">
      <div className="results-head">
        <h2 id="results-title">
          {query ? "Résultats de recherche" : "Catalogue"}
        </h2>
        {query && (
          <label className="results-sort">
            Trier par
            <select value={sort} onChange={(e) => onSortChange(e.target.value)}>
              <option value="occurrences">Fréquence normalisée</option>
              <option value="pagerank">PageRank</option>
            </select>
          </label>
        )}
      </div>
      {error && <p role="alert">{error}</p>}
      {!data && !error && (
        <>
          <p role="status" className="sr-only">
            Chargement…
          </p>
          <ul className="book-list" aria-hidden="true">
            {Array.from({ length: 10 }, (_, index) => (
              <li key={index} className="book-card">
                <div className="skeleton skeleton--cover" />
                <div className="skeleton skeleton--line" />
                <div className="skeleton skeleton--line skeleton--short" />
              </li>
            ))}
          </ul>
        </>
      )}

      {data && (
        <>
          <p role="status">
            {data.total === 0
              ? query
                ? "Aucun livre trouvé."
                : "Le catalogue est vide."
              : `${number.format(data.total)} ${data.total === 1 ? "livre" : "livres"}${query ? (sort === "pagerank" ? " · Tri PageRank" : " · Tri par fréquence normalisée") : ""}`}
          </p>

          {data.results.length > 0 && (
            <ul className="book-list">
              {data.results.map((book) => {
                const isFavorite = favorites.some(
                  (favorite) => favorite.id === book.id,
                );

                return (
                  <li key={book.id} className="book-card">
                    <div
                      className={`book-cover book-cover--${book.id % 5}`}
                      aria-hidden="true"
                    >
                      <span>{book.author}</span>
                      <strong>{book.title}</strong>
                      <em>N° {book.id}</em>
                    </div>

                    <div className="book-info">
                      <h3>{book.title}</h3>
                      <p>{book.author}</p>

                      {query && (
                        <>
                          <span className="score">
                            {number.format(book.score)} occurrences par million
                            de mots
                          </span>
                          {sort === "pagerank" &&
                            typeof book.pagerank === "number" && (
                              <span className="pagerank-score">
                                PageRank : {book.pagerank.toFixed(6)}
                              </span>
                            )}
                        </>
                      )}

                      <div className="book-actions">
                        {onToggleFavorite && (
                          <button
                            type="button"
                            className="icon-btn favorite-toggle"
                            aria-label={`Favori pour ${book.title}`}
                            aria-pressed={isFavorite}
                            onClick={() => onToggleFavorite(book)}
                          >
                            <StarIcon filled={isFavorite} />
                          </button>
                        )}

                        <a
                          className="btn btn--small"
                          href={`#/livre/${book.id}`}
                          aria-label={`Lire ${book.title}`}
                        >
                          Lire
                        </a>

                        <button
                          type="button"
                          className="btn btn--small btn--ghost similar-trigger"
                          aria-haspopup="dialog"
                          aria-label={`Livres similaires à ${book.title}`}
                          onClick={() => setSelectedBook(book)}
                        >
                          Similaires
                        </button>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}

          {query && offset === 0 && data.results.length > 0 && (
            <section
              className="search-suggestions"
              aria-label="Suggestions après recherche"
            >
              <h3>Suggestions pour cette recherche</h3>
              <p>Livres similaires aux deux premiers résultats.</p>
              <div className="search-suggestions__groups">
                {data.results.slice(0, 2).map((book) => (
                  <div key={book.id} className="search-suggestions__group">
                    <p>
                      À partir de <strong>{book.title}</strong>
                    </p>
                    <BookRecommendations
                      bookId={book.id}
                      onSelectBook={setSelectedBook}
                    />
                  </div>
                ))}
              </div>
            </section>
          )}

          {data.total > data.limit && (
            <nav className="pagination" aria-label="Pagination des livres">
              <button
                type="button"
                className="btn"
                disabled={offset === 0}
                onClick={() => onPageChange(offset - data.limit)}
              >
                Précédent
              </button>

              <span>
                Page {Math.floor(offset / data.limit) + 1} sur{" "}
                {Math.ceil(data.total / data.limit)}
              </span>

              <button
                type="button"
                className="btn"
                disabled={offset + data.limit >= data.total}
                onClick={() => onPageChange(offset + data.limit)}
              >
                Suivant
              </button>
            </nav>
          )}
        </>
      )}
      {selectedBook && (
        <RecommendationsDrawer
          key={selectedBook.id}
          book={selectedBook}
          onClose={() => setSelectedBook(null)}
        />
      )}
    </section>
  );
}
