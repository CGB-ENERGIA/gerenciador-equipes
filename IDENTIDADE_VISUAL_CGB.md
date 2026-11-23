# Identidade Visual CGB Energia: guia para novos projetos

**Origem:** extraído do sistema **Gerenciador de Equipes** (Vue 3 + Quasar).
**Primeira versão:** 23/10/2026 · **Atualizado:** 11/11/2026 (commit `80488b9`: menu lateral, filtros em pílula, chips tonais, visual mais sóbrio) e, em seguida, faixa lateral da CGB no login.
**Uso:** base para outros sistemas, relatórios e telas internas da CGB Energia ficarem com a mesma cara.

> Este guia descreve a identidade **como ela está aplicada no Gerenciador de Equipes**. Não é o manual oficial de marca da CGB: se existir um manual corporativo, ele prevalece. As cores do logo foram medidas direto no arquivo `logo-login.png`.

---

## 1. Essência

- **Cor-mãe:** bordô/vinho (`#711424`), tirado do losango do logo. Vai no cabeçalho, na barra lateral, no cabeçalho das tabelas e nas ações principais.
- **Neutros quentes:** fundos e textos puxam levemente para o rosado/marrom, nunca para o cinza puro.
- **Tom:** corporativo, sóbrio e operacional. Muita informação em pouco espaço.
- **Cor só com significado:** status (alocado, livre, afastado), disciplina, vaga vazia, extra, falta/sobra. Elementos sem significado ficam neutros.
- **Moldura forte, miolo suave:** o vinho fica nas "bordas" da tela (cabeçalho, menu lateral, cabeçalho de tabela). O conteúdo usa superfícies lisas e cores tonais (fundo claro + texto forte na mesma cor). Assim a tela não fica nem pesada nem "pastel".
- **Menos cara de "gerado":** sem degradês e sombras em todo canto, sem ícone em todo botão, sem chips coloridos por enfeite.
- **Assinatura gráfica:** o **losango de ladrilhos** do logo como marca-d'água discreta.
- **Dois temas:** claro (padrão) e escuro, com o mesmo tom quente.

---

## 2. Logo

| Arquivo | Uso | Descrição |
|---|---|---|
| `logo-login.png` (1512×596) | Fundos claros: login, cartões, relatórios | Losango bordô + "CGB" em cinza-grafite |
| `logo-cabecalho.png` | Sobre a barra bordô do cabeçalho | Versão **toda branca** |
| `logo-fundo.png` (500×500) | Marca-d'água | Só o losango |
| `favicon-16/32/96/128.png` e `favicon.ico` | Aba do navegador | Símbolo reduzido |

Ficam em `frontend/public/icons/`.

**Cores do símbolo** (8 ladrilhos em degradê de bordô, quadrado vazado no centro):

| Parte | Cor |
|---|---|
| Ladrilhos de cima e de baixo | `#711423` |
| Intermediários | `#7D162A` / `#82162C` |
| Laterais | `#9F183C` / `#A3183E` |
| Ponta esquerda (mais clara) | `#BA2255` |
| Letras "CGB" | `#4A4A49` |

**Regras:**
- Fundo bordô ou escuro: **versão branca**. Fundo claro: **versão colorida**. Nunca o colorido sobre o bordô.
- Cabeçalho: área de 88×40 px, `object-fit: contain`. Login: 56 px de altura.
- Marca-d'água da página: só o símbolo, **3,5%** de opacidade no claro e **6%** no escuro, fixa no canto inferior direito vazando da tela.
- Marca-d'água do menu lateral: `logo-fundo.png` em branco (`filter: brightness(0) invert(1)`), **6%** de opacidade, 180 px, no pé do menu (44 px com o menu recolhido).
- Não distorça o logo.

---

## 3. Cores

### 3.1 Marca

| Token | Claro | Escuro | Uso |
|---|---|---|---|
| `--marca` | `#711424` | `#7C1A2C` | Cabeçalho, botão principal, fundo de destaque |
| `--marca-clara` | `#8D2136` | `#99283F` | Links, foco, borda de filtro ativo |
| `--marca-texto` | `#8D2136` | `#F0A3B3` | Vinho usado **como texto** (clareia no escuro) |
| `--titulo` | `#4F1723` | `#F2DBE0` | Títulos (h4 a h6) |
| Rosa de destaque | `#E57C94` | `#E08A9C` | Fim de degradês |

