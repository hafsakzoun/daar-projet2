import { useEffect, useState } from 'react'
import './App.css'

const PAGE_SIZE = 20
const number = new Intl.NumberFormat('fr-FR')

function Results({ query, mode, offset, onPageChange }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    const params = new URLSearchParams({ limit: PAGE_SIZE, offset })
    const endpoint = query
      ? (mode === 'regex' ? 'search/regex' : 'search')
      : 'books'

    if (query) params.set('q', query)

    async function loadResults() {
      try {
        const response = await fetch(`/api/v1/${endpoint}?${params}`, {
          signal: controller.signal,
        })
        const body = await response.json()

        if (!response.ok) {
          const message = typeof body.detail === 'string'
            ? body.detail
            : 'La requête a échoué.'
          throw new Error(message)
        }

        if (!Array.isArray(body.results)) {
          throw new Error('Réponse inattendue du serveur.')
        }

        if (!controller.signal.aborted) setData(body)
      } catch (err) {
        if (controller.signal.aborted) return

        const message = err instanceof SyntaxError || err instanceof TypeError
          ? 'Le serveur est indisponible. Réessaie dans un instant.'
          : err.message
        setError(message)
      }
    }

    loadResults()
    return () => controller.abort()
  }, [query, mode, offset])

  return (
    <section className="results" aria-labelledby="results-title">
      <h2 id="results-title">{query ? 'Résultats de recherche' : 'Catalogue'}</h2>

      {error && <p role="alert">{error}</p>}
      {!data && !error && <p role="status">Chargement…</p>}

      {data && (
        <>
          <p role="status">
            {data.total === 0
              ? (query ? 'Aucun livre trouvé.' : 'Le catalogue est vide.')
              : `${number.format(data.total)} ${data.total === 1 ? 'livre' : 'livres'}${query ? ' · Tri par occurrences' : ''}`}
          </p>

          {data.results.length > 0 && (
            <ul className="book-list">
              {data.results.map((book) => (
                <li key={book.id} className="book-card">
                  <div
                    className={`book-cover book-cover--${book.id % 5}`}
                    aria-hidden="true"
                  >
                    <span>{book.author}</span>
                    <strong>{book.title}</strong>
                  </div>

                  <div className="book-info">
                    <h3>{book.title}</h3>
                    <p>{book.author}</p>
                    {query && (
                      <span className="score">
                        {number.format(book.score)} {book.score === 1 ? 'occurrence' : 'occurrences'}
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}

          {data.total > data.limit && (
            <nav className="pagination" aria-label="Pagination des livres">
              <button
                type="button"
                disabled={offset === 0}
                onClick={() => onPageChange(offset - data.limit)}
              >
                Précédent
              </button>
              <span>
                Page {Math.floor(offset / data.limit) + 1} sur {Math.ceil(data.total / data.limit)}
              </span>
              <button
                type="button"
                disabled={offset + data.limit >= data.total}
                onClick={() => onPageChange(offset + data.limit)}
              >
                Suivant
              </button>
            </nav>
          )}
        </>
      )}
    </section>
  )
}

function App() {
  const [mode, setMode] = useState('keyword')
  const [request, setRequest] = useState({
    query: '',
    mode: 'keyword',
    offset: 0,
    id: 0,
  })

  function submit(event) {
    event.preventDefault()
    const query = new FormData(event.currentTarget).get('query').trim()

    setRequest((previous) => ({
      query,
      mode,
      offset: 0,
      id: previous.id + 1,
    }))
  }

  return (
    <main className="library">
      <header>
        <p className="eyebrow">DAAR · Sorbonne Université</p>
        <h1>Bibliothèque DAAR</h1>
        <p>Explore les livres du corpus par mot-clé ou expression régulière.</p>
      </header>

      <form className="search" onSubmit={submit}>
        <fieldset className="search-modes">
          <legend className="sr-only">Mode de recherche</legend>

          <label>
            <input
              type="radio"
              name="mode"
              value="keyword"
              checked={mode === 'keyword'}
              onChange={() => setMode('keyword')}
            />
            <span>Mot-clé</span>
          </label>

          <label>
            <input
              type="radio"
              name="mode"
              value="regex"
              checked={mode === 'regex'}
              onChange={() => setMode('regex')}
            />
            <span>Regex</span>
          </label>
        </fieldset>

        <div className="search-row">
          <label htmlFor="book-query" className="sr-only">
            {mode === 'regex' ? 'Expression régulière' : 'Mot-clé'}
          </label>

          <input
            id="book-query"
            name="query"
            type="search"
            placeholder={mode === 'regex' ? 'Ex. histor.*' : 'Rechercher dans les livres…'}
            maxLength={mode === 'regex' ? 100 : undefined}
            aria-describedby="search-hint"
          />

          <button type="submit">Rechercher</button>
        </div>

        <p id="search-hint" className="hint">
          {mode === 'regex'
            ? 'La regex est comparée à chaque terme entier de l’index.'
            : 'Essaie un mot du corpus, par exemple « history ».'}
        </p>
      </form>

      <Results
        key={`${request.id}:${request.offset}`}
        query={request.query}
        mode={request.mode}
        offset={request.offset}
        onPageChange={(offset) => setRequest((previous) => ({ ...previous, offset }))}
      />
    </main>
  )
}

export default App