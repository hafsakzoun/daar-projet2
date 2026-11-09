import { useEffect, useState, useRef } from 'react'
import AuthDialog from './AuthDialog.jsx'
import BookRecommendations from './BookRecommendations'
import './App.css'

const PAGE_SIZE = 20
const number = new Intl.NumberFormat('fr-FR')

const historyDate = new Intl.DateTimeFormat('fr-FR', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

function useReadingActivity(userId) {
  const storageKey = userId == null ? null : `lisiere:activity:${userId}`
  const [activity, setActivity] = useState(null)
  const [storageError, setStorageError] = useState('')

  useEffect(() => {
    if (!storageKey) return

    try {
      const saved = JSON.parse(localStorage.getItem(storageKey))

      setActivity({
        key: storageKey,
        favorites: Array.isArray(saved?.favorites) ? saved.favorites : [],
        history: Array.isArray(saved?.history) ? saved.history : [],
      })
      setStorageError('')
    } catch {
      setActivity({ key: storageKey, favorites: [], history: [] })
      setStorageError('Impossible de lire tes favoris et ton historique.')
    }
  }, [storageKey])

  const current = storageKey && activity?.key === storageKey ? activity : null

  function save(changes) {
    if (!current) return

    const next = { ...current, ...changes }
    setActivity(next)

    try {
      localStorage.setItem(storageKey, JSON.stringify({
        favorites: next.favorites,
        history: next.history,
      }))
      setStorageError('')
    } catch {
      setStorageError(
        'Tes modifications sont visibles, mais le navigateur n’a pas pu les enregistrer.',
      )
    }
  }

  return { activity: current, save, storageError }
}

function RecommendationsDrawer({ book, onClose }) {
  const dialogRef = useRef(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog.open) dialog.showModal()
  }, [])

  return (
    <dialog
      ref={dialogRef}
      className="recommendations-drawer"
      aria-labelledby="recommendations-heading"
      onClose={onClose}
    >
      <header className="recommendations-drawer__header">
        <div>
          <p className="recommendations-kicker">Lisière · Découverte</p>
          <h2 id="recommendations-heading">Livres similaires</h2>
          <p className="recommendations-source">
            À partir de <cite>{book.title}</cite>
          </p>
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
        <BookRecommendations bookId={book.id} />
      </div>
    </dialog>
  )
}

function Results({
  query,
  mode,
  offset,
  onPageChange,
  favorites,
  onToggleFavorite,
}) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [selectedBook, setSelectedBook] = useState(null)

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
          throw new Error(
            typeof body?.detail === 'string'
              ? body.detail
              : 'La requête a échoué.',
          )
        }

        if (!Array.isArray(body?.results)) {
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
              {data.results.map((book) => {
                const isFavorite = favorites.some((favorite) => favorite.id === book.id)

                return (
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

                      {onToggleFavorite && (
                        <button
                          type="button"
                          className="favorite-toggle"
                          aria-label={`Favori pour ${book.title}`}
                          aria-pressed={isFavorite}
                          onClick={() => onToggleFavorite(book)}
                        >
                          <span aria-hidden="true">{isFavorite ? '★' : '☆'}</span>
                        </button>
                      )}

                      {query && (
                        <span className="score">
                          {number.format(book.score)}{' '}
                          {book.score === 1 ? 'occurrence' : 'occurrences'}
                        </span>
                      )}

                      <button
                        type="button"
                        className="similar-trigger"
                        aria-haspopup="dialog"
                        aria-label={`Livres similaires à ${book.title}`}
                        onClick={() => setSelectedBook(book)}
                      >
                        <span aria-hidden="true">↗</span> Similaires
                      </button>
                    </div>
                  </li>
                )
              })}
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
                Page {Math.floor(offset / data.limit) + 1} sur{' '}
                {Math.ceil(data.total / data.limit)}
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
      {selectedBook && (
        <RecommendationsDrawer
          key={selectedBook.id}
          book={selectedBook}
          onClose={() => setSelectedBook(null)}
        />
      )}
    </section>
  )
}

