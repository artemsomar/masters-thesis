# syntax=docker/dockerfile:1

FROM node:24.12.0-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL=
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

FROM nginxinc/nginx-unprivileged:1.28-alpine AS runtime

COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --chown=nginx:nginx --from=build /app/dist /usr/share/nginx/html

ENV API_HOST=host.docker.internal
ENV API_PORT=8000

EXPOSE 8080
