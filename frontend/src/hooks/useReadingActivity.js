import { useEffect, useState } from "react";

// Favoris et historique stockés en base : on les retrouve
// sur n'importe quelle machine une fois connecté.
const ACTIVITY_API = "/api/v1/auth/me";

async function callApi(path, options) {
  const response = await fetch(`${ACTIVITY_API}${path}`, options);
  if (!response.ok) throw new Error(String(response.status));
  return response.status === 204 ? null : response.json();
}

export default function useReadingActivity(userId) {
  const [activity, setActivity] = useState(null);
  const [storageError, setStorageError] = useState("");

  useEffect(() => {
    if (userId == null) return;
    let cancelled = false;

    Promise.all([callApi("/favorites"), callApi("/history")])
      .then(([favorites, history]) => {
        if (cancelled) return;
        setActivity({ userId, favorites, history });
        setStorageError("");
      })
      .catch(() => {
        if (cancelled) return;
        setActivity({ userId, favorites: [], history: [] });
        setStorageError("Impossible de charger tes favoris et ton historique.");
      });

    return () => {
      cancelled = true;
    };
  }, [userId]);

  const current = userId != null && activity?.userId === userId ? activity : null;

  // Mise à jour immédiate de l'écran, puis enregistrement côté serveur.
  async function persist(changes, request) {
    if (!current) return;
    const previous = current;
    setActivity({ ...current, ...changes });
    try {
      const result = await request();
      setStorageError("");
      return result;
    } catch {
      setActivity(previous);
      setStorageError("La modification n’a pas pu être enregistrée.");
    }
  }

  function toggleFavorite(book) {
    if (!current) return;
    const exists = current.favorites.some((favorite) => favorite.id === book.id);

    persist(
      {
        favorites: exists
          ? current.favorites.filter((favorite) => favorite.id !== book.id)
          : [
              { id: book.id, title: book.title, author: book.author },
              ...current.favorites,
            ],
      },
      () =>
        callApi(`/favorites/${book.id}`, { method: exists ? "DELETE" : "PUT" }),
    );
  }

  async function addHistory(query, mode) {
    if (!current) return;
    const entry = { id: `local-${Date.now()}`, query, mode, date: new Date().toISOString() };
    const saved = await persist(
      { history: [entry, ...current.history].slice(0, 30) },
      () =>
        callApi("/history", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query, mode }),
        }),
    );
    if (saved) {
      setActivity((state) =>
        state && {
          ...state,
          history: state.history.map((item) => (item.id === entry.id ? saved : item)),
        },
      );
    }
  }

  function clearHistory() {
    persist({ history: [] }, () => callApi("/history", { method: "DELETE" }));
  }

  return { activity: current, storageError, toggleFavorite, addHistory, clearHistory };
}
