import { useEffect, useState } from "react";

// Routage minimal par hash (#/favoris, #/livre/12…) :
// aucune dépendance, et nginx n'a rien à configurer.
function parse(hash) {
  const path = hash.replace(/^#/, "") || "/";
  const book = path.match(/^\/livre\/(\d+)$/);

  if (book) return { name: "book", bookId: Number(book[1]) };
  if (path === "/favoris") return { name: "favorites" };
  if (path === "/historique") return { name: "history" };
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
  window.location.hash = path;
}
