---
name: nginx-proxy
description: >
  Use para configurar proxy reverso nginx: upstreams, load balancing,
  SSL/TLS, rate limiting, headers de segurança, compressão gzip,
  SPA fallback e proxy pass para APIs.
---

# nginx-proxy

Configuração de proxy reverso com nginx.

## Quando usar

- Servir múltiplas aplicações na mesma porta (80/443).
- Terminar SSL/TLS antes dos backends.
- Aplicar rate limiting, compressão e headers de segurança centralizados.
- Fazer fallback de SPA (React/Vite) para `index.html`.

## Padrões principais

### Upstreams e load balancing

```nginx
upstream api_backend {
    server api:8000 weight=3;
    server api2:8000;
    keepalive 32;
}
```

### Proxy pass para APIs

```nginx
location /api/ {
    proxy_pass http://api_backend/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### SPA fallback

```nginx
location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;
}
```

### SSL/TLS

```nginx
server {
    listen 443 ssl http2;
    server_name app.exemplo.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### Redirect HTTP → HTTPS

```nginx
server {
    listen 80;
    server_name app.exemplo.com;
    return 301 https://$host$request_uri;
}
```

### Rate limiting

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://api_backend/;
    }
}
```

### Headers de segurança

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### Compressão gzip

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml;
gzip_min_length 1024;
```

### Logs formatados

```nginx
log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                '$status $body_bytes_sent "$http_referer" '
                '"$http_user_agent" "$http_x_forwarded_for"';

access_log /var/log/nginx/access.log main;
```

## Anti-patterns

- `proxy_pass` sem trailing slash causando duplicação de path (`/api//v1`).
- Rate limit sem `zone` definido → nginx não inicia.
- `ssl_protocols TLSv1 TLSv1.1` (obsoleto/inseguro).
- SPA sem `try_files` → 404 em rotas cliente.
