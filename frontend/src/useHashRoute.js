import { useEffect, useState } from "react";

// Routage minimal par hash (#/favoris, #/livre/12…) :
// aucune dépendance, et nginx n'a rien à configurer.
function parse(hash) {
  const [path = "/", query = ""] = (hash.replace(/^#/, "") || "/").split("?");
  const params = new URLSearchParams(query);
  const book = path.match(/^\/livre\/(\d+)$/);

  if (book) return { name: "book", bookId: Number(book[1]) };
  // Liens envoyés par e-mail : le jeton reste après le « # »,
  // il n'est donc jamais transmis au serveur ni aux journaux.
  if (path === "/verifier") return { name: "verify", token: params.get("jeton") ?? "" };
  if (path === "/reinitialiser") return { name: "reset", token: params.get("jeton") ?? "" };
  if (path === "/favoris") return { name: "favorites" };
  if (path === "/historique") return { name: "history" };
  if (path === "/compte") return { name: "account" };
  return { name: "search" };
}

export function useHashRoute() {
  const [route, setRoute] = useState(() => parse(window.location.hash));

  useEffect(() => {
    const onChange = () => {
      setRoute(parse(window.location.hash));
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  return route;
}

export function navigate(path) {
  // Si l'adresse est déjà la bonne (ex. jeton retiré avec replaceState),
  // le navigateur n'émet pas « hashchange » : on le déclenche nous-mêmes.
  if (window.location.hash === `#${path}`) {
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  } else {
    window.location.hash = path;
  }
}
