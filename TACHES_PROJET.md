# DAAR — Backlog du projet de recherche de livres

## État actuel — novembre 2026

Le projet utilise désormais **PostgreSQL**, et non SQLite.

**Validé :**
- Docker Compose, PostgreSQL et volumes persistants.
- Installation des 1 700 livres sur un environnement neuf.
- Indexation des 1 700 livres et reprise après interruption.
- Démarrage FastAPI et React ; catalogue réel affiché.
- 37 tests Python réussis dans GitLab CI.
- Jobs `backend_tests` et `frontend_build` validés.

**Restant à finaliser :**
- Interface de recherche React.
- Jaccard, graphe, PageRank et recommandations.
- Vérifications fonctionnelles et performances.
- Intégration des branches, accès Git, rapport et livraison.

Les sections détaillées suivantes conservent les critères du plan initial.
Certaines mentions de SQLite, chemins et scripts historiques ne décrivent
plus l'implémentation actuelle.

---



Document à placer à la racine du dépôt : `TACHES_PROJET.md`.
Organisation proposée à partir des éléments fournis, sans audit du code actuel.
Les objectifs de 1 664 livres et 10 000 mots minimum par livre sont repris du plan fourni ; à confronter au sujet officiel.

## Validation P1 du 9 novembre 2026

Les résultats complets sont disponibles dans
[docs/VALIDATION_P1.md](docs/VALIDATION_P1.md).

- **DAAR-005 — En cours** : installation et vérification du corpus
  opérationnelles ; téléchargement HTTP partiel non reprenable.
- **DAAR-006 — En cours** : 1 700 livres cohérents entre manifeste,
  PostgreSQL et fichiers ; 0 empreinte incorrecte, 0 doublon exact.
  Méthode de nettoyage restant à documenter.
- **DAAR-011 — En cours de finalisation** : recherche simple,
  pagination, résultats vides et fréquences SQL vérifiés.
- **DAAR-012 — En cours de finalisation** : regex, erreurs HTTP 400
  et scores SQL vérifiés.
- **DAAR-020 — En cours** : premières mesures de performances réalisées.
  Moyennes : 29,00 ms pour la recherche simple et 314,23 ms
  pour la recherche regex.
- **DAAR-022 — En cours** : trace technique produite,
  rapport final restant à rédiger.

---

## Équipe et fonctionnement

| Rôle | Responsable | Périmètre principal |
|---|---|---|
| P1 | Oum | Corpus, SQLite, index et recherche |
| P2 | Hafsa| React, graphe, PageRank et recommandations |

Chaque ticket a un seul responsable. L’autre personne relit et valide la PR.
Les choix communs sont discutés ensemble, puis consignés par le responsable du ticket.
Les attributions sont proposées et peuvent être adaptées à votre disponibilité.

- Statuts : À faire → En cours → En revue → Terminé ; Bloqué si une dépendance manque.
- Priorités : P0 = nécessaire pour démarrer ; P1 = fonctionnalité principale ; P2 = évaluation et livraison.
- Estimations : points relatifs (1, 2, 3, 5, 8), sans engagement de durée.
- Limite : un ticket de développement en cours par personne.
- Branche : `feat/DAAR-XXX-description` ; PR citant le ticket.
- Terminé : critères cochés, vérification effectuée, documentation adaptée et PR relue.
- Le tableau de suivi indique les statuts actualisés. Les descriptions détaillées ci-dessous proviennent du plan initial et doivent être adaptées à l'architecture actuelle.

## Jalons

| Jalon | Résultat attendu |
|---|---|
| M0 — Socle | Dépôt partagé, stockage Docker, conventions et contrat API |
| M1 — Première chaîne | 20 livres conformes importés dans SQLite et affichés dans React |
| M2 — Recherche | Recherche simple et regex intégrées et vérifiées |
| M3 — Graphe | Jaccard, PageRank, classement et recommandations vérifiés |
| M4 — Corpus complet | Au moins 1 664 livres conformes, application utilisable |
| M5 — Livraison | Évaluation, rapport, README et démonstration reproductible |

M1 doit être validé avant d’augmenter le corpus. P2 peut développer l’interface avec des données simulées pendant la préparation du corpus.

