# Plano Técnico: Correção do Flicker do Botão de Login

## 1. Diagnóstico

### Causa Raiz
**Loop infinito de reload da página** causado pela interação entre o interceptor de 401 do Axios (`api.ts`) e a verificação de sessão no mount do `AuthProvider` (`auth.tsx`).

### Fluxo do Bug
1. Usuário acessa `/login` sem sessão ativa.
2. `AuthProvider` monta e dispara `useEffect` que chama `api.get(ENDPOINTS.ME)` (`/auth/me`).
3. O backend retorna **401 Unauthorized**.
4. O interceptor de resposta do Axios (`api.ts`) captura o 401 e tenta renovar a sessão via `POST /api/v1/auth/refresh`.
5. O refresh falha (sem cookie de refresh válido).
6. O interceptor executa `window.location.href = '/login'` — **mesmo já estando na página `/login`**.
7. O navegador recarrega a página inteira, reiniciando o React tree.
8. O `AuthProvider` monta novamente e o ciclo se repete **infinitamente**.

### Por que o botão "flicka"
O flicker visual do botão "Logar" é o sintoma do reload contínuo da página. A cada ciclo (~centenas de ms):
- A DOM é destruída e recriada;
- O botão renderiza inicialmente com `isLoading = true` (texto "Entrando...", disabled);
- Em seguida a página recarrega e o estado some.

### Arquivos Envolvidos
- `frontend/src/lib/api.ts` — interceptor de resposta que redireciona incondicionalmente
- `frontend/src/lib/auth.tsx` — `AuthProvider` que dispara `/auth/me` no mount
- `frontend/src/pages/Login.tsx` — consome `isLoading`, sofre com os reloads

---

## 2. Ação Corretiva Necessária

### Mudança principal: `frontend/src/lib/api.ts`
No interceptor de erro, antes de redirecionar para `/login`, verificar se o usuário **já está** na rota de login. Se sim, apenas rejeitar a promise sem forçar navegação.

```typescript
// NO interceptor de resposta (api.ts)
if (error.response?.status === 401 && !originalRequest._retry) {
  originalRequest._retry = true
  try {
    await axios.post('/api/v1/auth/refresh', {}, { withCredentials: true })
    return api(originalRequest)
  } catch (refreshError) {
    // QUEBRA O LOOP: só redireciona se NÃO estiver em /login
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
    return Promise.reject(refreshError)
  }
}
```

### Comportamento esperado após a correção
- Em `/login` sem sessão: a chamada `/auth/me` falha com 401, o refresh falha, o interceptor rejeita silenciosamente, o `AuthProvider` seta `isLoading = false`, e o botão fica estável com texto **"Entrar"** e `disabled = false`.
- Em rotas protegidas com sessão expirada: o fluxo de redirecionamento para `/login` continua funcionando normalmente.

---

## 3. Critérios de Aceite

- [ ] Ao abrir `/login` sem sessão ativa, o botão exibe o texto **"Entrar"** de forma estável, sem alternar para "Entrando..." ou qualquer outro estado.
- [ ] Não há reload da página ao carregar a tela de login.
- [ ] Nenhum erro de loop de navegação aparece no console do navegador.
- [ ] Em rotas protegidas (`/`, `/historico`, `/detalhe/:id`), quando a sessão expira, o redirecionamento para `/login` ainda ocorre corretamente.
- [ ] O teste manual de login com credenciais válidas continua funcionando (botão mostra "Entrando..." apenas durante a submissão do formulário).

---

## 4. Ação Irreversível

**Não há.** A correção consiste em adicionar uma guarda condicional no interceptor do Axios. Pode ser revertida removendo a condição `window.location.pathname !== '/login'`.
