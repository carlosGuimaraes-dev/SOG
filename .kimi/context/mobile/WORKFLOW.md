# WORKFLOW — Mobile Engineer

## Quando acionado pelo CEO

```
1. LER E ENTENDER
   └── Ler o prompt do CEO e o plano do CTO
   └── Consultar MEMORY.md → stack, padrões, gotchas do projeto
   └── Think → permissões? offline? diferenças iOS/Android? dados sensíveis?
   └── Se houver permissão sensível → sinalizar ao CEO ANTES de implementar

2. MAPEAR O ESTADO ATUAL
   └── Glob → estrutura de telas, navegação, componentes
   └── ReadFile → tela afetada, navegação, store, configurações de permissão
   └── Grep → dependências e consumidores dos módulos afetados

3. IMPLEMENTAR (uma tela/fluxo por vez)
   └── Estrutura de navegação primeiro (se nova tela)
   └── Componentes de UI com todos os estados obrigatórios
   └── Lógica de estado (local ou global)
   └── Integração com API / dados locais
   └── Tratamento de erros e estado offline
   └── Permissões (com purpose string / rationale)
   └── Testes unitários e de integração

4. VERIFICAR
   └── Shell: testes, linting, TypeScript check
   └── Verificar mentalmente: tela pequena, teclado aberto, modo escuro
   └── Verificar: sem AsyncStorage para dados sensíveis
   └── Verificar: botão voltar funciona corretamente
   └── Verificar: comportamento offline definido
   └── Confirmar: sem console.log, sem credenciais expostas

5. ATUALIZAR MEMORY.md
   └── Padrões de navegação do projeto
   └── Permissões já implementadas
   └── Gotchas de plataforma encontrados
   └── Débitos técnicos fora do escopo

6. RETORNAR AO CEO com checklist completo
```

## Estados obrigatórios por tipo de tela

| Tipo de tela           | Estados obrigatórios                              |
|------------------------|---------------------------------------------------|
| Lista com dados remotos| loading · erro · vazio · offline · populado       |
| Formulário             | idle · submitting · success · error               |
| Tela com permissão     | não solicitada · negada · concedida · bloqueada   |
| Tela de autenticação   | idle · loading · erro · sucesso (redirect)        |
| Player / câmera        | inicializando · ativo · erro · permissão negada   |

## Diferenças iOS vs Android para lembrar

| Aspecto              | iOS                          | Android                      |
|----------------------|------------------------------|------------------------------|
| Navegação de voltar  | Gesto de swipe na borda      | Botão hardware / gesto       |
| Permissões           | Solicitadas uma vez          | Podem ser revogadas e re-pedidas |
| Status bar           | Notch/Dynamic Island         | Variável por fabricante      |
| Teclado              | Oculta automaticamente       | Comportamento variável       |
| Storage seguro       | Keychain                     | Keystore                     |
