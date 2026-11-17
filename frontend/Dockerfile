# Étape 1 : compilation de l'application React (Vite).
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Étape 2 : nginx sert les fichiers statiques et relaie /api vers FastAPI.
# Image finale ~50 Mo (contre ~300 Mo pour le serveur de dev Vite).
FROM nginx:stable-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
