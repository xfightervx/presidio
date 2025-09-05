FROM node:20-alpine AS builder
WORKDIR /web

COPY gdpr-dashboard/package.json gdpr-dashboard/package-lock.json ./
RUN npm ci

COPY gdpr-dashboard ./
RUN npm run build


FROM nginx:alpine AS runner
WORKDIR /usr/share/nginx/html
COPY --from=builder /web/dist ./


COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
