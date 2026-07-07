#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'Erro: %s\n' "$1" >&2
  exit 1
}

if [[ "${EUID}" -ne 0 ]]; then
  fail "execute como root ou com sudo"
fi

if [[ ! -r /etc/os-release ]]; then
  fail "/etc/os-release ausente; nao foi possivel identificar a distribuicao"
fi

# shellcheck disable=SC1091
source /etc/os-release

if [[ "${ID:-}" != "ubuntu" && "${ID:-}" != "debian" ]]; then
  fail "distribuicao sem suporte: ${ID:-desconhecida}. Use Ubuntu ou Debian."
fi

if [[ -z "${VERSION_CODENAME:-}" ]]; then
  fail "VERSION_CODENAME ausente em /etc/os-release"
fi

ARCH="$(dpkg --print-architecture)"

case "${ARCH}" in
  amd64|arm64|armhf)
    ;;
  *)
    fail "arquitetura sem suporte: ${ARCH}"
    ;;
esac

echo "==> Instalando pre-requisitos do APT"
apt-get update
apt-get install -y ca-certificates curl gnupg

echo "==> Configurando repositorio oficial Docker para ${ID} ${VERSION_CODENAME}"
install -m 0755 -d /etc/apt/keyrings
curl -fsSL "https://download.docker.com/linux/${ID}/gpg" | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

cat >/etc/apt/sources.list.d/docker.list <<EOF
deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${ID} ${VERSION_CODENAME} stable
EOF

echo "==> Instalando Docker Engine e plugins de Compose/Buildx"
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "==> Habilitando servico Docker"
systemctl enable --now docker
systemctl is-active --quiet docker || fail "servico docker nao ficou ativo"

echo "==> Versoes instaladas"
docker --version
docker compose version

cat <<'EOF'

Provisionamento concluido.

Proximos passos sugeridos:
1. Validar acesso administrativo com `docker run --rm hello-world`.
2. Preparar `.env.api` e `.env.agente` a partir de `.env.example`.
3. Subir a stack com `docker compose up -d --build`.

Observacao:
- O script nao adiciona usuarios ao grupo `docker`; mantenha o uso via sudo
  ate uma decisao operacional explicita sobre esse risco.
EOF