## Tableau de suivi

| Ticket | Epic | Résumé | Responsable | Priorité | Points | Dépendances | Jalon | Statut |
|---|---|---|---|---|---|---|---|---|
| DAAR-001 | Socle | Partager le dépôt GitHub | P1 | P0 | 2 | Aucune | M0 | Terminé |
| DAAR-002 | Socle | Préparer le stockage persistant | P1 | P0 | 2 | 001 | M0 | Terminé |
| DAAR-003 | Socle | Fixer le contrat API et les règles communes | P2 | P0 | 3 | 001 | M0 | En cours |
| DAAR-004 | Corpus | Sélectionner les sources et 20 livres pilotes | P1 | P0 | 2 | 003 | M1 | Terminé |
| DAAR-005 | Corpus | Développer un téléchargement reprenable | P1 | P1 | 5 | 002, 004 | M1 | En cours |
| DAAR-006 | Corpus | Nettoyer, contrôler et produire le manifeste | P1 | P1 | 5 | 005 | M1 | En cours |
| DAAR-007 | Corpus | Importer le catalogue dans SQLite | P1 | P1 | 3 | 006 | M1 | Terminé |
| DAAR-008 | API | Exposer le catalogue FastAPI | P1 | P1 | 3 | 003, 007 | M1 | Terminé |
| DAAR-009 | Interface | Construire le catalogue et les états d’affichage | P2 | P1 | 5 | 003 | M1 | En cours |
| DAAR-010 | Recherche | Construire l’index inversé | P1 | P1 | 5 | 006, 003 | M2 | Terminé |
| DAAR-011 | Recherche | Implémenter la recherche simple et son classement | P1 | P1 | 3 | 008, 010 | M2 | En cours |
| DAAR-012 | Recherche | Implémenter la recherche regex | P1 | P1 | 5 | 010, 011 | M2 | En cours |
| DAAR-013 | Interface | Créer le formulaire de recherche et les résultats | P2 | P1 | 5 | 009, 003 | M2 | À faire |
| DAAR-014 | Graphe | Construire les similarités de Jaccard | P2 | P1 | 5 | 006, 003 | M3 | À faire |
| DAAR-015 | Graphe | Calculer et vérifier PageRank | P2 | P1 | 5 | 014 | M3 | À faire |
| DAAR-016 | Recommandation | Créer la route de livres similaires | P2 | P1 | 3 | 008, 014 | M3 | À faire |
| DAAR-017 | Intégration | Ajouter les scores et le tri PageRank | P1 | P1 | 3 | 011, 012, 015 | M3 | À faire |
| DAAR-018 | Interface | Afficher les recommandations et terminer l’intégration | P2 | P1 | 3 | 013, 016, 017 | M3 | À faire |
| DAAR-019 | Corpus | Passer au corpus complet | P1 | P1 | 5 | 007, 010, 014, 015, 018 | M4 | En cours |
| DAAR-020 | Qualité | Vérifier l’exactitude et mesurer les performances | P1 | P2 | 5 | 019, 017 | M5 | En cours |
| DAAR-021 | Qualité | Évaluer la pertinence et produire les graphiques | P2 | P2 | 5 | 019, 018, 020 | M5 | À faire |
| DAAR-022 | Livraison | Documenter le backend et la reproduction du corpus | P1 | P2 | 3 | 020 | M5 | En cours |
| DAAR-023 | Livraison | Finaliser rapport, archive et démonstration | P2 | P2 | 3 | 021, 022 | M5 | À faire |

## Tickets détaillés

### DAAR-001 — Partager le dépôt GitHub

**Epic :** Socle · **Responsable :** P1 · **Priorité :** P0 · **Estimation :** 2 points  
**Statut :** À faire · **Dépendances :** Aucune · **Jalon :** M0

**Travail à réaliser**

- [ ] Créer ou retrouver le dépôt distant et vérifier son URL exacte.
- [ ] Pousser la branche main ; vérifier requirements.txt, Dockerfiles, compose.yaml et lockfile npm.
- [ ] Exclure les environnements locaux, secrets et données générées ; retirer les fichiers déjà suivis si nécessaire.
- [ ] Ajouter le binôme et documenter le fonctionnement par branches et PR.

