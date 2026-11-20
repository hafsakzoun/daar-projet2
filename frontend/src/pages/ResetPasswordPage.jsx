import { useState } from "react";
import { postAuth } from "../api/auth.js";
import PasswordInput from "../components/PasswordInput.jsx";

export default function ResetPasswordPage({ token, onLogin, loggedIn }) {
  const [notice, setNotice] = useState(null);
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);

  async function submit(event) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const password = fields.get("password");

    if (password !== fields.get("confirm")) {
      setNotice({ type: "error", text: "Les deux mots de passe ne sont pas identiques." });
      return;
    }

    setPending(true);
    const result = await postAuth("password/reset", { token, password });
    setPending(false);
    setNotice({ type: result.ok ? "success" : "error", text: result.message });
    if (result.ok) {
      setDone(true);
      window.history.replaceState(null, "", "#/");
    }
  }

  return (
    <section className="page page--narrow" aria-labelledby="reset-title">
      <header className="page-head">
        <h1 id="reset-title">Nouveau mot de passe</h1>
        <p>Choisis un mot de passe d’au moins 12 caractères.</p>
      </header>

      {!done && (
        <form className="auth-form" onSubmit={submit}>
          <PasswordInput label="Nouveau mot de passe" name="password" autoComplete="new-password" minLength={12} maxLength={128} hint="Au moins 12 caractères." required readOnly={pending} />
          <PasswordInput label="Confirmer le mot de passe" name="confirm" autoComplete="new-password" minLength={12} maxLength={128} required readOnly={pending} />
          <button type="submit" className="btn btn--primary btn--block" disabled={pending}>
            {pending ? "Patiente…" : "Enregistrer"}
          </button>
        </form>
      )}

      {notice && (
        <p className={`auth-notice auth-notice--${notice.type}`} role={notice.type === "error" ? "alert" : "status"}>
          {notice.text}
        </p>
      )}

      {done && (loggedIn ? (
        <a className="btn btn--primary" href="#/">
          Retour à l’accueil
        </a>
      ) : (
        <button type="button" className="btn btn--primary" onClick={onLogin}>
          Se connecter
        </button>
      ))}
    </section>
  );
}