function App() {
  const [mode, setMode] = useState('keyword')
  const [searchInput, setSearchInput] = useState('')
  const [authMode, setAuthMode] = useState(null)
  const [user, setUser] = useState(null)
  const [checkingSession, setCheckingSession] = useState(true)
  const [loggingOut, setLoggingOut] = useState(false)
  const [accountError, setAccountError] = useState('')
  const [activePanel, setActivePanel] = useState(null)
  const [request, setRequest] = useState({
    query: '',
    mode: 'keyword',
    offset: 0,
    id: 0,
  })

  const { activity, save, storageError } = useReadingActivity(user?.id)

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
      const response = await fetch('/api/v1/auth/logout', {
        method: 'POST',
      })

      if (!response.ok) throw new Error('Déconnexion impossible')

      setUser(null)
      setActivePanel(null)
    } catch {
      setAccountError('Impossible de te déconnecter. Réessaie.')
    } finally {
      setLoggingOut(false)
    }
  }

  function runSearch(query, searchMode) {
    setRequest((previous) => ({
      query,
      mode: searchMode,
      offset: 0,
      id: previous.id + 1,
    }))

    if (query && activity) {
      const entry = {
        id: crypto.randomUUID(),
        query,
        mode: searchMode,
        date: new Date().toISOString(),
      }

      save({ history: [entry, ...activity.history].slice(0, 30) })
    }
  }

  function submit(event) {
    event.preventDefault()
    runSearch(searchInput.trim(), mode)
  }

  function replaySearch(entry) {
    setSearchInput(entry.query)
    setMode(entry.mode)
    runSearch(entry.query, entry.mode)
  }

  function toggleFavorite(book) {
    if (!activity) return

    const exists = activity.favorites.some((favorite) => favorite.id === book.id)

    save({
      favorites: exists
        ? activity.favorites.filter((favorite) => favorite.id !== book.id)
        : [
            { id: book.id, title: book.title, author: book.author },
            ...activity.favorites,
          ],
    })
  }

  return (
    <main className="library">
      <div className="library-toolbar">
        {activity && (
          <div className="activity-actions" role="group" aria-label="Ma bibliothèque">
            <button
              type="button"
              aria-expanded={activePanel === 'favorites'}
              aria-controls="activity-favorites"
              onClick={() => setActivePanel((current) =>
                current === 'favorites' ? null : 'favorites'
              )}
            >
              <span aria-hidden="true">☆</span> Favoris
            </button>

            <button
              type="button"
              aria-expanded={activePanel === 'history'}
              aria-controls="activity-history"
              onClick={() => setActivePanel((current) =>
                current === 'history' ? null : 'history'
              )}
            >
              <span aria-hidden="true">◷</span> Historique
            </button>
          </div>
        )}
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
      </div>

      {activity && (
        <div className="activity-panel" hidden={!activePanel && !storageError}>
          {storageError && <p role="alert">{storageError}</p>}

          <section id="activity-favorites" className="activity-section" hidden={activePanel !== 'favorites'}>
            <h2>Favoris · {activity.favorites.length}</h2>

            {activity.favorites.length === 0 ? (
              <p>Clique sur l’étoile d’un livre pour l’ajouter ici.</p>
            ) : (
              <ul className="activity-list">
                {activity.favorites.map((book) => (
                  <li key={book.id}>
                    <div>
                      <strong>{book.title}</strong>
                      <small>{book.author}</small>
                    </div>

                    <button
                      type="button"
                      onClick={() => toggleFavorite(book)}
                      aria-label={`Retirer ${book.title} des favoris`}
                    >
                      Retirer
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section id="activity-history" className="activity-section" hidden={activePanel !== 'history'}>
            <h2>Historique de recherche · {activity.history.length}</h2>

            {activity.history.length === 0 ? (
              <p>Tes recherches apparaîtront ici avec leur date et leur heure.</p>
            ) : (
              <ul className="activity-list">
                {activity.history.map((entry) => (
                  <li key={entry.id}>
                    <div>
                      <strong>{entry.query}</strong>
                      <small>
                        {entry.mode === 'regex' ? 'Regex' : 'Mot-clé'} ·{' '}
                        <time dateTime={entry.date}>
                          {historyDate.format(new Date(entry.date))}
                        </time>
                      </small>
                    </div>

                    <button
                      type="button"
                      aria-label={`Relancer la recherche ${entry.query}`}
                      onClick={() => replaySearch(entry)}
                    >
                      Relancer
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}

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
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
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
        favorites={activity?.favorites ?? []}
        onToggleFavorite={activity ? toggleFavorite : undefined}
      />
    </main>
  )
}

export default App
