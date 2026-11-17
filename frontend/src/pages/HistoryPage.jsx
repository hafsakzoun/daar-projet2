const historyDate = new Intl.DateTimeFormat("fr-FR", {
  dateStyle: "medium",
  timeStyle: "short",
});

export default function HistoryPage({ activity, onReplay, onClear }) {
  const { history } = activity;

  return (
    <section className="page" aria-labelledby="history-title">
      <header className="page-head page-head--split">
        <div>
          <h1 id="history-title">Historique</h1>
          <p>
            {history.length === 0
              ? "Tes recherches apparaîtront ici avec leur date et leur heure."
              : "Tes 30 dernières recherches."}
          </p>
        </div>

        {history.length > 0 && (
          <button type="button" className="btn btn--small" onClick={onClear}>
            Effacer l’historique
          </button>
        )}
      </header>

      {history.length > 0 && (
        <ul className="activity-list">
          {history.map((entry) => (
            <li key={entry.id}>
              <div>
                <strong className="activity-title">{entry.query}</strong>
                <small>
                  {entry.mode === "regex" ? "Regex" : "Mot-clé"} ·{" "}
                  <time dateTime={entry.date}>
                    {historyDate.format(new Date(entry.date))}
                  </time>
                </small>
              </div>

              <button
                type="button"
                className="btn btn--small"
                aria-label={`Relancer la recherche ${entry.query}`}
                onClick={() => onReplay(entry)}
              >
                Relancer
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