**Critères d’acceptation**

- [ ] Le binôme peut cloner le dépôt et accéder aux sources.
- [ ] Aucun .venv, node_modules ou secret n’est suivi.
- [ ] Le dépôt contient les fichiers nécessaires à la construction Docker.

### DAAR-002 — Préparer le stockage persistant

**Epic :** Socle · **Responsable :** P1 · **Priorité :** P0 · **Estimation :** 2 points  
**Statut :** À faire · **Dépendances :** 001 · **Jalon :** M0

**Travail à réaliser**

- [ ] Créer data/raw, data/processed, data/metadata, data/generated et backend/scripts.
- [ ] Conserver ./backend:/app et ajouter ./data:/data au service backend.
- [ ] Définir DATA_DIR=/data dans Docker et un chemin configurable pour l’exécution locale.
- [ ] Ignorer raw, processed et generated dans Git ; conserver des .gitkeep si nécessaire et versionner le manifeste.

**Critères d’acceptation**

- [ ] Un fichier de data est lisible depuis /data dans le backend.
- [ ] Les données restent présentes après docker compose down puis redémarrage.
- [ ] Les chemins ne dépendent pas d’un répertoire personnel du Mac.

### DAAR-003 — Fixer le contrat API et les règles communes

**Epic :** Socle · **Responsable :** P2 · **Priorité :** P0 · **Estimation :** 3 points  
**Statut :** À faire · **Dépendances :** 001 · **Jalon :** M0

**Travail à réaliser**

- [ ] Rédiger docs/api-contract.md et faire valider les choix par P1.
- [ ] Définir les routes, champs, types, pagination, tris et erreurs détaillés en annexe.
- [ ] Décider ensemble : langue, normalisation, sens d’occurrences, sémantique regex et construction du graphe.
- [ ] Définir des réponses JSON simulées et l’adaptation de l’ancien React si /books renvoie maintenant un objet paginé.

**Critères d’acceptation**

- [ ] P1 et P2 utilisent les mêmes exemples JSON.
- [ ] Recherche vide, regex invalide, livre inconnu et tri non autorisé ont un comportement défini.
- [ ] Les règles de tokenisation et de classement sont écrites.

### DAAR-004 — Sélectionner les sources et 20 livres pilotes

**Epic :** Corpus · **Responsable :** P1 · **Priorité :** P0 · **Estimation :** 2 points  
**Statut :** À faire · **Dépendances :** 003 · **Jalon :** M1

**Travail à réaliser**

- [ ] Choisir une langue et une source autorisant la récupération et l’usage prévu.
- [ ] Vérifier les modalités de téléchargement et préparer une liste d’identifiants et d’URL.
- [ ] Prévoir des candidats supplémentaires pour remplacer les textes trop courts ou en doublon.
- [ ] Consigner source, langue, provenance et conditions d’utilisation.

**Critères d’acceptation**

- [ ] 20 livres acceptables peuvent être obtenus sans créer de doublons.
- [ ] La source et la méthode de sélection sont documentées.

### DAAR-005 — Développer un téléchargement reprenable

**Epic :** Corpus · **Responsable :** P1 · **Priorité :** P1 · **Estimation :** 5 points  
**Statut :** À faire · **Dépendances :** 002, 004 · **Jalon :** M1

**Travail à réaliser**

- [ ] Créer backend/scripts/download_books.py avec une sélection ou une limite en argument.
- [ ] Enregistrer les textes dans raw avec identifiants stables et encodage connu.
- [ ] Ajouter délais, reprises limitées, gestion des erreurs réseau et écriture atomique.
- [ ] Ne pas retélécharger un fichier déjà complet ; journaliser les échecs pour relance.

**Critères d’acceptation**

- [ ] Une relance ne duplique pas les livres ni les téléchargements réussis.
- [ ] Une interruption permet de reprendre.
- [ ] Les échecs sont identifiables sans bloquer tout le lot.

### DAAR-006 — Nettoyer, contrôler et produire le manifeste

**Epic :** Corpus · **Responsable :** P1 · **Priorité :** P1 · **Estimation :** 5 points  
**Statut :** À faire · **Dépendances :** 005 · **Jalon :** M1

**Travail à réaliser**

