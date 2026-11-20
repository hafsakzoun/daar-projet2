// Appels au compte utilisateur, avec un message d'erreur lisible.
export async function postAuth(path, payload) {
  let response;
  try {
    response = await fetch(`/api/v1/auth/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    return { ok: false, status: 0, message: "Impossible de joindre le serveur. Réessaie dans un instant." };
  }

  const body = await response.json().catch(() => null);
  const message =
    typeof body?.detail === "string"
      ? body.detail
      : response.status === 422
        ? "Vérifie les champs et réessaie."
        : "Une erreur est survenue. Réessaie dans un instant.";
  return { ok: response.ok, status: response.status, body, message };
}
