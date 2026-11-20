import { useEffect, useState } from "react";
import AuthDialog from "./components/AuthDialog.jsx";
import Results from "./components/Results.jsx";
import SignInRequired from "./components/SignInRequired.jsx";
import useReadingActivity from "./hooks/useReadingActivity.js";
import BookReader from "./pages/BookReader.jsx";
import FavoritesPage from "./pages/FavoritesPage.jsx";
import AccountPage from "./pages/AccountPage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import ResetPasswordPage from "./pages/ResetPasswordPage.jsx";
import VerifyEmailPage from "./pages/VerifyEmailPage.jsx";
import { navigate, useHashRoute } from "./useHashRoute.js";
import "./App.css";

// Décor : une rangée de dos de livres (largeur, hauteur, couleur).
const SPINES = [
  [26, 78, "#1f4d3a"], [18, 92, "#6b2737"], [30, 70, "#22375a"],
  [16, 85, "#8a6a2a"], [24, 96, "#3d3a52"], [20, 74, "#1f4d3a"],
  [34, 88, "#22375a"], [16, 66, "#6b2737"], [22, 82, "#8a6a2a", true],
];

function HeroSpines() {
  return (
    <div className="spines" aria-hidden="true">
      {SPINES.map(([width, height, color, lean], index) => (
        <span
          key={index}
          className={lean ? "lean" : undefined}
          style={{ "--w": `${width}px`, "--h": `${height}%`, "--c": color }}
        />
      ))}
    </div>
  );
}

