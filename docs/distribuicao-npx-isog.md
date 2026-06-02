# Distribuicao do iSOG via npx

Comando alvo para operadores Windows:

```powershell
npx -y isog
```

O pacote npm `isog` deve permanecer pequeno. Ele nao carrega o instalador
inteiro no npm; ele baixa o asset versionado da release, valida o SHA256 e abre
o instalador Windows.

Em termos de experiencia do usuario:

1. O usuario executa `npx -y isog` no PowerShell.
2. O `npx` baixa e abre o instalador oficial do iSOG/SOG Desktop.
3. O instalador instala o sistema no Windows.
4. O usuario abre o aplicativo instalado.
5. O aplicativo inicia a stack local e abre o dashboard no navegador padrao do
   Windows, que pode ser o Chrome.

Ou seja: o npm nao hospeda o sistema completo. O npm hospeda apenas o comando
de bootstrap. O sistema completo continua sendo entregue pelo instalador
Windows versionado.

## Fluxo inicial

1. Gerar o instalador Windows pelo fluxo existente do desktop.
2. Publicar o instalador como asset da release `v0.1.0`.
3. Confirmar que o SHA256 do instalador publicado corresponde ao hash fixado no
   bootstrap da versao.
4. Publicar `packages/isog` no npm.
5. Testar em um desktop Windows limpo:

```powershell
npx -y isog --verify-only
npx -y isog
```

## Nome

- Marca: `iSOG`
- Pacote npm: `isog`
- Comando: `npx -y isog`

O npm exige pacote/comando em minusculas para esse caso. A interface textual do
bootstrap usa a marca `iSOG`.

## Multiplataforma

Na versao inicial, plataformas que nao sejam Windows recebem uma mensagem clara
de indisponibilidade. Quando macOS e Linux estiverem prontos, o mesmo comando
`npx -y isog` podera escolher o asset correto por plataforma.
