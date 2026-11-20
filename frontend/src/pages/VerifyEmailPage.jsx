import { useEffect, useState } from "react";
import { postAuth } from "../api/auth.js";

export default function VerifyEmailPage({ token, onLogin, loggedIn }) {
  const [state, setState] = useState({ status: "pending", message: "" });

  useEffect(() => {
    let cancelled = false;
    postAuth("email/verify", { token }).then((result) => {
      if (!cancelled) {
        setState({ status: result.ok ? "done" : "error", message: result.message });
        // Le jeton ne sert plus : on le retire de l'adresse et de l'historique.
        if (result.ok) window.history.replaceState(null, "", "#/");
      }
    });
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <section className="page" aria-labelledby="verify-title">
      <header className="page-head">
        <h1 id="verify-title">Confirmation de l’adresse</h1>
        <p role={state.status === "error" ? "alert" : "status"}>
          {state.status === "pending" ? "Vérification du lien…" : state.message}
        </p>
      </header>

      {state.status === "done" && (loggedIn ? (
        <a className="btn btn--primary" href="#/">
          Retour à l’accueil
        </a>
      ) : (
        <button type="button" className="btn btn--primary" onClick={onLogin}>
          Se connecter
        </button>
      ))}
      {state.status === "error" && (
        <a className="btn" href="#/">
          Retour à l’accueil
        </a>
      )}
    </section>
  );
}