**Degradês da marca:**

| Nome | Valor | Onde |
|---|---|---|
| `--gradiente-marca` | `linear-gradient(100deg, #4E0B17 0%, #711424 45%, #A8304A 100%)` | Cabeçalho e cabeçalho das tabelas |
| Menu lateral (claro) | `linear-gradient(180deg, #5A0F1C 0%, #711424 55%, #8D2136 100%)` | Barra lateral |
| Menu lateral (escuro) | `linear-gradient(180deg, #2A0A10 0%, #4A0D18 55%, #5E1424 100%)` | Barra lateral no tema escuro |

No Quasar (`quasar.variables.scss`):
```scss
$primary:   #711424;
$secondary: #9b5361;
$accent:    #c9741b;
$positive:  #1b6b45;
$negative:  #b3261e;
$info:      #31ccec;
$warning:   #f2c037;
```

### 3.2 Neutros

| Token | Claro | Escuro | Uso |
|---|---|---|---|
| `--fundo` | `#F2EEEF` | `#171314` | Fundo da página |
| `--superficie` | `#FFFFFF` | `#221C1E` | Cartões, tabelas, campos |
| `--superficie-2` | `#FAF7F8` | `#2B2325` | Áreas secundárias, linha de total, filtro em pílula |
| `--tinta` | `#2D2527` | `#F1E9EA` | Texto principal |
| `--tinta-fraca` | `#6D5F63` | `#B7A6AA` | Texto secundário, rótulos |
| `--neutro` | `#7A6C70` | `#9C8B90` | Status neutro (livre, vagas) |
| `--linha` | `rgba(113,20,36,.16)` | `rgba(212,154,85,.20)` | Bordas e divisórias |
| `--linha-forte` | `rgba(113,20,36,.32)` | `rgba(212,154,85,.38)` | Hover, separação de grupo |

No claro as bordas são **bordô translúcido**; no escuro, **âmbar translúcido**.

### 3.3 Cores com significado

| Significado | Texto (claro / escuro) | Fundo (claro / escuro) |
|---|---|---|
| Positivo / alocado / sobra | `#1B6B45` / `#6CC79A` | `#E6F2EA` / `#1E3329` |
| Negativo / falta / erro | `#B3261E` / `#F08A80` | `#FBE9E7` / `#3D2321` |
| Afastado / atenção | `#8A5A00` / `#E0B84C` | `#FDF0CD` / `#3D3218` |
| Folguista / extra (laranja) | `#C9741B` / `#E0A259` | `#FBEEDD` / `#3B2C1C` |
| Vaga vazia (azul do BID) | `--vaga-vazia` `#2F5D8A` | `--vaga-vazia-fundo` `#E3ECF5` (+ versão escura no tema) |
| Realce informativo | — | `#F7E9D7` / `#382A1C` |

### 3.4 Paleta de categorias (disciplinas, bases, séries de gráfico)

Construção usa a cor da marca, Folguista usa o laranja; as demais recebem as cores abaixo **sempre na mesma ordem e fixas por nome**, para a categoria manter a cor em todas as telas.

| Token | Claro | Escuro |
|---|---|---|
| `--tipo-construcao` | `#711424` | `#E08A9C` |
| `--tipo-folguista` | `#AD6417` | `#E0A259` |
| `--tipo-p1` | `#3F6B48` | `#86C294` |
| `--tipo-p2` | `#4A5C80` | `#9AB0D8` |
| `--tipo-p3` | `#6B4A78` | `#C3A0CD` |
| `--tipo-p4` | `#1F6F6B` | `#71C4BD` |
| `--tipo-p5` | `#8A5A2B` | `#D9A877` |
| `--tipo-p6` | `#A03D5C` | `#E896AC` |
| `--tipo-p7` | `#5F6B2A` | `#B9C47E` |
| `--tipo-p8` | `#2F6690` | `#86B6DD` |
| `--tipo-p9` | `#8A6A1F` | `#D9C078` |
| `--tipo-p10` | `#8A3F78` | `#D693C9` |
| `--tipo-outro` | `#6D5F63` | `#B7A6AA` |