- [ ] Créer backend/scripts/prepare_corpus.py ; garder les originaux intacts.
- [ ] Retirer les en-têtes et pieds de page selon les marqueurs de la source ; signaler les cas ambigus.
- [ ] Uniformiser l’encodage et compter les mots après nettoyage selon la règle convenue.
- [ ] Rejeter les livres de moins de 10 000 mots et détecter les doublons par identifiant et empreinte du texte nettoyé.
- [ ] Écrire processed, metadata/manifest.json et un bilan accepté/rejeté avec motifs ; utiliser des chemins relatifs.

**Critères d’acceptation**

- [ ] 20 livres distincts et conformes figurent dans le manifeste.
- [ ] Chaque entrée contient id, title, author, language, source_url, chemins, word_count et empreinte.
- [ ] Le même lot relancé donne un résultat stable ; quelques nettoyages sont vérifiés manuellement.

### DAAR-007 — Importer le catalogue dans SQLite

**Epic :** Corpus · **Responsable :** P1 · **Priorité :** P1 · **Estimation :** 3 points  
**Statut :** À faire · **Dépendances :** 006 · **Jalon :** M1

**Travail à réaliser**

- [ ] Créer le schéma et backend/scripts/import_catalog.py.
- [ ] Placer la base dans data/generated/catalog.sqlite ; utiliser une transaction et des identifiants uniques.
- [ ] Importer les métadonnées et références aux textes, avec mises à jour sans doublons.
- [ ] Documenter la commande de reconstruction à partir du manifeste.

**Critères d’acceptation**

- [ ] Le nombre de lignes correspond aux livres acceptés.
- [ ] Deux imports successifs ne créent pas de doublons.
- [ ] La base est reconstruisible à partir des fichiers et du manifeste.

### DAAR-008 — Exposer le catalogue FastAPI

**Epic :** API · **Responsable :** P1 · **Priorité :** P1 · **Estimation :** 3 points  
**Statut :** À faire · **Dépendances :** 003, 007 · **Jalon :** M1

**Travail à réaliser**

- [ ] Implémenter GET /health, GET /books et GET /books/{id}.
- [ ] Ajouter pagination, validation des paramètres et réponse 404 pour un identifiant absent.
- [ ] Renvoyer les données SQLite, sans chemins internes ni contenu arbitraire du système de fichiers.
- [ ] Adapter CORS aux adresses du frontend local.

**Critères d’acceptation**

- [ ] Le catalogue paginé et les fiches proviennent de SQLite.
- [ ] Les paramètres invalides et livres absents produisent les erreurs convenues.
- [ ] Les routes sont utilisables dans /docs et depuis React.

### DAAR-009 — Construire le catalogue et les états d’affichage

**Epic :** Interface · **Responsable :** P2 · **Priorité :** P1 · **Estimation :** 5 points  
**Statut :** À faire · **Dépendances :** 003 · **Jalon :** M1

**Travail à réaliser**

- [ ] Remplacer la page Vite par une interface bibliothèque.
- [ ] Créer catalogue, pagination et fiche livre ; commencer avec les réponses simulées.
- [ ] Prévoir chargement, erreur, liste vide, navigation et affichage lisible.
- [ ] Centraliser l’URL de l’API et un adaptateur de données ; connecter les routes réelles quand 008 est prêt.

**Critères d’acceptation**

- [ ] Le catalogue fonctionne d’abord avec les mocks, puis avec les 20 livres réels.
- [ ] Une API inaccessible affiche un message compréhensible.
- [ ] Les boutons et formulaires sont utilisables au clavier.

### DAAR-010 — Construire l’index inversé

**Epic :** Recherche · **Responsable :** P1 · **Priorité :** P1 · **Estimation :** 5 points  
**Statut :** À faire · **Dépendances :** 006, 003 · **Jalon :** M2

**Travail à réaliser**

- [ ] Créer backend/scripts/build_index.py et un module de normalisation partagé.
- [ ] Indexer terme → livres et fréquences ; stocker les informations nécessaires au sens d’occurrences choisi.
- [ ] Versionner le format et conserver une empreinte du corpus et des règles pour détecter un index périmé.
- [ ] Enregistrer l’index dans generated ; ne pas le recalculer au démarrage de FastAPI.

