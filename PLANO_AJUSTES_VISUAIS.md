# Plano — ajustes visuais (pedido de 10/11/2026)

Status: **concluído e publicado em 11/11/2026** (commits 80488b9, 7a2b152, 4ca4567).
Não commitar este arquivo (como `.claude/`, `IDENTIDADE_VISUAL_CGB.md` e os relatórios).

Regras de sempre: testar no servidor local (`qa-vagas`, 127.0.0.1:5001), mostrar,
e só publicar quando o usuário disser. Commit com
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Responder em PT-BR.

Referência de estilo: a aba **Indiretos** (`frontend/src/pages/alocacao-indiretos.vue`)
como ficou no commit 06a2169 — lista limpa, faixa de números em vez de cartões
de indicador, botões só com texto, campos sem ícone na frente, cor com
significado (base, vaga vazia azul, extra laranja), esqueleto no carregamento.
Tokens em `frontend/src/css/app.scss` (`--marca`, `--marca-clara`, `--titulo`,
`--superficie`, `--superficie-2`, `--linha`, `--tinta-fraca`, `--tipo-p1..p10`,
`--vaga-vazia`, `--folguista`), claro e escuro (`body.body--dark`).

---

## 1. Visual mais sóbrio em todas as abas

Abas: `index.vue` (Resumo), `banco-dados.vue`, `cadastro-vagas.vue`,
`cadastro-colaboradores.vue`, `usuarios.vue` (+ `sem-acesso.vue`).

Fazer, aba a aba, o mesmo acabamento dos Indiretos:
- tirar degradês e sombras fortes dos cartões/botões; superfície lisa com
  borda fina (`--linha`); vinho só em ação e destaque;
- chips coloridos de contagem → texto/faixa de números (ex.: no topo do Banco
  de Dados, linhas ~153–176: "N equipes · N alocados · N livres · N afastados");
- botões com texto sem ícone (ícone só nos botões que são só ícone);
- campos de formulário sem ícone na frente (`<template #prepend>` nos diálogos);
- dicas (`hint`) que só repetem o rótulo: tirar;
- spinner de carregamento → `q-skeleton` no formato da tela.
- Cuidado: o Resumo (`index.vue`) tem os chips de disciplina coloridos por tipo
  (`--tipo-*`) — esses têm significado, manter a cor, só suavizar.

Ordem sugerida: Banco de Dados → Resumo → Cadastro de Vagas → Usuários →
Cadastro de Colaboradores.

## 2. "Menu" suspenso vira barra lateral que se oculta

Hoje: `frontend/src/components/CabecalhoApp.vue` — `q-header` com
`q-btn-dropdown label="Menu"` (linhas ~33–60, itens de navegação) e o menu da
conta (~66–110). Cada página monta o próprio `<q-layout view="lHh Lpr lFf">`
e usa `<CabecalhoApp>` (alocacao-indiretos, banco-dados, cadastro-colaboradores,
cadastro-vagas, index, sem-acesso, usuarios).

Plano:
- criar `frontend/src/components/MenuLateral.vue` com `q-drawer`
  (`side="left"`, `show-if-above`, `:width="232"`, `bordered`), lista dos mesmos
  itens de navegação (mesmas permissões/`v-if` do dropdown atual), item ativo
  destacado em vinho claro;
- modo recolhido: `:mini="recolhido"` (só ícones) + botão de recolher/expandir no
  rodapé do menu; lembrar a escolha em `localStorage` (com try/catch);
- no celular: abre por cima (overlay) pelo botão ☰ do cabeçalho;
- `CabecalhoApp.vue`: tirar o dropdown "Menu", pôr o botão ☰ (alterna o menu)
  à esquerda; manter atualizar, modo noturno e o menu da conta;
- estado do menu compartilhado (composable `useMenuLateral` com `ref` global)
  para todas as páginas, sem mexer na lógica delas;
- mudar `view` do `q-layout` das páginas para `"lHh LpR lFf"` (drawer
  embaixo do cabeçalho) e incluir `<MenuLateral />` — 7 páginas, mudança igual.
- Verificar: navegação entre todas as abas, permissões (conta sem
  gerenciar_usuarios não vê Usuários etc.), celular 375px, claro/escuro,
  exportar imagem do organograma (não pode pegar o menu).

## 3. Banco de Dados > Colaboradores: chips ocupando linhas demais

Hoje: `frontend/src/pages/banco-dados.vue` linhas ~450–497: quatro `q-btn`
outline separados (Todos, Alocados (N), Livres (N), Afastados (N)), cada um num
`col-auto` de uma `row`; abaixo, outra linha com o `q-btn-toggle`
Diretos/Indiretos e a busca (~499–520).

