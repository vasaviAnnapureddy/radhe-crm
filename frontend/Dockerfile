# Frontend image: build the React app, then serve it with nginx (which also forwards /api to the backend).
FROM node:22-alpine AS build
WORKDIR /app/frontend
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html
EXPOSE 80