**Critères d’acceptation**

- [ ] Les termes et fréquences correspondent à un petit exemple vérifié à la main.
- [ ] La normalisation est identique à l’indexation et à la recherche.
- [ ] L’index peut être rechargé et son absence ou obsolescence est signalée.

### DAAR-011 — Implémenter la recherche simple et son classement

**Epic :** Recherche · **Responsable :** P1 · **Priorité :** P1 · **Estimation :** 3 points  
**Statut :** À faire · **Dépendances :** 008, 010 · **Jalon :** M2

**Travail à réaliser**

- [ ] Implémenter GET /search en mode keyword avec l’index.
- [ ] Appliquer la sémantique convenue pour un ou plusieurs termes.
- [ ] Classer par occurrences décroissantes avec un départage stable par id.
- [ ] Paginer les résultats et exposer le total avant pagination.

**Critères d’acceptation**

- [ ] Les livres et occurrences concordent avec une lecture directe sur un jeu connu.
- [ ] Une requête sans résultat renvoie total=0 et results=[].
- [ ] Le classement et la pagination sont déterministes.

### DAAR-012 — Implémenter la recherche regex

**Epic :** Recherche · **Responsable :** P1 · **Priorité :** P1 · **Estimation :** 5 points  
**Statut :** À faire · **Dépendances :** 010, 011 · **Jalon :** M2

**Travail à réaliser**

- [ ] Définir les constructions regex supportées selon le sujet officiel et réutiliser les algorithmes imposés le cas échéant.
- [ ] Appliquer les regex aux termes de l’index ou aux textes selon la sémantique validée dans 003 ; expliquer les limites.
- [ ] Valider les expressions et limiter le coût des requêtes pour éviter de bloquer le serveur.
- [ ] Calculer les occurrences selon cette sémantique et conserver le format de résultats commun.

**Critères d’acceptation**

- [ ] Des expressions simples, alternatives et répétitions donnent les résultats attendus.
- [ ] Une regex invalide produit une erreur explicite sans erreur serveur.
- [ ] Les résultats concordent avec la méthode de référence choisie.

### DAAR-013 — Créer le formulaire de recherche et les résultats

**Epic :** Interface · **Responsable :** P2 · **Priorité :** P1 · **Estimation :** 5 points  
**Statut :** À faire · **Dépendances :** 009, 003 · **Jalon :** M2

**Travail à réaliser**

- [ ] Ajouter champ de requête, choix keyword/regex et tri occurrences/pagerank.
- [ ] Afficher nombre total, résultats paginés et scores avec libellés compréhensibles.
- [ ] Prévoir saisie vide, aucun résultat, erreur regex et attente réseau ; annuler les réponses obsolètes.
- [ ] Développer avec mocks puis brancher 011 et 012 ; activer le tri PageRank après 017.

**Critères d’acceptation**

- [ ] La recherche simple et regex fonctionne depuis l’interface avec l’API réelle.
- [ ] Un changement de requête ne laisse pas apparaître les anciens résultats.
- [ ] Le tri PageRank n’est proposé comme disponible que lorsque les scores existent.

### DAAR-014 — Construire les similarités de Jaccard

**Epic :** Graphe · **Responsable :** P2 · **Priorité :** P1 · **Estimation :** 5 points  
**Statut :** À faire · **Dépendances :** 006, 003 · **Jalon :** M3

**Travail à réaliser**

- [ ] Créer backend/scripts/build_graph.py en réutilisant la normalisation commune.
- [ ] Définir la représentation des livres, les mots exclus éventuels et le seuil d’arête.
- [ ] Calculer J(A,B)=|A∩B|/|A∪B| et définir le cas de deux ensembles vides.
- [ ] Construire un graphe sans boucles, sans doublons et persister paramètres, poids et identifiants.
- [ ] Mesurer le coût du calcul par paires avant le passage au corpus complet.

**Critères d’acceptation**

- [ ] Les similarités d’un petit corpus concordent avec un calcul manuel.
- [ ] Les scores sont symétriques et compris entre 0 et 1.
- [ ] Le graphe est reproductible pour un même corpus et les mêmes paramètres.

