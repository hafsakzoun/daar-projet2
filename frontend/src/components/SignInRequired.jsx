export default function SignInRequired({ onLogin, checking }) {
  return (
    <section className="page">
      <header className="page-head">
        <h1>Connexion requise</h1>
        <p>
          {checking
            ? "Vérification de la session…"
            : "Connecte-toi pour retrouver tes favoris et ton historique."}
        </p>
      </header>
      {!checking && (
        <button type="button" className="btn btn--primary" onClick={onLogin}>
          Se connecter
        </button>
      )}
    </section>
  );
}