Essas cores **não são mais usadas chapadas com texto branco** nos chips: elas entram no estilo tonal (seção 5.4). Chapadas, só em barrinhas e marcadores finos (ex.: filete de 3 px da disciplina na tabela, cor da base nos Indiretos).

---

## 4. Tipografia

Fontes **hospedadas no projeto** (`frontend/public/fonts/`, woff2), sem Google Fonts, por causa da CSP do app. Licença livre (SIL OFL).

| Papel | Fonte | Pesos | Onde |
|---|---|---|---|
| **Interface** (`--fonte-ui`) | Barlow Semi Condensed | 600, 700 | Títulos, rótulo de disciplina, barra superior |
| **Texto** (`--fonte-texto`) | Inter (variável) | 400 a 800 | Corpo, campos, tabelas, botões, chips |

Reserva: `'Segoe UI', sans-serif`. (Há um `@font-face` de IBM Plex Sans 400 no `app.scss`, mas ele não é mais usado.)

**Escala e estilo:**
- Base `html { font-size: 13px }`: sistema denso. Para relatório ou página de leitura, 14 a 16 px.
- Títulos (h4 a h6): Barlow 700, cor `--titulo`, `text-wrap: balance`.
- Overline (rótulo acima de seção): Barlow 700, `0.14em`, cor `--marca-clara`.
- Cabeçalho de tabela: **11 px, peso 600, MAIÚSCULAS, espaçamento `0.06em`**, branco sobre o degradê da marca.
- Números: `font-variant-numeric: tabular-nums` em tabelas, chips e contadores.
- Rótulo de filtro: 13 px; nome do filtro em `--tinta-fraca`, valor em peso 600.

---

## 5. Componentes

### 5.1 Estrutura da tela

- `q-layout view="hHh Lpr lFf"`: o cabeçalho ocupa a largura toda e o menu lateral fica **embaixo** dele.
- **Cabeçalho:** fundo bordô, texto branco. Da esquerda para a direita: botão ☰ (abre/recolhe o menu), logo branco, título da tela, atualizar, tema claro/escuro, menu da conta (nome, nível, ajuda, trocar senha, sair).
- **Menu lateral** (`CabecalhoApp.vue` + `composables/useMenuLateral.js`):
  - degradê vinho vertical (seção 3.1), texto branco a 82%, ícones de 20 px;
  - itens com 40 px de altura e cantos de 8 px; hover `rgba(255,255,255,.08)`;
  - item ativo: fundo `rgba(255,255,255,.16)`, texto branco peso 600 e **filete branco de 3 px à esquerda**;
  - largura 232 px; recolhido 60 px (só ícones, nome em dica ao passar o mouse); botão "Recolher menu" no rodapé; a escolha fica salva no navegador;
  - abaixo de **1024 px** abre por cima da página pelo ☰ e fecha ao escolher uma aba;
  - mostra só as abas que o nível da pessoa alcança.

### 5.2 Cartões

- Fundo `--superficie`, cantos de **14 px** (`--raio`), borda de 1 px em `--linha`, sombra em camadas (`--sombra`).
- Cartão dentro de cartão não repete a sombra.
- **Barra de filtros:** cartão **liso** (cantos de 12 px, borda `--linha`, sem sombra, sem degradê e sem filete no topo), com 12×16 px de respiro.

### 5.3 Filtros em pílula (`SelectFiltroMultiplo.vue`)

- Altura fixa de **36 px**, cantos `999px`, fundo `--superficie-2`, borda `--linha`; sem ícone, sem rótulo flutuante e sem chips dentro do campo.
- Mostra o resumo: `Setor: Todos`, `Setor: GOMAN` ou `Setor: 3 selecionados`, com seta à direita.
- **Filtro em uso:** borda `--marca-clara`, fundo `rgba(113,20,36,.07)`, valor em vinho e um **×** que limpa só aquele filtro.
- Foco/aberto: anel `0 0 0 3px rgba(113,20,36,.10)`.
- Menu: cantos de 12 px, "Todos" fixo no alto separado por linha, caixas de seleção, itens de 32 px, rolagem até 300 px, contagem por opção à direita quando houver. Com mais de 6 opções aparece uma **busca** no topo (já com o cursor, ignora acentos).
- Serve também para escolha única (`:multiple="false"`).
- **"Limpar filtros":** link de texto sublinhado, sem ícone, à direita da linha.

### 5.4 Chips tonais (classe `chip-tonal`)