### DAAR-015 — Calculer et vérifier PageRank

**Epic :** Graphe · **Responsable :** P2 · **Priorité :** P1 · **Estimation :** 5 points  
**Statut :** À faire · **Dépendances :** 014 · **Jalon :** M3

**Travail à réaliser**

- [ ] Créer backend/scripts/compute_pagerank.py.
- [ ] Fixer facteur d’amortissement, tolérance, nombre maximal d’itérations et usage des poids.
- [ ] Traiter les sommets isolés et sans sortie ; consigner la convergence.
- [ ] Persister les scores par id de livre et l’empreinte du graphe utilisé.

**Critères d’acceptation**

- [ ] Les scores sont non négatifs et leur somme est proche de 1.
- [ ] Un petit graphe connu produit un résultat cohérent avec une référence.
- [ ] L’absence de convergence est signalée ; tous les livres ont un score défini.

### DAAR-016 — Créer la route de livres similaires

**Epic :** Recommandation · **Responsable :** P2 · **Priorité :** P1 · **Estimation :** 3 points  
**Statut :** À faire · **Dépendances :** 008, 014 · **Jalon :** M3

**Travail à réaliser**

- [ ] Implémenter GET /books/{id}/recommendations à partir du graphe.
- [ ] Exclure le livre demandé, classer par similarité et appliquer une limite.
- [ ] Définir le comportement sans voisin : liste vide ou stratégie documentée.
- [ ] Garder la logique de graphe dans un module distinct des routes de recherche de P1.

**Critères d’acceptation**

- [ ] Les recommandations sont distinctes et ne contiennent pas le livre source.
- [ ] similarity est fourni et l’ordre est stable.
- [ ] Livre inconnu et livre sans voisin sont correctement traités.

### DAAR-017 — Ajouter les scores et le tri PageRank

**Epic :** Intégration · **Responsable :** P1 · **Priorité :** P1 · **Estimation :** 3 points  
**Statut :** À faire · **Dépendances :** 011, 012, 015 · **Jalon :** M3

**Travail à réaliser**

- [ ] Charger les scores produits par P2 et les joindre par id aux résultats.
- [ ] Implémenter sort=pagerank sans modifier l’ensemble des livres correspondant à la requête.
- [ ] Définir un départage stable et une erreur explicite si les scores ne sont pas disponibles.
- [ ] Éviter les mélanges entre versions du corpus, de l’index et du graphe.

**Critères d’acceptation**

- [ ] Le tri change l’ordre, sans ajouter de livre ne correspondant pas à la recherche.
- [ ] Les scores API correspondent aux scores calculés.
- [ ] Des fichiers incompatibles ou manquants donnent un diagnostic exploitable.

### DAAR-018 — Afficher les recommandations et terminer l’intégration

**Epic :** Interface · **Responsable :** P2 · **Priorité :** P1 · **Estimation :** 3 points  
**Statut :** À faire · **Dépendances :** 013, 016, 017 · **Jalon :** M3

**Travail à réaliser**

- [ ] Ajouter les livres similaires à la fiche et rendre leur navigation possible.
- [ ] Afficher similarité et PageRank avec un format adapté.
- [ ] Vérifier recherche → fiche → recommandations → autre fiche.
- [ ] Tester l’affichage sur deux tailles d’écran et avec API indisponible.

**Critères d’acceptation**

- [ ] Le parcours complet fonctionne sans données simulées.
- [ ] Les états sans recommandation et les erreurs ne bloquent pas la navigation.
- [ ] Les classements affichés correspondent aux réponses API.

### DAAR-019 — Passer au corpus complet

**Epic :** Corpus · **Responsable :** P1 · **Priorité :** P1 · **Estimation :** 5 points  
**Statut :** À faire · **Dépendances :** 007, 010, 014, 015, 018 · **Jalon :** M4

**Travail à réaliser**

- [ ] Faire valider la chaîne sur 20 livres avant de lancer le lot complet.
- [ ] Collecter suffisamment de candidats pour obtenir au moins 1 664 livres acceptés.
- [ ] Régénérer catalogue, index, graphe et PageRank dans l’ordre ; P2 vérifie les sorties du graphe.
- [ ] Produire un bilan de conformité et conserver les versions et paramètres de génération.

