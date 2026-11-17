export default function FavoritesPage({ activity, onRemove }) {
  return (
    <section className="page" aria-labelledby="favorites-title">
      <header className="page-head">
        <h1 id="favorites-title">Favoris</h1>
        <p>
          {activity.favorites.length === 0
            ? "Ajoute un livre avec l’étoile depuis les résultats de recherche."
            : `${activity.favorites.length} livre${activity.favorites.length > 1 ? "s" : ""} enregistré${activity.favorites.length > 1 ? "s" : ""}.`}
        </p>
      </header>

      {activity.favorites.length > 0 && (
        <ul className="activity-list">
          {activity.favorites.map((book) => (
            <li key={book.id}>
              <div>
                <a className="activity-title" href={`#/livre/${book.id}`}>
                  {book.title}
                </a>
                <small>{book.author}</small>
              </div>

              <div className="activity-buttons">
                <a className="btn btn--small" href={`#/livre/${book.id}`}>
                  Lire
                </a>
                <button
                  type="button"
                  className="btn btn--small btn--ghost"
                  onClick={() => onRemove(book)}
                  aria-label={`Retirer ${book.title} des favoris`}
                >
                  Retirer
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
