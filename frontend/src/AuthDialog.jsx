import { useEffect, useRef, useState } from 'react'

function AuthDialog({ initialMode, onClose, onLogin }) {
  const dialog = useRef(null)
  const [mode, setMode] = useState(initialMode)
  const [notice, setNotice] = useState(null)
  const [email, setEmail] = useState('')
  const [pending, setPending] = useState(false)
  const isSignup = mode === 'signup'

  useEffect(() => {
    const element = dialog.current
    element.showModal()

    return () => element.close()
  }, [])

  function changeMode(nextMode) {
    if (nextMode === mode) return
    setMode(nextMode)
    setNotice(null)
  }

  async function submit(event) {
    event.preventDefault()
    if (pending) return

    const form = event.currentTarget
    const fields = new FormData(form)
    const payload = {
      email: email.trim(),
      password: fields.get('password'),
    }

    if (isSignup) {
      payload.first_name = fields.get('firstName').trim()

      if (!payload.first_name) {
        setNotice({ type: 'error', text: 'Renseigne ton prénom.' })
        return
      }
    }

    setPending(true)
    setNotice(null)

    try {
      const endpoint = isSignup ? 'signup' : 'login'
      const response = await fetch(`/api/v1/auth/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (isSignup && response.status === 409) {
        setNotice({
          type: 'error',
          text: 'Un compte existe déjà avec cette adresse e-mail.',
        })
        return
      }

      const expectedStatus = isSignup ? 201 : 200

      if (response.status !== expectedStatus) {
        const body = await response.json().catch(() => null)
        const text = typeof body?.detail === 'string'
          ? body.detail
          : response.status === 422
            ? 'Vérifie les champs et réessaie.'
            : 'Une erreur est survenue. Réessaie dans un instant.'

        setNotice({ type: 'error', text })
        return
      }

      if (isSignup) {
        setEmail(payload.email)
        setMode('login')
        setNotice({
          type: 'success',
          text: 'Ton compte a été créé. Tu peux maintenant te connecter.',
        })
      } else {
        const user = await response.json()
        onLogin(user)
      }
    } catch {
      setNotice({
        type: 'error',
        text: 'Impossible de joindre le serveur. Réessaie dans un instant.',
      })
    } finally {
      setPending(false)
    }
  }

  return (
    <dialog
      ref={dialog}
      className="auth-dialog"
      aria-labelledby="auth-title"
      onCancel={(event) => {
        event.preventDefault()
        if (!pending) onClose()
      }}
    >
      <div className="auth-heading">
        <h2 id="auth-title">
          {isSignup ? 'Créer un compte' : 'Se connecter'}
        </h2>

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

      <div className="auth-switch" role="group" aria-label="Accès au compte">
        <button
          type="button"
          aria-pressed={!isSignup}
          onClick={() => changeMode('login')}
          disabled={pending}
        >
          Connexion
        </button>

        <button
          type="button"
          aria-pressed={isSignup}
          onClick={() => changeMode('signup')}
          disabled={pending}
        >
          Inscription
        </button>
      </div>

      <form key={mode} className="auth-form" onSubmit={submit}>
        {isSignup && (
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

        <label>
          Mot de passe
          <input
            name="password"
            type="password"
            autoComplete={isSignup ? 'new-password' : 'current-password'}
            minLength={isSignup ? 12 : undefined}
            maxLength={128}
            aria-describedby={isSignup ? 'password-hint' : undefined}
            readOnly={pending}
            required
          />
        </label>

        {isSignup && <small id="password-hint">Au moins 12 caractères.</small>}

        <button type="submit" disabled={pending}>
          {pending ? 'Patiente…' : isSignup ? 'Créer mon compte' : 'Se connecter'}
        </button>
      </form>

      {notice && (
        <p
          className={`auth-notice auth-notice--${notice.type}`}
          role={notice.type === 'error' ? 'alert' : 'status'}
        >
          {notice.text}
        </p>
      )}
    </dialog>
  )
}

export default AuthDialog