**Critères d’acceptation**

- [ ] Au moins 1 664 livres uniques ont chacun au moins 10 000 mots après nettoyage.
- [ ] Manifeste, base, index et scores référencent les mêmes livres.
- [ ] Le corpus reste accessible après arrêt et redémarrage des conteneurs.

### DAAR-020 — Vérifier l’exactitude et mesurer les performances

**Epic :** Qualité · **Responsable :** P1 · **Priorité :** P2 · **Estimation :** 5 points  
**Statut :** À faire · **Dépendances :** 019, 017 · **Jalon :** M5

**Travail à réaliser**

- [ ] Préparer des cas de référence pour catalogue, fréquences, keyword et regex.
- [ ] Mesurer séparément téléchargement, préparation, indexation et temps de requête.
- [ ] Répéter les mesures sur plusieurs tailles disponibles avec mêmes requêtes et environnement consigné.
- [ ] Distinguer premiers accès et accès suivants ; enregistrer résultats bruts, moyenne, dispersion et mémoire si mesurable.

**Critères d’acceptation**

- [ ] Les résultats attendus sont vérifiés par une méthode indépendante.
- [ ] Les mesures sont répétées et leurs conditions sont reproductibles.
- [ ] Les limites et erreurs constatées sont consignées sans conclusions excessives.

### DAAR-021 — Évaluer la pertinence et produire les graphiques

**Epic :** Qualité · **Responsable :** P2 · **Priorité :** P2 · **Estimation :** 5 points  
**Statut :** À faire · **Dépendances :** 019, 018, 020 · **Jalon :** M5

**Travail à réaliser**

- [ ] Définir quelques requêtes et livres de référence avec jugements de pertinence documentés.
- [ ] Comparer classement par occurrences et par PageRank ; inspecter les recommandations.
- [ ] Choisir des métriques adaptées aux jugements disponibles, sans présenter une appréciation subjective comme une vérité générale.
- [ ] Créer graphiques à partir des mesures brutes et expliquer les compromis du seuil Jaccard.

**Critères d’acceptation**

- [ ] Les exemples et critères permettent de comprendre la pertinence obtenue.
- [ ] Les graphiques indiquent unités, corpus et conditions.
- [ ] Les conclusions distinguent qualité de recherche, popularité dans le graphe et vitesse.

### DAAR-022 — Documenter le backend et la reproduction du corpus

**Epic :** Livraison · **Responsable :** P1 · **Priorité :** P2 · **Estimation :** 3 points  
**Statut :** À faire · **Dépendances :** 020 · **Jalon :** M5

**Travail à réaliser**

- [ ] Rédiger les parties corpus, stockage, index, recherche et limites du rapport.
- [ ] Mettre à jour README : installation, Docker, génération des données et reconstruction.
- [ ] Fournir les commandes réelles et expliquer que docker compose up ne télécharge ni ne recalcule le corpus.
- [ ] Vérifier le lancement depuis un clone propre avec la procédure documentée.

**Critères d’acceptation**

- [ ] Une autre personne peut préparer les données et lancer l’application en suivant le README.
- [ ] Les dépendances et paramètres nécessaires sont listés.
- [ ] Les chiffres du rapport correspondent aux résultats enregistrés.

### DAAR-023 — Finaliser rapport, archive et démonstration

**Epic :** Livraison · **Responsable :** P2 · **Priorité :** P2 · **Estimation :** 3 points  
**Statut :** À faire · **Dépendances :** 021, 022 · **Jalon :** M5

**Travail à réaliser**

- [ ] Rédiger interface, graphe, PageRank, recommandations et évaluation ; harmoniser avec P1.
- [ ] Préparer l’archive attendue par le sujet sans environnements locaux ni secrets.
- [ ] Vérifier le scénario de démonstration avec deux clients, selon le mode de déploiement attendu.
- [ ] Relire le rapport avec P1 et figer une version de livraison avec les paramètres du corpus.

**Critères d’acceptation**

- [ ] README, rapport et application décrivent le même état final.
- [ ] L’archive contient tous les éléments requis ou leur méthode de récupération.
- [ ] Les deux personnes savent présenter et reproduire le parcours de démonstration.

