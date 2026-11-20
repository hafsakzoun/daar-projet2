import { useState } from "react";

function EyeIcon({ open }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" />
      {!open && <path d="M4 4l16 16" />}
    </svg>
  );
}

// Champ mot de passe avec un bouton pour afficher ou masquer la saisie.
export default function PasswordInput({ label, hint, invalid, ...inputProps }) {
  const [visible, setVisible] = useState(false);

  return (
    <label>
      {label}
      <span className="password-field">
        <input
          {...inputProps}
          type={visible ? "text" : "password"}
          aria-invalid={invalid || undefined}
          spellCheck={false}
          autoCapitalize="off"
        />
        <button
          type="button"
          className="password-toggle"
          onClick={() => setVisible((value) => !value)}
          aria-label={visible ? "Masquer le mot de passe" : "Afficher le mot de passe"}
          aria-pressed={visible}
          title={visible ? "Masquer" : "Afficher"}
        >
          <EyeIcon open={!visible} />
        </button>
      </span>
      {hint && <small className={invalid ? "field-error" : undefined}>{hint}</small>}
    </label>
  );
}
