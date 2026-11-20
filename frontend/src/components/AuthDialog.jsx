import { useEffect, useRef, useState } from "react";
import { postAuth } from "../api/auth.js";

const TITLES = {
  login: "Se connecter",
  signup: "Créer un compte",
  forgot: "Mot de passe oublié",
};

function AuthDialog({ initialMode, onClose, onLogin }) {
  const dialog = useRef(null);
  const [mode, setMode] = useState(initialMode);
  const [notice, setNotice] = useState(null);
  const [email, setEmail] = useState("");
  const [pending, setPending] = useState(false);
  // Connexion refusée car l'adresse n'est pas encore confirmée.
  const [unverified, setUnverified] = useState(false);

  useEffect(() => {
    const element = dialog.current;
    element.showModal();

    return () => element.close();
  }, []);

  function changeMode(nextMode) {
    if (nextMode === mode) return;
    setMode(nextMode);
    setNotice(null);
    setUnverified(false);
  }

  async function run(path, payload) {
    setPending(true);
    setNotice(null);
    try {
      return await postAuth(path, payload);
    } finally {
      setPending(false);
    }
  }

  async function submit(event) {
    event.preventDefault();
    if (pending) return;

    const fields = new FormData(event.currentTarget);
    const address = email.trim();

    if (mode === "forgot") {
      const result = await run("password/forgot", { email: address });
      setNotice({
        type: result.ok ? "success" : "error",
        text: result.ok
          ? "Si un compte correspond à cette adresse, tu vas recevoir un e-mail avec un lien pour choisir un nouveau mot de passe (pense à regarder les spams)."
          : result.message,
      });
      return;
    }

    if (mode === "signup") {
      const firstName = fields.get("firstName").trim();
      if (!firstName) {
        setNotice({ type: "error", text: "Renseigne ton prénom." });
        return;
      }

      const result = await run("signup", {
        email: address,
        password: fields.get("password"),
        first_name: firstName,
      });
      if (!result.ok) {
        setNotice({ type: "error", text: result.message });
        return;
      }

      setMode("login");
      setNotice({
        type: "success",
        text: result.body?.verification_required
          ? `Compte créé. Un e-mail de confirmation a été envoyé à ${address} : clique sur le lien qu’il contient pour activer ton compte.`
          : "Ton compte a été créé. Tu peux maintenant te connecter.",
      });
      return;
    }

    const result = await run("login", { email: address, password: fields.get("password") });
    if (result.ok) {
      onLogin(result.body);
      return;
    }
    setUnverified(result.status === 403);
    setNotice({ type: "error", text: result.message });
  }

  async function resend() {
    const result = await run("email/resend", { email: email.trim() });
    setUnverified(false);
    setNotice({
      type: result.ok ? "success" : "error",
      text: result.ok ? "Un nouvel e-mail de confirmation vient d’être envoyé." : result.message,
    });
  }

  return (
    <dialog
      ref={dialog}
      className="auth-dialog"
      aria-labelledby="auth-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!pending) onClose();
      }}
    >
      <div className="auth-heading">
        <h2 id="auth-title">{TITLES[mode]}</h2>

        <button
          type="button"
          className="auth-close"
          aria-label="Fermer"
          onClick={onClose}
          disabled={pending}
        >
          ×
        </button>
      </div>

      {mode === "forgot" ? (
        <p className="auth-intro">
          Indique l’adresse de ton compte : nous t’enverrons un lien pour
          choisir un nouveau mot de passe.
        </p>
      ) : (
        <div className="auth-switch" role="group" aria-label="Accès au compte">
          <button
            type="button"
            aria-pressed={mode === "login"}
            onClick={() => changeMode("login")}
            disabled={pending}
          >
            Connexion
          </button>

          <button
            type="button"
            aria-pressed={mode === "signup"}
            onClick={() => changeMode("signup")}
            disabled={pending}
          >
            Inscription
          </button>
        </div>
      )}

      <form key={mode} className="auth-form" onSubmit={submit}>
        {mode === "signup" && (
          <label>
            Prénom
            <input
              name="firstName"
              autoComplete="given-name"
              maxLength={80}
              readOnly={pending}
              required
            />
          </label>
        )}

        <label>
          Adresse e-mail
          <input
            name="email"
            type="email"
            autoComplete="email"
            placeholder="nom@exemple.fr"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            maxLength={254}
            readOnly={pending}
            required
          />
        </label>

        {mode !== "forgot" && (
          <label>
            Mot de passe
            <input
              name="password"
              type="password"
              autoComplete={mode === "signup" ? "new-password" : "current-password"}
              minLength={mode === "signup" ? 12 : undefined}
              maxLength={128}
              aria-describedby={mode === "signup" ? "password-hint" : undefined}
              readOnly={pending}
              required
            />
          </label>
        )}

        {mode === "signup" && <small id="password-hint">Au moins 12 caractères.</small>}

        {mode === "login" && (
          <button
            type="button"
            className="auth-link"
            onClick={() => changeMode("forgot")}
            disabled={pending}
          >
            Mot de passe oublié ?
          </button>
        )}

        <button
          type="submit"
          className="btn btn--primary btn--block"
          disabled={pending}
        >
          {pending
            ? "Patiente…"
            : mode === "signup"
              ? "Créer mon compte"
              : mode === "forgot"
                ? "Envoyer le lien"
                : "Se connecter"}
        </button>

        {mode === "forgot" && (
          <button
            type="button"
            className="auth-link"
            onClick={() => changeMode("login")}
            disabled={pending}
          >
            ← Retour à la connexion
          </button>
        )}
      </form>

      {notice && (
        <p
          className={`auth-notice auth-notice--${notice.type}`}
          role={notice.type === "error" ? "alert" : "status"}
        >
          {notice.text}
        </p>
      )}

      {unverified && (
        <button
          type="button"
          className="btn btn--block auth-resend"
          onClick={resend}
          disabled={pending}
        >
          Renvoyer l’e-mail de confirmation
        </button>
      )}
    </dialog>
  );
}

export default AuthDialog;
