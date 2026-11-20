# Déploiement sur Kubernetes

Les manifestes sont dans [`k8s/`](../k8s), assemblés par Kustomize. Ils
reproduisent la chaîne de Docker Compose, avec en plus la réplication, la
répartition de charge, l'autoréparation et la mise à l'échelle automatique.

## Architecture

```
                     NodePort 30080
                          │
                ┌─────────▼─────────┐
                │ Service frontend  │  répartit entre les répliques
                └─────────┬─────────┘
          ┌───────────────┴───────────────┐
   ┌──────▼──────┐                 ┌──────▼──────┐
   │ frontend #1 │  nginx + React  │ frontend #2 │
   └──────┬──────┘                 └──────┬──────┘
          └──────────── /api ─────────────┘
                          │
                ┌─────────▼─────────┐
                │  Service backend  │
                └─────────┬─────────┘
          ┌───────────────┴───────────────┐       HPA : 2 → 4 répliques
   ┌──────▼──────┐                 ┌──────▼──────┐     selon le CPU
   │ backend #1  │     FastAPI     │ backend #2  │
   └──────┬──────┘                 └──────┬──────┘
          │       lecture des textes      │
          │      ┌──────────────────┐     │
          ├──────► PVC corpus (3 Go)◄─────┤
          │      └────────▲─────────┘     │
          │               │ écrit         │
          │      ┌────────┴─────────┐     │
          │      │ Job lisiere-init │     │
          │      │ corpus → index → │     │
          │      │      graphe      │     │
          │      └────────┬─────────┘     │
          └───────────────┼───────────────┘
                ┌─────────▼─────────┐
                │ StatefulSet db    │  PostgreSQL + PVC 4 Go
                └───────────────────┘
```

| Ressource | Rôle |
|---|---|
| `StatefulSet db` + Service headless | PostgreSQL avec un volume persistant, nom DNS stable `db` |
| `PersistentVolumeClaim corpus` | Textes des 1 700 livres |
| `Job lisiere-init` | Étapes successives (initContainers) : attente de la base, téléchargement et vérification du corpus, index inversé ; conteneur final : graphe de Jaccard et PageRank. Chaque étape passe son tour si son résultat existe déjà. |
| `Deployment backend` (2 répliques) | API FastAPI. Un initContainer `wait-data` retient le pod tant que l'index et le graphe ne sont pas prêts. Sondes de disponibilité et de vie sur `/api/v1/health`. |
| `Deployment frontend` (2 répliques) | nginx + React, relaie `/api` vers le Service `backend` |
| `HorizontalPodAutoscaler backend` | 2 à 4 répliques, cible 70 % de CPU |
| `ConfigMap` / `Secret` | Paramètres de connexion et du graphe ; mot de passe de la base |

## Lancer sur minikube

```bash
minikube start --driver=docker --memory=2600 --cpus=4
minikube addons enable metrics-server        # pour l'HPA

docker compose build backend frontend
minikube image load lisiere-backend:latest
minikube image load lisiere-frontend:latest

kubectl apply -k k8s/
kubectl -n lisiere wait --for=condition=complete job/lisiere-init --timeout=3h
kubectl -n lisiere get pods
```

Le premier lancement indexe les 1 700 livres (~30 min). Ensuite, l'application est
accessible avec :

```bash
minikube service frontend -n lisiere
```

Pour la démonstration sur plusieurs appareils du même réseau :

```bash
kubectl -n lisiere port-forward --address 0.0.0.0 service/frontend 8080:80
```

puis ouvrir `http://<IP-du-Mac>:8080` sur les autres machines.

## Secrets

- `lisiere-db` (mot de passe PostgreSQL) est généré par Kustomize.
- `lisiere-smtp` (envoi d'e-mails) est **facultatif** et créé à la main, hors du dépôt :

```bash
kubectl -n lisiere create secret generic lisiere-smtp \
  --from-literal=SMTP_HOST=smtp.gmail.com \
  --from-literal=SMTP_USER=adresse@gmail.com \
  --from-file=SMTP_PASSWORD=secrets/smtp_password.txt
kubectl -n lisiere rollout restart deployment/backend
```

## Démonstrations utiles

```bash
# Autoréparation : le pod supprimé est recréé, le service reste disponible.
kubectl -n lisiere delete pod -l app=backend --wait=false
kubectl -n lisiere get pods -w

# Mise à l'échelle manuelle
kubectl -n lisiere scale deployment/frontend --replicas=3

# État de la mise à l'échelle automatique
kubectl -n lisiere get hpa
```

## Avec les images de la CI

Le pipeline GitLab publie les images dans le registre du projet. Pour les
utiliser à la place des images locales :

```bash
cd k8s
kustomize edit set image lisiere-backend=registry.gitlab.com/<projet>/backend:<sha>
kustomize edit set image lisiere-frontend=registry.gitlab.com/<projet>/frontend:<sha>
```

Le job `k8s_manifests` du pipeline valide les manifestes à chaque commit
(rendu Kustomize puis `kubeconform -strict`).

## Limites

- Le mot de passe de démonstration est dans `kustomization.yaml` (comme la
  valeur par défaut de `compose.yaml`). En production, créer le Secret hors du
  dépôt.
- Le volume `corpus` est en `ReadWriteOnce` : toutes les répliques du backend
  doivent tourner sur le même nœud, ce qui est le cas d'un cluster minikube.
  Sur un cluster à plusieurs nœuds, il faudrait un stockage `ReadWriteMany`
  (NFS, EFS…) ou stocker les textes dans un service d'objets.
- PostgreSQL n'est pas répliqué (une seule instance).
