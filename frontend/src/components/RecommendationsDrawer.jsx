import { useEffect, useRef, useState } from "react";
import BookRecommendations from "./BookRecommendations.jsx";

const number = new Intl.NumberFormat("fr-FR");

function RecommendedBookDetails({ book }) {
  const [details, setDetails] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadDetails() {
      try {
        const response = await fetch(`/api/v1/books/${book.id}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error("Impossible de charger la fiche du livre.");
        }

        const data = await response.json();
        if (!controller.signal.aborted) setDetails(data);
      } catch {
        if (!controller.signal.aborted) {
          setError("Impossible de charger la fiche du livre.");
        }
      }
    }

    loadDetails();
    return () => controller.abort();
  }, [book.id]);

  return (
    <section className="book-details" aria-label="Fiche du livre">
      <p className="book-details__author">{book.author}</p>
      {error && <p role="alert">{error}</p>}
      {!details && !error && <p role="status">Chargement de la fiche…</p>}

      {details && (
        <dl className="book-details__facts">
          <div>
            <dt>Langue</dt>
            <dd>{details.language}</dd>
          </div>
          <div>
            <dt>Longueur</dt>
            <dd>{number.format(details.word_count)} mots</dd>
          </div>
        </dl>
      )}

      <a className="btn btn--primary btn--block book-details__read" href={`#/livre/${book.id}`}>
        Lire le livre
      </a>
    </section>
  );
}

export default function RecommendationsDrawer({ book, onClose }) {
  const dialogRef = useRef(null);
  const [visitedBooks, setVisitedBooks] = useState([]);
  const currentBook = visitedBooks.at(-1) ?? book;
  const isViewingDetails = visitedBooks.length > 0;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog.open) dialog.showModal();
  }, []);

  return (
    <dialog
      ref={dialogRef}
      className="recommendations-drawer"
      aria-labelledby="recommendations-heading"
      onClose={onClose}
    >
      <header className="recommendations-drawer__header">
        <div>
          <h2 id="recommendations-heading">
            {isViewingDetails ? currentBook.title : "Livres similaires"}
          </h2>

          {!isViewingDetails && (
            <p className="recommendations-source">
              À partir de <cite>{book.title}</cite>
            </p>
          )}
        </div>

        <form method="dialog">
          <button
            type="submit"
            className="recommendations-drawer__close"
            aria-label="Fermer les recommandations"
          >
            ×
          </button>
        </form>
      </header>
      <div className="recommendations-drawer__body">
        {isViewingDetails && (
          <>
            <button
              type="button"
              className="recommendations-back"
              onClick={() => setVisitedBooks((books) => books.slice(0, -1))}
            >
              ← Retour
            </button>
            <RecommendedBookDetails key={currentBook.id} book={currentBook} />
          </>
        )}

        <BookRecommendations
          key={currentBook.id}
          bookId={currentBook.id}
          onSelectBook={(nextBook) => {
            setVisitedBooks((books) => [...books, nextBook]);
          }}
        />
      </div>
    </dialog>
  );
}
