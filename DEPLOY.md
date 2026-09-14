# Deploy no Vercel

Esta é a cópia do "Gerenciador de Equipes" adaptada para o Vercel — o
projeto original (mesmo código, hospedado no Render) continua em
`../gerenciador-equipes`, sem nenhuma alteração. As duas hospedagens
apontam para a **mesma base Neon**; nenhum dado é duplicado, só a
aplicação.

## O que é diferente daqui pro projeto original

O Render mantém um processo Flask rodando o tempo todo, e esse processo
também serve os arquivos do frontend (`send_from_directory`). O Vercel é
serverless — cada chamada de API roda numa função isolada, de vida curta —
então a divisão de trabalho mudou:

- **Frontend** (`frontend/dist/spa`, gerado pelo `npm run build`): publicado
  como site estático, servido pelo CDN do Vercel. O Flask não participa
  disso aqui — as rotas que serviam `/assets`, `/fonts`, `/icons`,
  `/videos`, `/favicon.ico` e `/` foram removidas do `app.py` desta cópia
  (ver comentário no lugar onde elas estavam).
- **API** (`/api/*`): uma função Python só, `api/index.py`, que importa o
  `app` do `app.py` — mesma lógica de rotas, autenticação (`auth.py`) e
  acesso ao banco do projeto original, sem duplicar nada. `vercel.json`
  manda todo `/api/*` pra essa função.
- **`/resumo`**: no projeto original é uma rota Flask que redireciona pra
  `/#/resumo`. Aqui virou um `redirect` declarado direto no `vercel.json`
  (não precisa de Python pra isso).
- **Pool de conexão do banco** (`database/database.py`): `pool_size`
  reduzido — serverless não deve manter conexões ociosas abertas por
  instância. A `DATABASE_URL` continua a mesma (já usa o endpoint
  `-pooler` da Neon, que é quem absorve picos de várias instâncias abrindo
  conexão ao mesmo tempo).
- **`SECRET_KEY`**: gerada uma chave nova e independente da do Render — as
  duas hospedagens não compartilham sessão de login entre si.

O router do Vue já usa **modo hash** (`/#/...`), então não foi preciso
nenhuma regra de rewrite pra rota "coringa" — só o `/api/*` acima.

## Passo a passo

1. **Repositório**: este projeto precisa do próprio repositório Git (já
   inicializado nesta pasta, `git init` feito). Criar um repo novo no
   GitHub — **não** reaproveitar o `igcarvalh0/Cadastro` do projeto
   original — e dar push.

2. **No Vercel**: New Project > importar esse repositório. O
   `vercel.json` na raiz já declara `buildCommand`, `outputDirectory`,
   a função de API e o redirect do `/resumo` — o Vercel deve detectar tudo
   sozinho ao importar.

3. **Environment Variables** (Project Settings > Environment Variables):
   - `DATABASE_URL` — mesma connection string da Neon do `.env` local
     (com `-pooler`).
   - `SECRET_KEY` — o valor gerado no `.env` local desta cópia.

4. Deploy.

## Pontos a validar depois do primeiro deploy (não testados ainda)

- **`runtime: "python3.12"` no `vercel.json`**: a sintaxe exata de runtime
  Python e de "incluir arquivo extra" (`database/importacao/depara_cadastro.json`
  precisa viajar junto com a função, é lido em runtime por
  `database/depara.py`) muda de tempo em tempo na documentação do Vercel —
  conferir a doc atual deles antes de assumir que subiu certo. Se o build
  reclamar do runtime ou o `/api/status` responder 500 puxando esse JSON,
  é o primeiro lugar a olhar.
- **Tamanho de upload das planilhas**: funções serverless costumam ter um
  limite de tamanho de corpo de requisição (varia por plano). Testar a
  importação de planilha (`/api/equipes/planilha/aplicar`,
  `/api/colaboradores/planilha/aplicar`, `/api/usuarios/planilha/aplicar`)
  com um arquivo do tamanho real usado na operação, não um de teste
  pequeno.
- **Tempo de execução**: mesma ideia — se algum endpoint pesado
  (planilha grande, `edicao-massa`) demorar, pode esbarrar no timeout
  padrão de função do Vercel. Ajustar `maxDuration` no `vercel.json` se
  precisar, depois de medir.
- **Rodar os dois ao mesmo tempo**: Render e Vercel na mesma Neon não
  deveriam conflitar (HTTP sem estado compartilhado no lado da aplicação),
  mas vale confirmar na prática com um teste de uso simultâneo.

## Testar localmente antes de subir

- `python app.py` sobe só a API em `http://127.0.0.1:5000` (sem servir o
  frontend — ver comentário no fim do `app.py`).
- `vercel dev` (Vercel CLI) reproduz o comportamento de produção
  localmente — build do frontend + função da API + rewrites/redirects do
  `vercel.json` — é o jeito mais fiel de pegar problema de configuração
  antes do deploy real.
