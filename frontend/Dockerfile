FROM node:20-alpine AS builder

WORKDIR /app
COPY frontend/package.json .
RUN npm install

COPY frontend/src/ ./src/
COPY frontend/index.html frontend/vite.config.ts frontend/tsconfig.json frontend/tsconfig.node.json ./
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx-default.conf /etc/nginx/conf.d/default.conf