Plano:
- trocar os 4 botões por **um** `q-btn-toggle` (ou grupo segmentado) compacto
  com as quatro opções e a contagem: "Todos · Alocados 748 · Livres 13 ·
  Afastados 4" (`statusColaborador`, mesmos valores);
- juntar na **mesma linha**: segmentado de situação + Diretos/Indiretos + busca
  (busca com `col` para ocupar o resto); em tela estreita quebra para 2 linhas
  no máximo;
- mesma ideia no topo da aba Equipes (linhas ~127–176: toggle
  Todas/Completas/Incompletas + 4 chips) → toggle + faixa de números numa linha.
- Verificar: os filtros continuam filtrando igual; 1366px cabe numa linha.

## 4. Filtros mais modernos em todas as abas

Hoje: `frontend/src/components/SelectFiltroMultiplo.vue` (170 linhas, usado em
alocacao-indiretos, banco-dados, cadastro-vagas, index) + estilos
`.barra-filtros` / `.filtros-campos` em `frontend/src/css/app.scss`
(~linhas 440–510, inclusive modo escuro). Mostra chips "Todos os setores ⊗"
dentro do campo, rótulo flutuante pequeno e ícone.

Plano (no componente, vale para todas as abas de uma vez):
- campo "pílula" de altura fixa (~36px), sem chips dentro: mostra o resumo
  ("Setor: Todos", "Setor: GOMAN", "Setor: 3 selecionados"); fundo
  `--superficie-2`, borda fina, cantos arredondados, sem rótulo flutuante;
- selecionado (≠ Todos) fica destacado em vinho claro + "×" para limpar só ele;
- menu suspenso com busca no topo, caixas de seleção, "Todos" fixo no alto,
  rolagem; contagem por opção quando a página fornecer;
- barra de filtros: uma linha só com os filtros + "Limpar filtros" como link de
  texto à direita; a busca por nome/chapa na mesma linha quando couber;
- manter a API do componente (`model-value`, `options`, `label`, `icon`,
  `proximaSelecaoMultipla` com `TODOS`) para não mexer na lógica das páginas.
- Verificar: as 4 abas que usam o filtro, seleção múltipla, "Todos" volta a
  limpar, teclado (Tab/Enter/Esc), modo escuro, celular.

## 5. Tela de login com faixa lateral da CGB

Hoje: `frontend/src/pages/login.vue` (1014 linhas). O fundo **não é vídeo**: é
um **plexus gerado em código** — `canvas.canvas-fundo` desenhado em 2D nativo,
26 pontos (`particulas`) flutuando devagar e ligados por linhas finas quando
ficam perto, nas cores da marca (linhas ~346–440; animação por
`requestAnimationFrame`, refeita no resize). Marca d'água
`/icons/logo-fundo.png`, `.conteudo-login` com `.coluna-mensagem` ("Gestão de
Equipes", selo de acesso restrito) e o cartão do formulário. Logos em
`frontend/public/icons/` (`logo-login.png`, `logo-fundo.png`).

Plano:
- layout em duas partes: **faixa lateral à esquerda** (~38% da largura no
  desktop) com o degradê/cores da CGB (`--gradiente-marca`), logo CGB grande em
  branco, nome do sistema e o selo "Acesso restrito"; **à direita**, o resto da
  página com o canvas das linhas flutuantes (mantido) e o cartão de login;
- o plexus continua sendo gerado do mesmo jeito (mesmo código, mesmas cores e
  velocidade), só que o canvas passa a ocupar a área da direita: medir pelo
  contêiner, não pela janela, e redistribuir os pontos no resize; a faixa
  lateral fica lisa, sem plexus por baixo;
- conferir se há versão branca/negativa do logo; se não, usar `logo-login.png`
  sobre um selo claro ou aplicar `filter: brightness(0) invert(1)` (testar);
- celular: a faixa vira um topo baixo (só o logo), formulário embaixo;
- manter tudo do formulário (login, mostrar senha, "esqueceu a senha", ajuda) e
  o modo escuro.
- Verificar: login funciona, 375px, claro/escuro, sem rolagem horizontal.

---

## Ordem e tamanho

1. Item 4 (filtros) — 1 componente + CSS global, efeito em todas as abas.
2. Item 3 (chips do Banco de Dados) — pequeno.
3. Item 5 (login) — 1 arquivo.
4. Item 2 (menu lateral) — 1 componente novo + cabeçalho + 7 páginas.
5. Item 1 (sóbrio, aba a aba) — o maior; fazer por partes e mostrar cada aba.

Cada item: implementar → build (`npm run build` em `frontend/`) → testes
(`.venv/Scripts/python.exe -m pytest -q`) → conferir no servidor local (claro,
escuro, 375px) → mostrar → publicar só com o "sim" do usuário.
Nenhum item mexe em banco/migração.
