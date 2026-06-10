# iSOG via npx

Pacote npm pequeno para iniciar a instalacao do iSOG pelo comando:

```powershell
npx -y sogtj
```

Na versao `0.1.12`, o bootstrap suporta apenas Windows. O pacote baixa o
instalador publicado no R2, confere a integridade automaticamente e abre o
instalador.

O comando `npx -y sogtj` nao substitui o instalador do sistema. Ele apenas
entrega o usuario ao instalador oficial. Depois da instalacao, o aplicativo
iSOG/SOG Desktop instalado inicia a stack local e abre o dashboard no navegador
padrao do Windows, que pode ser o Chrome. O dashboard local nao pede senha
propria; PJe/SISTJWEB continuam exigindo login manual quando o agente precisar.

Asset padrao da versao do instalador `0.1.9`:

```text
SOG.Desktop.Setup.0.1.9.exe
```

## Publicacao

1. Publique o instalador Windows no R2 em `sog.carlosguimaraes.us/sogtj/v0.1.9/`.
2. Atualize a verificacao de integridade interna do bootstrap.
3. Publique este pacote no npm:

```bash
cd packages/sogtj
npm publish --access public
```

## Teste com URL direta

```powershell
$env:ISOG_ASSET_URL="https://exemplo.local/SOG.Desktop.Setup.0.1.9.exe"
npx -y sogtj --verify-only
```