Referência: fundo claro no tom da cor, texto forte na mesma cor, cantos arredondados, número no lugar do ícone.

- Cor definida por `--cor-chip` (ex.: `style="--cor-chip: var(--positivo)"` ou a cor da disciplina).
- Fundo: `color-mix(in srgb, var(--cor-chip) 11%, var(--superficie))`; texto: `color-mix(in srgb, var(--cor-chip) 88%, #000)`; peso 700; cantos de **10 px**; sem sombra.
- **Número** (`chip-tonal__num`): quadradinho de 22×20 px, cantos de 6 px, fundo com a cor a 20%, peso 800, à esquerda do nome.
- Escuro: fundo com a cor a 22% sobre `--superficie`, texto `color-mix(cor 45%, #fff)`, número a 40%.
- Chip de filtro ativo: contorno interno de 1,5 px na cor do texto.
- Os selos soltos do Quasar (`color="positive"`, `amber-8`, `grey-*`, `primary`, `negative`, `orange`) viram tonais automaticamente pelo `app.scss`, com cantos de 8 px. O mesmo vale para os `q-badge` de situação (Alocado, Livre, Afastado), com cantos de 6 px.

### 5.5 Seletor segmentado (ex.: situação dos colaboradores)

- Uma barra dividida em partes **iguais** (`grid-template-columns: repeat(N, 1fr)`), borda `--linha`, cantos de 10 px, divisórias verticais finas.
- Cada parte: **número em cima** (1,05rem, 700) e nome embaixo (0,72rem, 600).
- Parte ativa: fundo tonal da cor dela e **filete de 2 px embaixo** na cor (Todos = vinho, Alocados = verde, Livres = cinza, Afastados = âmbar).
- Use no lugar de vários botões soltos que quebram linha.
- Para opções sem número (ex.: Diretos/Indiretos, Todas/Completas/Incompletas), `q-btn-toggle` compacto.

### 5.6 Botões

- Cantos de **12 px**, Inter 600, `letter-spacing: 0.01em`.
- Botão principal (`color="primary"`): degradê da marca.
- **Botão com texto não leva ícone**; ícone só em botão que é só ícone (redondo, com dica).
- Contornado: borda de 1,5 px; hover `rgba(113,20,36,.06)`.
- Exportar Excel: botão redondo com o ícone `excel.png` e dica.
- Respeita `prefers-reduced-motion`.

### 5.7 Tabelas

- **Cabeçalho:** linha com `--gradiente-marca` (células transparentes, para o degradê não se repetir por coluna), texto branco 11 px em maiúsculas (seção 4). É a cor que segura a tela agora que os chips são suaves.
- Corpo sobre `--superficie`, bordas `--linha`, hover `--superficie-2`, linhas compactas.
- **Célula de grupo** (disciplina mesclada): alinhada à esquerda, sem fundo, **filete de 3 px** na cor da disciplina; nome em Barlow 700 maiúsculo na cor da disciplina, detalhe ("N equipe(s) · N vaga(s)") em `--tinta-fraca`.
- Separação entre grupos: borda superior `--linha-forte`.
- **Diferença:** falta em pílula vermelha (`--negativo` / `--negativo-fundo`), sobra em pílula verde; **zero é só o número apagado, sem pílula**.
- **Linha de Total:** fundo `--superficie-2`, borda superior de 2 px `--linha-forte`, peso 700. Os totais são **clicáveis** (abrem a lista completa daquela base ou de todas).
- Números clicáveis: `q-btn flat dense color="primary"`.
- Cartão de tabela: título + legenda curta (ex.: "746 pessoa(s) · clique num número para ver a lista").

### 5.8 Listas de vagas (aba Indiretos — referência de lista limpa)

- Lista em vez de tabela "de Excel".
- Base à **esquerda** do nome, com a cor da base (`--tipo-pN`).
- **Vaga vazia:** fundo `--vaga-vazia-fundo`, texto `--vaga-vazia` (azul). **Extra:** fundo laranja claro (`--folguista-fundo`).
- No topo, **faixa de números** ("N vagas · N ocupadas · N vazias · N extras") em vez de cartões de indicador.

### 5.9 Avisos, diálogos e carregamento

