import { useEffect, useState } from 'react'

export default function BookRecommendations({ bookId }) {
  const [results, setResults] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()

    async function loadRecommendations() {
      try {
        const response = await fetch(
          `/api/v1/books/${bookId}/recommendations?limit=5`,
          { signal: controller.signal },
        )
        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.detail || 'Recommandations indisponibles.')
        }

        setResults(data.results)
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err.message)
        }
      }
    }

    loadRecommendations()
    return () => controller.abort()
  }, [bookId])

  return (
    <section>
      <h2>Livres similaires</h2>
      {error && <p role="alert">{error}</p>}
      {!error && results === null && <p>Chargement…</p>}
      {results?.length === 0 && <p>Aucun livre similaire trouvé.</p>}
      {results?.length > 0 && (
        <ul>
          {results.map((book) => (
            <li key={book.id}>
              {book.title} — {book.author} ({Math.round(book.similarity * 100)} %)
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}