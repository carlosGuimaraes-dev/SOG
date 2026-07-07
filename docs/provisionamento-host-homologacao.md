# Provisionamento do host de homologacao com Docker Engine e Compose

Este procedimento prepara um host Linux de homologacao para rodar o Compose do
SOG com Docker Engine e o plugin `docker compose`.

## Escopo

- instala Docker Engine pelo repositorio oficial da Docker
- instala `docker compose` e `docker buildx`
- habilita o servico `docker`
- deixa um caminho de verificacao operacional explicito

## Premissas

- host Linux Debian 12+ ou Ubuntu 22.04+/24.04+
- acesso administrativo com `sudo`
- saida HTTPS para `download.docker.com`
- esta issue cobre apenas o runtime Docker do host, nao o preenchimento dos
  segredos do SOG

## Script canônico

Use o script do repositório:

```bash
sudo bash scripts/provision-docker-host.sh
```

O script:

- falha em distribuicoes fora de Debian/Ubuntu
- instala `docker-ce`, `docker-ce-cli`, `containerd.io`,
  `docker-buildx-plugin` e `docker-compose-plugin`
- habilita `systemctl enable --now docker`
- exibe `docker --version` e `docker compose version` ao final

## Verificacao minima do host

Depois da instalacao, rode:

```bash
sudo docker run --rm hello-world
docker --version
docker compose version
systemctl status docker --no-pager
```

Resultado esperado:

- `hello-world` executa sem erro
- `docker compose version` responde pelo plugin oficial
- `systemctl status docker` mostra o servico como `active (running)`

## Proximos passos para o SOG

1. Copiar o arquivo de exemplo:

   ```bash
   cp .env.example .env.api
   cp .env.example .env.agente
   ```

2. Preencher os segredos reais fora do repositório.
3. Subir a stack:

   ```bash
   docker compose up -d --build
   ```

4. Validar o ambiente:

   ```bash
   docker compose ps
   curl -sS http://localhost/api/v1/health
   docker logs --tail 200 custas-api
   docker logs --tail 200 custas-agente
   ```

## Decisoes operacionais

- O script nao adiciona usuarios ao grupo `docker` automaticamente.
- O uso de `sudo` permanece o caminho padrao ate uma decisao explicita sobre
  delegacao de privilegios no host.
- Se o host de homologacao usar outra distribuicao Linux, abra uma issue
  dedicada para adicionar suporte em vez de adaptar ad hoc no servidor.
