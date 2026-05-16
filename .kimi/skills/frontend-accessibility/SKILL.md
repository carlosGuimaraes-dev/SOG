---
name: frontend-accessibility
description: Acessibilidade WCAG 2.1 AA no frontend. Use quando criar componentes, formulários, navegação, modais ou qualquer interação que deve ser usável por teclado, leitores de tela e usuários com deficiências visuais.
---

# Acessibilidade (WCAG 2.1 AA)

## Resumo

Acessibilidade não é feature opcional. Esta skill cobre semântica HTML, ARIA, contraste, navegação por teclado, formulários acessíveis e testes automatizados com axe-core.

## Quando usar

- Criar ou revisar componentes React (botões, links, formulários, tabelas, modais).
- Implementar navegação, menus ou skip links.
- Revisar contraste de cores ou tamanho de fonte.
- Testar com teclado ou leitor de tela.
- Adicionar testes de acessibilidade automatizados.

## Padrões principais

### Semântica HTML

Use tags semânticas nativas sempre que possível. Elas já carregam roles e comportamentos acessíveis.

```tsx
<!-- Bom -->
<nav>
  <ul>
    <li><a href="/">Home</a></li>
    <li><a href="/processos">Processos</a></li>
  </ul>
</nav>

<main>
  <article>
    <h1>Título do processo</h1>
    <p>Descrição...</p>
  </article>
</main>

<!-- Ruim -->
<div class="menu">
  <div class="item" onclick="go('/')">Home</div>
</div>
```

### Atributos ARIA quando necessário

Use ARIA apenas quando o HTML semântico não for suficiente.

```tsx
<!-- Modal -->
<div role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <h2 id="modal-title">Confirmar exclusão</h2>
  <p>Tem certeza?</p>
  <button>Cancelar</button>
  <button>Excluir</button>
</div>

<!-- Alerta dinâmico -->
<div role="alert" aria-live="polite">
  Processo salvo com sucesso.
</div>

<!-- Expandir/colapsar -->
<button aria-expanded={isOpen} aria-controls="menu-content">
  Menu
</button>
<div id="menu-content" hidden={!isOpen}>...</div>
```

### Contraste de cores (4.5:1)

Texto normal deve ter contraste mínimo de 4.5:1 com o fundo. Texto grande (18px+ ou 14px bold) aceita 3:1.

- Use ferramentas como o DevTools do Chrome (Lighthouse) ou contrast checker online.
- Não confie apenas em cor para transmitir informação.

```tsx
<!-- Ruim: verde/vermelho sem texto -->
<span className="text-green-500">●</span>

<!-- Bom: cor + texto ou ícone + texto -->
<span className="flex items-center gap-1 text-green-700">
  <CheckIcon aria-hidden="true" /> Concluído
</span>
```

### Navegação por teclado

Todo elemento interativo deve ser alcançável com `Tab` e acionável com `Enter`/`Space`.

```tsx
<!-- Botão nativo já é focável -->
<button onClick={handleSave}>Salvar</button>

<!-- Div como botão: anti-pattern -->
<!-- Use <button> ou adicione tabIndex, role, handlers de tecla -->
<div
  role="button"
  tabIndex={0}
  onClick={handleSave}
  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleSave(); }}
>
  Salvar
</div>
```

### Labels em formulários

Todo input deve ter um `<label>` associado via `htmlFor`/`id`.

```tsx
<label htmlFor="numero">Número do processo</label>
<input id="numero" name="numero" type="text" required />

<!-- Ou aria-label quando não houver label visível -->
<input aria-label="Buscar processo" type="search" />

<!-- Grupos de campos -->
<fieldset>
  <legend>Tipo de custa</legend>
  <label><input type="radio" name="tipo" value="inicial" /> Inicial</label>
  <label><input type="radio" name="tipo" value="preparo" /> Preparo</label>
</fieldset>
```

### Textos alternativos

```tsx
<!-- Imagens informativas -->
<img src="logo.png" alt="Logo do TJDFT" />

<!-- Imagens decorativas -->
<img src="divider.svg" alt="" aria-hidden="true" />

<!-- Ícones dentro de botões -->
<button aria-label="Fechar modal">
  <XIcon aria-hidden="true" />
</button>
```

### Foco visível

Nunca remova o outline sem substituí-lo por outro indicador de foco.

```css
/* Tailwind já fornece focus-visible:ring */
button:focus-visible {
  @apply ring-2 ring-primary ring-offset-2;
}
```

### Skip links

```tsx
<a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded focus:bg-primary focus:px-4 focus:py-2 focus:text-white">
  Pular para o conteúdo
</a>
<main id="main-content">...</main>
```

### Testes com axe-core

```tsx
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { expect, describe, it } from 'vitest';
import { FormProcesso } from './FormProcesso';

expect.extend(toHaveNoViolations);

describe('Acessibilidade', () => {
  it('FormProcesso não tem violações', async () => {
    const { container } = render(<FormProcesso />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

## Exemplos

### Tabela acessível

```tsx
<table>
  <caption>Lista de custas processuais</caption>
  <thead>
    <tr>
      <th scope="col">Número</th>
      <th scope="col">Valor</th>
      <th scope="col">Status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">0001234</th>
      <td>R$ 150,00</td>
      <td>Pago</td>
    </tr>
  </tbody>
</table>
```

## Anti-patterns

- **`<div onClick>` sem role/foco/teclado** → use `<button>`.
- **Links que parecem botões** (`<a href="#">` com `onClick`) → use `<button>` para ações.
- **Cores como única forma de comunicar estado** → sempre acompanhe com texto ou ícone + texto.
- **ARIA em excesso** → HTML semântico resolve a maioria dos casos.
- **`tabIndex > 0`** → quebra a ordem natural do tab. Use `tabIndex={0}` ou `-1`.
- **Falta de `<main>` e headings hierárquicos** → leitores de tela dependem da estrutura.