function App() {
  const [mode, setMode] = useState("keyword");
  const [searchInput, setSearchInput] = useState("");
  const [authMode, setAuthMode] = useState(null);
  const [user, setUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [loggingOut, setLoggingOut] = useState(false);
  const [accountError, setAccountError] = useState("");
  const [accountNotice, setAccountNotice] = useState("");
  const route = useHashRoute();

  // Un lien d'e-mail ouvert dans l'onglet ferme la fenêtre de connexion,
  // qui masquerait sinon la page de confirmation ou de réinitialisation.
  const [routeSeen, setRouteSeen] = useState(route);
  if (routeSeen !== route) {
    setRouteSeen(route);
    setAuthMode(null);
  }
  const [request, setRequest] = useState({
    query: "",
    mode: "keyword",
    offset: 0,
    sort: "occurrences",
    id: 0,
  });

  const { activity, storageError, toggleFavorite, addHistory, clearHistory } =
    useReadingActivity(user?.id);

  useEffect(() => {
    const controller = new AbortController();

    async function restoreSession() {
      try {
        const response = await fetch("/api/v1/auth/me", {
          signal: controller.signal,
        });

        if (response.status === 401) return;
        if (!response.ok) throw new Error("Vérification impossible");

        const profile = await response.json();
        if (!controller.signal.aborted) setUser(profile);
      } catch {
        if (!controller.signal.aborted) {
          setAccountError("Impossible de vérifier ta session.");
        }
      } finally {
        if (!controller.signal.aborted) setCheckingSession(false);
      }
    }

    restoreSession();
    return () => controller.abort();
  }, []);

  function handleLogin(profile) {
    setAccountNotice("");
    setUser(profile);
    setAuthMode(null);
    setAccountError("");
    // Après une confirmation ou une réinitialisation, on quitte la page du lien.
    if (route.name === "verify" || route.name === "reset") navigate("/");
  }

  async function handleLogout() {
    setLoggingOut(true);
    setAccountError("");

    try {
      const response = await fetch("/api/v1/auth/logout", {
        method: "POST",
      });

      if (!response.ok) throw new Error("Déconnexion impossible");

      setUser(null);
      if (["favorites", "history", "account"].includes(route.name)) navigate("/");
    } catch {
      setAccountError("Impossible de te déconnecter. Réessaie.");
    } finally {
      setLoggingOut(false);
    }
  }

  function runSearch(query, searchMode) {
    setRequest((previous) => ({
      query,
      mode: searchMode,
      offset: 0,
      sort: previous.sort,
      id: previous.id + 1,
    }));

    if (query) addHistory(query, searchMode);
  }

  function submit(event) {
    event.preventDefault();
    runSearch(searchInput.trim(), mode);
  }

  function replaySearch(entry) {
    navigate("/");
    setSearchInput(entry.query);
    setMode(entry.mode);
    runSearch(entry.query, entry.mode);
  }

  return (
    <div className="app">
      <header className="topbar">
        <a className="brand" href="#/">
          <svg
            className="brand-mark"
            width="24"
            height="24"
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
          <span>Lisière</span>
        </a>

        <div className="topbar-actions">
          <nav className="main-nav" aria-label="Navigation principale">
            <a href="#/" aria-current={route.name === "search" ? "page" : undefined}>
              Recherche
            </a>
            {activity && (
              <>
                <a
                  href="#/favoris"
                  aria-current={route.name === "favorites" ? "page" : undefined}
                >
                  Favoris
                  <span className="nav-count">{activity.favorites.length}</span>
                </a>
                <a
                  href="#/historique"
                  aria-current={route.name === "history" ? "page" : undefined}
                >
                  Historique
                </a>
              </>
            )}
          </nav>

          <div className="account-actions" role="group" aria-label="Compte">
            {checkingSession ? (
              <span className="account-welcome" role="status">
                Vérification de la session…
              </span>
            ) : user ? (
              <>
                <span className="account-welcome" role="status">
                  Bienvenue, {user.first_name} !
                </span>

                <a
                  className="btn btn--ghost"
                  href="#/compte"
                  aria-current={route.name === "account" ? "page" : undefined}
                >
                  Mon compte
                </a>

                <button
                  type="button"
                  className="btn btn--ghost"
                  onClick={handleLogout}
                  disabled={loggingOut}
                >
                  {loggingOut ? "Déconnexion…" : "Se déconnecter"}
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  className="btn btn--ghost"
                  onClick={() => setAuthMode("login")}
                >
                  Se connecter
                </button>

                <button
                  type="button"
                  className="btn btn--primary"
                  onClick={() => setAuthMode("signup")}
                >
                  S’inscrire
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="library">
        {storageError && <p role="alert">{storageError}</p>}
        {accountError && <p role="alert">{accountError}</p>}
        {accountNotice && (
          <p className="auth-notice auth-notice--success page-notice" role="status">
            {accountNotice}
          </p>
        )}

        {authMode && (
          <AuthDialog
            initialMode={authMode}
            onClose={() => setAuthMode(null)}
            onLogin={handleLogin}
          />
        )}

        {route.name === "favorites" && (activity ? (
          <FavoritesPage activity={activity} onRemove={toggleFavorite} />
        ) : (
          <SignInRequired onLogin={() => setAuthMode("login")} checking={checkingSession} />
        ))}

        {route.name === "history" && (activity ? (
          <HistoryPage
            activity={activity}
            onReplay={replaySearch}
            onClear={clearHistory}
          />
        ) : (
          <SignInRequired onLogin={() => setAuthMode("login")} checking={checkingSession} />
        ))}

        {route.name === "account" && (user ? (
          <AccountPage
            user={user}
            onDeleted={() => {
              setUser(null);
              setAccountNotice("Ton compte a été supprimé. Un e-mail de confirmation t’a été envoyé.");
              navigate("/");
            }}
          />
        ) : (
          <SignInRequired onLogin={() => setAuthMode("login")} checking={checkingSession} />
        ))}

        {route.name === "verify" && (
          <VerifyEmailPage token={route.token} loggedIn={Boolean(user)} onLogin={() => setAuthMode("login")} />
        )}

        {route.name === "reset" && (
          <ResetPasswordPage token={route.token} loggedIn={Boolean(user)} onLogin={() => setAuthMode("login")} />
        )}

        {route.name === "book" && (
          <BookReader
            key={route.bookId}
            bookId={route.bookId}
            favorites={activity?.favorites ?? []}
            onToggleFavorite={activity ? toggleFavorite : undefined}
          />
        )}

        {route.name === "search" && (
        <>
        <section className="hero">
          <div>
          <p className="eyebrow">Bibliothèque · 1 700 livres du Projet Gutenberg</p>
          <h1>
            Un mot suffit pour <em>ouvrir</em> un livre.
          </h1>
          <p className="hero-sub">
            Cherche par mot-clé ou par expression régulière dans le texte
            intégral des livres.
          </p>

          <form className="search" onSubmit={submit}>
            <div className="search-row">
              <label htmlFor="book-query" className="sr-only">
                {mode === "regex" ? "Expression régulière" : "Mot-clé"}
              </label>

              <div className="search-field">
                <svg
                  width="20"
                  height="20"
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

                <input
                  id="book-query"
                  name="query"
                  type="search"
                  value={searchInput}
                  onChange={(event) => setSearchInput(event.target.value)}
                  placeholder={
                    mode === "regex"
                      ? "Ex. histor.*"
                      : "Rechercher dans les livres…"
                  }
                  maxLength={mode === "regex" ? 100 : undefined}
                  aria-describedby="search-hint"
                />
              </div>

              <button type="submit" className="btn btn--primary search-submit">
                Rechercher
              </button>
            </div>

            <div className="search-meta">
              <fieldset className="search-modes">
                <legend className="sr-only">Mode de recherche</legend>

                <label>
                  <input
                    type="radio"
                    name="mode"
                    value="keyword"
                    checked={mode === "keyword"}
                    onChange={() => setMode("keyword")}
                  />
                  <span>Mot-clé</span>
                </label>

                <label>
                  <input
                    type="radio"
                    name="mode"
                    value="regex"
                    checked={mode === "regex"}
                    onChange={() => setMode("regex")}
                  />
                  <span>Regex</span>
                </label>
              </fieldset>

              <p id="search-hint" className="hint">
                {mode === "regex"
                  ? "La regex est comparée à chaque terme entier de l’index."
                  : "Essaie un mot du corpus, par exemple « history »."}
              </p>
            </div>
          </form>
          </div>

          <HeroSpines />
        </section>

        <Results
          key={`${request.id}:${request.offset}`}
          query={request.query}
          mode={request.mode}
          offset={request.offset}
          sort={request.sort}
          onPageChange={(offset) =>
            setRequest((previous) => ({ ...previous, offset }))
          }
          onSortChange={(sort) =>
            setRequest((previous) => ({
              ...previous,
              sort,
              offset: 0,
              id: previous.id + 1,
            }))
          }
          favorites={activity?.favorites ?? []}
          onToggleFavorite={activity ? toggleFavorite : undefined}
        />
        </>
        )}
      </main>
    </div>
  );
}

export default App;
