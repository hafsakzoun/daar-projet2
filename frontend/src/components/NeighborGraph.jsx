import { useEffect, useState } from "react";

function initials(title) {
  return title.split(/\s+/).filter(Boolean).slice(0, 2).map((word) => word[0]).join("").toUpperCase();
}

function shortTitle(title) {
  return title.length > 22 ? `${title.slice(0, 21)}…` : title;
}

export default function NeighborGraph({ book }) {
  const [neighbors, setNeighbors] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch(`/api/v1/books/${book.id}/recommendations?limit=8`, { signal: controller.signal });
        const body = await response.json();
        if (!response.ok) throw new Error("Les livres voisins sont indisponibles pour le moment.");
        if (!controller.signal.aborted) setNeighbors(body.results);
      } catch (err) {
        if (!controller.signal.aborted) setError(err instanceof TypeError ? "Le serveur est indisponible." : err.message);
      }
    }
    load();
    return () => controller.abort();
  }, [book.id]);

  if (error) return <p role="alert">{error}</p>;
  if (neighbors === null) return <p role="status">Chargement du graphe…</p>;
  if (neighbors.length === 0) return <p>Aucun voisin de Jaccard disponible pour ce livre.</p>;

  const nodes = neighbors.map((neighbor, index) => {
    const score = Math.max(0, Math.min(1, neighbor.similarity));
    const angle = -Math.PI / 2 + index * 2 * Math.PI / neighbors.length;
    const radius = 90 + (1 - score) * 100;
    return { ...neighbor, score, x: 360 + Math.cos(angle) * radius, y: 240 + Math.sin(angle) * radius };
  });

  return (
    <div className="neighbor-graph">
      <p className="neighbor-graph-intro">
        Graphe de Jaccard : plus un livre est proche du centre et relié par un
        trait épais, plus son vocabulaire ressemble à celui-ci. Cliquez sur un
        nœud pour le lire.
      </p>
      <div className="neighbor-graph-canvas">
        <svg viewBox="0 0 720 480" aria-label={`Voisins de ${book.title}`}>
          {nodes.map((node) => <line key={node.id} x1="360" y1="240" x2={node.x} y2={node.y} strokeWidth={1 + node.score * 8} className="neighbor-graph-edge" />)}
          <g className="neighbor-graph-center">
            <title>{book.title} — livre ouvert</title>
            <circle cx="360" cy="240" r="34" />
            <text x="360" y="245" textAnchor="middle">{initials(book.title)}</text>
            <text x="360" y="294" textAnchor="middle" className="neighbor-graph-center-label">Livre ouvert</text>
          </g>
          {nodes.map((node) => {
            const centered = Math.abs(node.x - 360) < 20;
            const side = node.x >= 360 ? 1 : -1;
            const labelX = centered ? node.x : node.x + side * 32;
            const labelY = centered ? node.y + (node.y < 240 ? -42 : 43) : node.y - 4;
            return (
              <a key={node.id} href={`#/livre/${node.id}`} className={`neighbor-graph-node neighbor-graph-node--${node.id % 5}`} aria-label={`Lire ${node.title}, similarité ${Math.round(node.score * 100)} %`}>
                <title>{node.title} — {Math.round(node.score * 100)} % de similarité de Jaccard</title>
                <circle cx={node.x} cy={node.y} r="24" />
                <text x={node.x} y={node.y + 5} textAnchor="middle" className="neighbor-graph-initials">{initials(node.title)}</text>
                <text x={labelX} y={labelY} textAnchor={centered ? "middle" : side > 0 ? "start" : "end"} className="neighbor-graph-label">{shortTitle(node.title)}</text>
                <text x={labelX} y={labelY + 18} textAnchor={centered ? "middle" : side > 0 ? "start" : "end"} className="neighbor-graph-score">{Math.round(node.score * 100)} %</text>
              </a>
            );
          })}
        </svg>
      </div>
      <ol className="neighbor-graph-list" aria-label="Livres voisins par similarité décroissante">
        {neighbors.map((neighbor) => (
          <li key={neighbor.id}>
            <a href={`#/livre/${neighbor.id}`}>{neighbor.title}</a>
            <span>{Math.round(neighbor.similarity * 100)} %</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
