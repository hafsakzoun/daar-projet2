import { useEffect, useState } from 'react'

const API_URL = '/api/v1'

function App() {
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()

    async function loadBooks() {
      try {
        const response = await fetch(`${API_URL}/books`, {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error(`Erreur HTTP ${response.status}`)
        }

        const data = await response.json()
        setBooks(data.results)
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError('Impossible de récupérer les livres depuis FastAPI.')
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    loadBooks()

    return () => controller.abort()
  }, [])

  return (
    <main>
      <h1>Bibliothèque DAAR</h1>
      <p>Moteur de recherche de livres</p>

      {loading && <p>Chargement…</p>}
      {error && <p role="alert">{error}</p>}

      <ul>
        {books.map((book) => (
          <li key={book.id}>
            <strong>{book.title}</strong> — {book.author}
          </li>
        ))}
      </ul>
    </main>
  )
}

export default App