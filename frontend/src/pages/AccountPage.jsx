import { useState } from "react";
import { postAuth } from "../api/auth.js";
import PasswordInput from "../components/PasswordInput.jsx";

// Page « Mon compte » : informations et changement du mot de passe.
function DeleteAccount({ onDeleted }) {
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    const password = new FormData(event.currentTarget).get("password");
    setPending(true);
    setError("");
    const result = await postAuth("me/delete", { password });
    setPending(false);
    if (result.ok) onDeleted();
    else setError(result.message);
  }

  return (
    <section className="danger-zone" aria-labelledby="delete-title">
      <h2 id="delete-title" className="section-title">Supprimer mon compte</h2>
      <p>
        Ton compte, tes favoris et ton historique de recherche seront
        définitivement effacés. Cette action est irréversible.
      </p>

      {!open ? (
        <button type="button" className="btn btn--danger" onClick={() => setOpen(true)}>
          Supprimer mon compte
        </button>
      ) : (
        <form className="auth-form" onSubmit={submit}>
          <PasswordInput
            label="Confirme avec ton mot de passe"
            name="password"
            autoComplete="current-password"
            maxLength={128}
            required
            readOnly={pending}
          />
          <div className="danger-actions">
            <button type="submit" className="btn btn--danger" disabled={pending}>
              {pending ? "Suppression…" : "Supprimer définitivement"}
            </button>
            <button type="button" className="btn btn--ghost" onClick={() => setOpen(false)} disabled={pending}>
              Annuler
            </button>
          </div>
          {error && (
            <p className="auth-notice auth-notice--error" role="alert">
              {error}
            </p>
          )}
        </form>
      )}
    </section>
  );
}

export default function AccountPage({ user, onDeleted }) {
  const [notice, setNotice] = useState(null);
  const [pending, setPending] = useState(false);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [formKey, setFormKey] = useState(0);
  const mismatch = confirm !== "" && confirm !== password;

  async function submit(event) {
    event.preventDefault();
    if (pending || mismatch) return;
    const current = new FormData(event.currentTarget).get("current");

    setPending(true);
    setNotice(null);
    const result = await postAuth("password/change", {
      current_password: current,
      new_password: password,
    });
    setPending(false);
    setNotice({ type: result.ok ? "success" : "error", text: result.message });

    if (result.ok) {
      // Vide le formulaire après un changement réussi.
      setPassword("");
      setConfirm("");
      setFormKey((key) => key + 1);
    }
  }

  return (
    <section className="page page--narrow" aria-labelledby="account-title">
      <header className="page-head">
        <h1 id="account-title">Mon compte</h1>
        <p>
          {user.first_name} · {user.email}
        </p>
      </header>

      <h2 className="section-title">Changer le mot de passe</h2>
      <form key={formKey} className="auth-form" onSubmit={submit}>
        <PasswordInput label="Mot de passe actuel" name="current" autoComplete="current-password" maxLength={128} required readOnly={pending} />
        <PasswordInput
          label="Nouveau mot de passe"
          name="password"
          autoComplete="new-password"
          minLength={12}
          maxLength={128}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          hint="Au moins 12 caractères."
          required
          readOnly={pending}
        />
        <PasswordInput
          label="Confirmer le nouveau mot de passe"
          name="confirm"
          autoComplete="new-password"
          minLength={12}
          maxLength={128}
          value={confirm}
          onChange={(event) => setConfirm(event.target.value)}
          invalid={mismatch}
          hint={mismatch ? "Les mots de passe ne correspondent pas." : undefined}
          required
          readOnly={pending}
        />
        <button type="submit" className="btn btn--primary btn--block" disabled={pending || mismatch}>
          {pending ? "Patiente…" : "Changer le mot de passe"}
        </button>
      </form>

      {notice && (
        <p className={`auth-notice auth-notice--${notice.type}`} role={notice.type === "error" ? "alert" : "status"}>
          {notice.text}
        </p>
      )}

      <DeleteAccount onDeleted={onDeleted} />
    </section>
  );
}
