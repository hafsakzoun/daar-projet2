import { useEffect, useRef, useState } from 'react'

function AuthDialog({ initialMode, onClose }) {
  const dialog = useRef(null)
  const [mode, setMode] = useState(initialMode)
  const [message, setMessage] = useState('')
  const isSignup = mode === 'signup'

  useEffect(() => {
    const element = dialog.current
    element.showModal()

    return () => element.close()
  }, [])

  function changeMode(nextMode) {
    setMode(nextMode)
    setMessage('')
  }

  function submit(event) {
    event.preventDefault()
    setMessage('Le formulaire est valide. La gestion des comptes reste à connecter.')
  }

  return (
    <dialog
      ref={dialog}
      className="auth-dialog"
      aria-labelledby="auth-title"
      onCancel={(event) => {
        event.preventDefault()
        onClose()
      }}
    >
      <div className="auth-heading">
        <h2 id="auth-title">{isSignup ? 'Créer un compte' : 'Se connecter'}</h2>
        <button
          type="button"
          className="auth-close"
          aria-label="Fermer"
          onClick={onClose}
        >
          ×
        </button>
      </div>

      <div className="auth-switch" role="group" aria-label="Accès au compte">
        <button
          type="button"
          aria-pressed={!isSignup}
          onClick={() => changeMode('login')}
        >
          Connexion
        </button>
        <button
          type="button"
          aria-pressed={isSignup}
          onClick={() => changeMode('signup')}
        >
          Inscription
        </button>
      </div>

      <form key={mode} className="auth-form" onSubmit={submit}>
        {isSignup && (
          <label>
            Prénom
            <input name="firstName" autoComplete="given-name" required />
          </label>
        )}

        <label>
          Adresse e-mail
          <input
            name="email"
            type="email"
            autoComplete="email"
            placeholder="nom@exemple.fr"
            required
          />
        </label>

        <label>
          Mot de passe
          <input
            name="password"
            type="password"
            autoComplete={isSignup ? 'new-password' : 'current-password'}
            minLength={isSignup ? 8 : undefined}
            aria-describedby={isSignup ? 'password-hint' : undefined}
            required
          />
        </label>

        {isSignup && <small id="password-hint">Au moins 8 caractères.</small>}

        <button type="submit">
          {isSignup ? 'Créer mon compte' : 'Se connecter'}
        </button>

        <p className="auth-status" role="status">{message}</p>
      </form>
    </dialog>
  )
}

export default AuthDialog