- Banners com fundo semântico e texto na cor correspondente.
- Toasts: canto superior direito, branco translúcido com `backdrop-filter: blur(10px)`, cantos de 12 px, borda colorida pelo tipo.
- Confirmações por **diálogo do sistema**, nunca `window.confirm`; botão vermelho quando a ação é destrutiva.
- Campos de formulário **sem ícone na frente**; sem `hint` que só repete o rótulo.
- Carregamento: **`q-skeleton` no formato da tela** em vez de spinner solto.

### 5.10 Ícones

- Material Icons (pacote do Quasar). Só onde ajudam a reconhecer (menu lateral, botões só-ícone).

---

## 6. Tela de login (vitrine da marca)

- **Cabeçalho** claro translúcido (`rgba(255,255,255,.85)`, desfoque 12 px): logo colorido, "Gerenciador de Equipes" em Inter 800, "CGB ENERGIA" em maiúsculas pequenas, selo "Sistema online", tema e ajuda.
- **Tela em duas partes** (`.tela-login` em grid):
  - **Faixa lateral da CGB à esquerda** (`.faixa-cgb`, 38% da largura, mínimo 340 px):
    - degradê `linear-gradient(160deg, #4E0B17 0%, #711424 50%, #A8304A 100%)` (escuro: `#2A0A10 → #4A0D18 → #6A1729`), lisa, **sem plexus**;
    - logo **branco** (`logo-cabecalho.png`) com 168 px no topo;
    - no meio: selo "Acesso restrito às equipes autorizadas" (branco translúcido, borda `rgba(255,255,255,.28)`), título "Gestão de **Equipes**" em Inter 800 branco (`clamp(2.6rem, 4.2vw, 3.8rem)`), com "Equipes" em rosa claro `#FFD6E0`, e a frase de apoio em branco a 78%;
    - rodapé "CGB ENERGIA" em maiúsculas pequenas, branco a 60%;
    - marca-d'água do losango em branco a **7%**, grande, vazando no canto inferior direito.
  - **Área do login à direita** (`.area-login`): o plexus animado por trás e o cartão de login centralizado (até 420 px).
- **Celular (< 900 px):** a faixa vira um **topo baixo só com o logo branco** (112 px); mensagem e rodapé somem; o formulário fica embaixo.
- **Cartão:** branco translúcido (`rgba(255,255,255,.88)`), **faixa de 4 px no topo** em degradê `#711424 → #8D2136 → #E57C94`, logo de 56 px, sombra `0 30px 60px -15px rgba(37,4,13,.45)` e halo radial bordô atrás.
- **Plexus gerado em código** (não é vídeo): `canvas` 2D só na área da direita, medido pelo contêiner (`ResizeObserver`), com pontos flutuando devagar ligados por linhas finas quando ficam perto e pequenos losangos (ladrilhos `#5D0C1E`, `#6B1025`, `#7D132C`, `#8E1834`, `#9F1C3C`); linhas `rgb(213,77,110)`, pontos `rgb(229,124,148)`, destaques `rgb(255,214,224)`. A quantidade de pontos é sorteada para uma tela de 1366×768 e reduzida na proporção da área, para manter a mesma densidade em telas menores.

---

## 7. Tema escuro

- Botão sol/lua no cabeçalho; a escolha fica salva e é aplicada **antes da primeira tela**, sem piscar.
- Fundos marrom-avinhados (`#171314`, `#221C1E`, `#2B2325`), bordas âmbar translúcido — não é cinza neutro.
- Textos coloridos clareiam (`--marca-texto` `#F0A3B3`, positivo `#6CC79A`, negativo `#F08A80`).
- Chips tonais e segmentado usam a cor a 22% sobre a superfície e texto clareado.
- No Quasar, sobrescreva `--q-dark` e `--q-dark-page`; as cores fixas (`grey-3`, `text-grey-*`, `bg-red-1`...) são remapeadas para os tokens.

---

## 8. Pronto para copiar

