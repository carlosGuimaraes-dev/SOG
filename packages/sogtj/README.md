# iSOG via npx

Pacote npm pequeno para iniciar a instalacao do iSOG pelo comando:

```powershell
npx -y sogtj
```

Na versao `0.1.0`, o bootstrap suporta apenas Windows. O pacote baixa o
instalador publicado na release do GitHub, valida o SHA256 esperado da versao e
abre o instalador.

O comando `npx -y sogtj` nao substitui o instalador do sistema. Ele apenas
entrega o usuario ao instalador oficial. Depois da instalacao, o aplicativo
iSOG/SOG Desktop instalado inicia a stack local e abre o dashboard no navegador
padrao do Windows, que pode ser o Chrome.

Asset padrao da versao `0.1.0`:

```text
SOG.Desktop.Setup.0.1.0.exe
```

## Publicacao

1. Publique o instalador Windows como asset da release `v0.1.0`.
2. Calcule o SHA256 do instalador.
3. Publique este pacote no npm:

```bash
cd packages/sogtj
npm publish --access public
```

## Teste com URL direta

```powershell
$env:ISOG_ASSET_URL="https://exemplo.local/SOG%20Desktop%20Setup%200.1.0.exe"
npx -y sogtj --verify-only
```

Use `ISOG_SHA256` apenas para testar um asset diferente do oficial da versao.
