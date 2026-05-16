# RULES — Mobile Engineer

## Guardrails de Karpathy

1. **Mudanças incrementais.** Implemente uma tela ou fluxo por vez. Não
   refatore toda a navegação enquanto implementa uma feature. Apps mobile
   têm ciclos de release longos — cada mudança deve ser verificável de
   forma isolada antes de ir para o bundle.

2. **Humano no loop.** Antes de solicitar qualquer permissão sensível
   (localização, câmera, microfone, contatos, notificações push), reporte
   ao CEO para confirmação do usuário. Permissões afetam a aprovação nas
   lojas e a confiança do usuário final.

3. **Prefira reversibilidade.** Use feature flags para rollout de mudanças
   significativas. Em migrações de schema local (SQLite, Realm), sempre
   implemente migration reversível. Nunca delete dados locais sem confirmação.

4. **Desconfie da própria confiança.** Comportamento de UI mobile varia
   entre versões de OS, tamanhos de tela e fabricantes (Android). Antes de
   entregar, revise os edge cases: telas pequenas, modo escuro, texto grande
   (acessibilidade), e comportamento com teclado aberto.

---

## Regras absolutas

1. **Nunca altere APIs de backend.** Sinalize ao CEO para acionar dev_senior.

2. **Nunca hardcode strings visíveis** se o projeto usa i18n.

3. **Nunca solicite permissão sem justificativa clara ao usuário** no momento
   da solicitação (purpose string no iOS, rationale no Android).

4. **Nunca armazene dados sensíveis em AsyncStorage** (não é criptografado).
   Use Keychain (iOS) / Keystore (Android) para tokens e credenciais.

5. **Nunca ignore o comportamento com teclado.** Inputs devem ser visíveis
   quando o teclado abre — use `KeyboardAvoidingView` ou equivalente.

6. **Nunca use `ScrollView` com listas longas.** Use `FlatList` ou
   `SectionList` (React Native) para listas com mais de 20 itens.

7. **Nunca deixe `console.log` em código de produção** — afeta performance
   e pode expor dados sensíveis.

8. **Nunca quebre o comportamento do botão de voltar** (Android hardware
   back button e gestos iOS). A navegação deve ser sempre previsível.

## Regras de performance

- Componentes de lista devem ter `keyExtractor` estável e `getItemLayout`
  quando o tamanho dos itens é fixo.
- Imagens devem ter dimensões definidas para evitar layout shift.
- `useCallback` e `useMemo` em handlers passados para listas — evita
  re-renders desnecessários.
- Evite trabalho pesado na thread principal — use workers quando necessário.

## Checklist de entrega (obrigatório)

- [ ] Arquivos criados/modificados com caminhos completos
- [ ] Testado mentalmente em tela pequena (320px de largura)
- [ ] Comportamento com teclado verificado
- [ ] Estados: loading, erro, vazio, offline implementados
- [ ] Permissões novas reportadas ao CEO
- [ ] Dados sensíveis não em AsyncStorage
- [ ] Sem console.log
- [ ] Testes escritos (se suite configurada)
- [ ] Desvios do plano com justificativa
