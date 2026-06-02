# Distribuicao do iSOG via npx

Comando alvo para operadores Windows:

```powershell
npx -y sogtj
```

O pacote npm `sogtj` deve permanecer pequeno. Ele nao carrega o instalador
inteiro no npm; ele baixa o asset versionado da release, confere a integridade
automaticamente e abre o instalador Windows.

Em termos de experiencia do usuario:

1. O usuario executa `npx -y sogtj` no PowerShell.
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
2. Publicar o instalador no R2 em `sog.carlosguimaraes.us/sogtj/v0.1.4/` com o nome
   `SOG.Desktop.Setup.0.1.4.exe`.
3. Confirmar que o instalador publicado corresponde a verificacao interna do
   bootstrap da versao.
4. Publicar `packages/sogtj` no npm.
5. Testar em um desktop Windows limpo:

```powershell
npx -y sogtj --verify-only
npx -y sogtj
```

## Nome

- Marca: `iSOG`
- Pacote npm: `sogtj`
- Comando: `npx -y sogtj`

O npm exige pacote/comando em minusculas para esse caso. A interface textual do
bootstrap usa a marca `iSOG`.

## Multiplataforma

Na versao inicial, plataformas que nao sejam Windows recebem uma mensagem clara
de indisponibilidade. Quando macOS e Linux estiverem prontos, o mesmo comando
`npx -y sogtj` podera escolher o asset correto por plataforma.
