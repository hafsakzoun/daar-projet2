import { useState } from "react";
import { postAuth } from "../api/auth.js";

export default function ResetPasswordPage({ token, onLogin }) {
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
    if (result.ok) setDone(true);
  }

  return (
    <section className="page page--narrow" aria-labelledby="reset-title">
      <header className="page-head">
        <h1 id="reset-title">Nouveau mot de passe</h1>
        <p>Choisis un mot de passe d’au moins 12 caractères.</p>
      </header>

      {!done && (
        <form className="auth-form" onSubmit={submit}>
          <label>
            Nouveau mot de passe
            <input name="password" type="password" autoComplete="new-password" minLength={12} maxLength={128} required readOnly={pending} />
          </label>
          <label>
            Confirmation
            <input name="confirm" type="password" autoComplete="new-password" minLength={12} maxLength={128} required readOnly={pending} />
          </label>
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

      {done && (
        <button type="button" className="btn btn--primary" onClick={onLogin}>
          Se connecter
        </button>
      )}
    </section>
  );
}