```css
:root {
  --marca: #711424;
  --marca-clara: #8d2136;
  --marca-texto: #8d2136;
  --titulo: #4f1723;
  --fundo: #f2eeef;
  --superficie: #ffffff;
  --superficie-2: #faf7f8;
  --tinta: #2d2527;
  --tinta-fraca: #6d5f63;
  --neutro: #7a6c70;
  --linha: rgba(113, 20, 36, 0.16);
  --linha-forte: rgba(113, 20, 36, 0.32);
  --positivo: #1b6b45;
  --positivo-fundo: #e6f2ea;
  --negativo: #b3261e;
  --negativo-fundo: #fbe9e7;
  --afastado: #8a5a00;
  --afastado-fundo: #fdf0cd;
  --folguista: #c9741b;
  --folguista-fundo: #fbeedd;
  --vaga-vazia: #2f5d8a;
  --vaga-vazia-fundo: #e3ecf5;
  --realce: #f7e9d7;
  --raio: 14px;
  --sombra: 0 1px 3px rgba(65, 32, 38, 0.1), 0 6px 14px rgba(65, 32, 38, 0.1), 0 16px 36px rgba(65, 32, 38, 0.12);
  --gradiente-marca: linear-gradient(100deg, #4e0b17 0%, #711424 45%, #a8304a 100%);
  --fonte-ui: 'Barlow Semi Condensed', 'Segoe UI', sans-serif;
  --fonte-texto: 'Inter', 'Segoe UI', sans-serif;
}

/* tema escuro: no Quasar a classe é body.body--dark */
body.body--dark {
  --q-dark: #221c1e;
  --q-dark-page: #171314;
  --marca: #7c1a2c;
  --marca-clara: #99283f;
  --marca-texto: #f0a3b3;
  --titulo: #f2dbe0;
  --fundo: #171314;
  --superficie: #221c1e;
  --superficie-2: #2b2325;
  --tinta: #f1e9ea;
  --tinta-fraca: #b7a6aa;
  --neutro: #9c8b90;
  --linha: rgba(212, 154, 85, 0.2);
  --linha-forte: rgba(212, 154, 85, 0.38);
  --positivo: #6cc79a;
  --positivo-fundo: #1e3329;
  --negativo: #f08a80;
  --negativo-fundo: #3d2321;
  --afastado: #e0b84c;
  --afastado-fundo: #3d3218;
  --folguista: #e0a259;
  --folguista-fundo: #3b2c1c;
  --realce: #382a1c;
  --sombra: 0 1px 3px rgba(0, 0, 0, 0.4), 0 6px 14px rgba(0, 0, 0, 0.35), 0 16px 36px rgba(0, 0, 0, 0.4);
}

/* chip tonal */
.chip-tonal {
  background: color-mix(in srgb, var(--cor-chip) 11%, var(--superficie));
  color: color-mix(in srgb, var(--cor-chip) 88%, #000);
  border-radius: 10px;
  font-weight: 700;
}
.chip-tonal__num {
  display: inline-grid; place-items: center;
  min-width: 22px; height: 20px; padding: 0 5px; margin-right: 6px;
  border-radius: 6px; font-weight: 800;
  background: color-mix(in srgb, var(--cor-chip) 20%, transparent);
}
body.body--dark .chip-tonal {
  background: color-mix(in srgb, var(--cor-chip) 22%, var(--superficie));
  color: color-mix(in srgb, var(--cor-chip) 45%, #fff);
}
```

### Arquivos a levar para o novo projeto

| Arquivo | Para quê |
|---|---|
| `frontend/public/icons/*` | Logos e favicons |
| `frontend/public/fonts/*.woff2` | Fontes (Barlow Semi Condensed e Inter) |
| `frontend/src/css/app.scss` | Tokens, temas, chips tonais, filtros e estilos de componente |
| `frontend/src/css/quasar.variables.scss` | Cores do Quasar |
| `frontend/src/components/CabecalhoApp.vue` + `composables/useMenuLateral.js` | Cabeçalho e menu lateral |
| `frontend/src/components/SelectFiltroMultiplo.vue` | Filtro em pílula |
| `frontend/src/components/MarcaDaguaFundo.vue` | Marca-d'água |
| `frontend/src/composables/useModoNoturno.js` e `frontend/src/boot/tema.js` | Tema sem piscar |

---

## 9. Resumo em uma linha

**Bordô `#711424` na moldura (cabeçalho, menu lateral em degradê, cabeçalho de tabela, faixa lateral do login); miolo liso com cores tonais e só com significado; neutros quentes; Barlow Semi Condensed nos títulos e Inter no texto; filtros em pílula, chips com número, botões sem ícone; o losango como marca-d'água; claro e escuro com o mesmo tom quente.**