## Contrat technique proposé — à valider dans DAAR-003

### Stockage

| Chemin | Contenu | Git |
|---|---|---|
| data/raw/ | Textes téléchargés | Non |
| data/processed/ | Textes nettoyés | Non |
| data/metadata/manifest.json | Provenance et métadonnées reproductibles | Oui |
| data/generated/ | SQLite, index, graphe et scores | Non |
| backend/scripts/ | Commandes de préparation | Oui |
| docs/ | Contrat API, conventions et résultats d’évaluation | Oui |

Le montage `./data:/data` est un bind mount : les données restent sur le Mac.
Conserver le montage `./backend:/app`. Ne pas utiliser de chemins absolus du Mac dans le manifeste.
Les commandes de téléchargement, nettoyage, import, indexation et graphe sont explicites et séparées du démarrage web.

### Routes et réponses

| Route | Fonction | Contrat proposé |
|---|---|---|
| GET /health | État du serveur | status et disponibilité des données |
| GET /books?offset=0&limit=20 | Catalogue | total, offset, limit, results |
| GET /books/{id} | Fiche | Un objet livre |
| GET /search?q=king&mode=keyword&sort=occurrences&offset=0&limit=20 | Recherche simple | Objet paginé de résultats |
| GET /search?q=king%7Cqueen&mode=regex&sort=pagerank&offset=0&limit=20 | Recherche regex | Même structure |
| GET /books/{id}/recommendations?limit=5 | Livres similaires | book_id et results avec similarity |

Proposition : id entier stable ; title et author chaînes ; occurrences entier ; pagerank nombre ou null avant calcul.
Un auteur inconnu est représenté de manière uniforme, par exemple « Auteur inconnu ».
Définir les bornes de pagination et les codes d’erreur dans le contrat.
Le seuil minimal de mots et la tokenisation doivent être identiques dans tous les scripts concernés.

Exemple de réponse de recherche :

```json
{
  "total": 1,
  "offset": 0,
  "limit": 20,
  "results": [
    {
      "id": 12,
      "title": "Titre du livre",
      "author": "Auteur",
      "occurrences": 84,
      "pagerank": 0.002
    }
  ]
}
```

Les recommandations utilisent ici leur route dédiée ; le champ recommendations du premier exemple n’est donc pas nécessaire dans /search.
Cette proposition doit être figée ensemble avant l’implémentation.

### Décisions à consigner

- Langue et source du corpus ; minimum de mots confirmé dans le sujet.
- Casse, accents, apostrophes, traits d’union, mots vides et définition d’un mot.
- Recherche multi-termes : ET, OU ou autre comportement.
- Regex : portée (termes ou texte), syntaxe supportée, sens des occurrences et limites de coût.
- Jaccard : ensembles retenus, seuil et traitement des ensembles vides.
- PageRank : graphe pondéré ou non, amortissement, convergence et sommets isolés.
- Démonstration sur deux clients : contexte exact et accès réseau prévu par le sujet.
- Versions du corpus et des fichiers générés garantissant leur compatibilité.

## Démarrage immédiat

1. P1 démarre DAAR-001 puis DAAR-002.
2. P2 prépare DAAR-003 ; P1 valide les décisions communes.
3. P1 enchaîne DAAR-004 à DAAR-008 ; P2 développe DAAR-009 avec les mocks.
4. Ensemble : vérifier que les 20 livres SQLite s’affichent dans React avant de poursuivre.

## Répartition et coordination

P1 : 13 tickets, 51 points. P2 : 10 tickets, 37 points.
La préparation du corpus charge davantage P1 : P2 peut reprendre DAAR-002 (2 points) et DAAR-020 (5 points) après accord, pour arriver à 44 points chacun.
Ces totaux servent à repérer la charge ; ils ne sont pas des durées garanties.
Réestimer après M1 et déplacer un ticket si nécessaire.

P1 est référent des routes catalogue/recherche et du stockage ; P2 est référent des modules graphe/recommandations et du frontend.
Éviter de modifier simultanément le même fichier : découper les routes en modules et convenir d’un responsable pour leur assemblage.
Chaque PR indique : ticket, comportement ajouté, vérification effectuée et éventuelle dépendance restante.

