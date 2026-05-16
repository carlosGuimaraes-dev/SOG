---
name: playwright-scraper
description: Automação web com Playwright para sistemas judiciais (PJe, SISTJWEB). Padrões de login, navegação, screenshots como evidência, retry, selectors resilientes, espera por elementos dinâmicos, tratamento de CAPTCHA/2FA e download de documentos.
---

# Playwright Scraper para Sistemas Judiciais

## Resumo

Automação robusta de navegadores para consulta e extração de dados em sistemas judiciais brasileiros. Foco em estabilidade, rastreabilidade via screenshots e recuperação de falhas transitórias.

## Quando usar

- Raspagem de dados em PJe, SISTJWEB ou outros sistemas judiciais
- Automação de login em portais com sessões expiráveis
- Download de documentos processuais (PDFs, guias de custas)
- Captura de evidências para auditoria ou debug

## Padrões principais

### 1. Login e navegação

```python
from playwright.async_api import async_playwright

async def login(page, cpf: str, senha: str):
    await page.goto("https://pje.tjdft.jus.br/")
    await page.fill('input[placeholder="CPF"]', cpf)
    await page.fill('input[type="password"]', senha)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
```

### 2. Selectors resilientes

Prefira atributos estáveis em vez de classes geradas automaticamente:

```python
# Ruim
await page.click(".css-1a2b3c4d")

# Bom
await page.click('button[title="Consultar processo"]')
await page.click('input[name="numeroProcesso"]')
await page.locator("text=Consultar").click()
```

### 3. Espera por elementos dinâmicos

```python
# Espera explícita por elemento
await page.wait_for_selector("#resultado", state="visible", timeout=30000)

# Espera por requisições de rede terminarem
await page.wait_for_load_state("networkidle")

# Retry com backoff
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def consultar_processo(page, numero: str):
    await page.fill('input[name="numeroProcesso"]', numero)
    await page.click('button[title="Consultar"]')
    await page.wait_for_selector("#resultado", timeout=15000)
```

### 4. Screenshots como evidência

```python
import os
from datetime import datetime

async def screenshot_evidence(page, numero_processo: str, etapa: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"/dados/screenshots/{numero_processo}/{etapa}_{timestamp}.png"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    await page.screenshot(path=path, full_page=True)
    return path
```

### 5. Download de documentos

```python
async def download_documento(page, link_text: str, destino: str):
    async with page.expect_download() as download_info:
        await page.click(f"text={link_text}")
    download = await download_info.value
    await download.save_as(destino)
    return destino
```

### 6. Tratamento de CAPTCHA / 2FA

Nunca tente burlar CAPTCHA automaticamente. Pare e reporte:

```python
async def check_captcha(page):
    captcha = await page.query_selector(".g-recaptcha, #captcha, iframe[src*='recaptcha']")
    if captcha and await captcha.is_visible():
        await screenshot_evidence(page, "captcha_detectado", "alerta")
        raise RuntimeError("CAPTCHA detectado. Intervenção manual necessária.")
```

### 7. Retry patterns para instabilidade

```python
from tenacity import retry, retry_if_exception_type, stop_after_attempt

@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    reraise=True
)
async def operacao_critica(page):
    # ...
```

## Anti-patterns

- Usar `time.sleep()` fixo em vez de esperas explícitas
- Fazer login a cada requisição em vez de reutilizar sessão/cookies
- Ignorar erros de rede sem retry
- Usar f-string em vez de parametrização em URLs/inputs
- Não capturar screenshots em falhas
- Tentar resolver CAPTCHA automaticamente (violação de termos)
