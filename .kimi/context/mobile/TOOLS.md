# TOOLS — Mobile Engineer

## `Think`
Use antes de implementar. Raciocine sobre:
- A feature precisa de permissão sensível? (reportar ao CEO)
- Qual o comportamento esperado offline?
- Há diferença de comportamento entre iOS e Android?
- A mudança afeta a navegação existente?
- Há dados sensíveis envolvidos? Onde serão armazenados?

---

## `ReadFile`
Leia sempre antes de modificar:
- A tela ou componente que será alterado
- O arquivo de navegação (rotas, stacks, tabs)
- Arquivos de store/estado relacionados
- Configurações de permissão (Info.plist, AndroidManifest.xml)
- Testes existentes

---

## `Glob`
Use para mapear a estrutura do app:
```
src/screens/**/*.tsx       → todas as telas
src/components/**/*.tsx    → componentes reutilizáveis
src/navigation/**          → arquivos de navegação
android/app/src/**         → código Android nativo
ios/**/*.swift             → código iOS nativo
*.json | app.json          → configurações Expo/RN
```

---

## `Grep`
Use para entender impacto de mudanças:
```
"useNavigation"            → onde navegação é usada
"AsyncStorage"             → onde dados são armazenados localmente
"PermissionsAndroid"       → permissões Android existentes
"requestPermission"        → solicitações de permissão iOS
"store.dispatch"           → chamadas ao estado global
```

---

## `Shell`
Use para:
- Instalar dependências (`npm install`, `expo install`)
- Rodar testes (`jest`, `detox test`)
- Verificar linting (`eslint`)
- Checar compatibilidade de dependências (`expo doctor`)
- Verificar erros de TypeScript (`tsc --noEmit`)

**Para builds: acione o agente devops — não faça builds você mesmo.**

---

## `WriteFile` / `StrReplaceFile`
WriteFile para arquivos novos (sempre completos).
StrReplaceFile para edições cirúrgicas em arquivos existentes.

---

## `SearchWeb` / `FetchURL`
Use para consultar:
- Documentação React Native / Expo / Flutter
- Human Interface Guidelines (Apple)
- Material Design Guidelines (Google)
- Políticas de permissão das lojas (App Store Review, Google Play Policy)
- Compatibilidade de APIs com versões de OS
