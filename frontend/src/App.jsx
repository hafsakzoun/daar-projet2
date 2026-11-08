import { useEffect, useState } from 'react'
import AuthDialog from './AuthDialog.jsx'
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
  const [authMode, setAuthMode] = useState(null)
  const [user, setUser] = useState(null)
  const [checkingSession, setCheckingSession] = useState(true)
  const [loggingOut, setLoggingOut] = useState(false)
  const [accountError, setAccountError] = useState('')
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

  useEffect(() => {
  const controller = new AbortController()

  async function restoreSession() {
    try {
      const response = await fetch('/api/v1/auth/me', {
        signal: controller.signal,
      })

      if (response.status === 401) return
      if (!response.ok) throw new Error('Vérification impossible')

      const profile = await response.json()
      if (!controller.signal.aborted) setUser(profile)
    } catch {
      if (!controller.signal.aborted) {
        setAccountError('Impossible de vérifier ta session.')
      }
    } finally {
      if (!controller.signal.aborted) setCheckingSession(false)
    }
  }

  restoreSession()
  return () => controller.abort()
}, [])

function handleLogin(profile) {
  setUser(profile)
  setAuthMode(null)
  setAccountError('')
}

async function handleLogout() {
  setLoggingOut(true)
  setAccountError('')

  try {
    const response = await fetch('/api/v1/auth/logout', { method: 'POST' })
    if (!response.ok) throw new Error('Déconnexion impossible')

    setUser(null)
  } catch {
    setAccountError('Impossible de te déconnecter. Réessaie.')
  } finally {
    setLoggingOut(false)
  }
}

  return (
    <main className="library">
      <div className="account-actions" role="group" aria-label="Compte">
        {checkingSession ? (
          <span role="status">Vérification de la session…</span>
        ) : user ? (
          <>
            <span className="account-welcome" role="status">
              Bienvenue, {user.first_name} !
            </span>

            <button type="button" onClick={handleLogout} disabled={loggingOut}>
              {loggingOut ? 'Déconnexion…' : 'Se déconnecter'}
            </button>
          </>
        ) : (
          <>
            <button type="button" onClick={() => setAuthMode('login')}>
              Se connecter
            </button>

            <button type="button" onClick={() => setAuthMode('signup')}>
              S’inscrire
            </button>
          </>
        )}
      </div>

      {accountError && <p role="alert">{accountError}</p>}

      {authMode && (
        <AuthDialog
          initialMode={authMode}
          onClose={() => setAuthMode(null)}
          onLogin={handleLogin}
        />
      )}
      <header className="library-hero">
        <div className="hero-content">
          <svg
            className="brand-mark"
            width="26"
            height="26"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M12 6a7 7 0 0 0-8-1v13a7 7 0 0 1 8 1 7 7 0 0 1 8-1V5a7 7 0 0 0-8 1Z" />
            <path d="M12 6v13" />
          </svg>

          <h1>Lisière</h1>
          <p>Un mot suffit pour ouvrir un livre.</p>
        </div>
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

          <button type="submit" className="search-submit">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              aria-hidden="true"
            >
              <circle cx="10.5" cy="10.5" r="5.5" />
              <path d="m15 15 4 4" />
            </svg>
            Rechercher
          </button>
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