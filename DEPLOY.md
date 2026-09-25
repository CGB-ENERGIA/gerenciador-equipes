# Deploy na Vercel

O sistema roda na Vercel, com o banco Postgres na Neon.

## Como está dividido

- **Frontend** (`frontend/dist/spa`, gerado pelo `npm run build`): publicado
  como site estático, servido pelo CDN da Vercel. O Flask não participa
  disso.
- **API** (`/api/*`): uma função Python só, `api/index.py`, que importa o
  `app` do `app.py`. O `vercel.json` manda todo `/api/*` para essa função.
- **`/resumo`**: redirect declarado no `vercel.json` para `/#/resumo`.
- **Pool de conexão do banco** (`database/database.py`): `pool_size`
  reduzido, porque em serverless cada instância abre o próprio pool. A
  `DATABASE_URL` usa o endpoint `-pooler` da Neon, que absorve picos de
  várias instâncias abrindo conexão ao mesmo tempo.

O router do Vue usa **modo hash** (`/#/...`), então não é preciso regra de
rewrite para rotas do frontend, só a do `/api/*`.

## Publicar

Com o projeto da Vercel ligado ao repositório `CGB-ENERGIA/gerenciador-equipes`,
todo push na `main` gera um deploy novo. O `vercel.json` na raiz declara `buildCommand`,
`outputDirectory`, a função de API e o redirect do `/resumo`.

**Antes de publicar código que depende de uma migration nova, rode a
migration no Neon.** Não há controle automático de migrations (ver README):
se o código chegar antes, as rotas que usam a coluna ou tabela nova falham.

### Variáveis de ambiente

Em Project Settings > Environment Variables:

- `DATABASE_URL`: connection string da Neon (com `-pooler`).
- `SECRET_KEY`: assina o cookie de sessão. Precisa ser fixa: sem ela, cada
  instância gera a própria chave e as sessões caem de forma imprevisível.
  Gere com `python -c "import secrets; print(secrets.token_hex(32))"`.

## Pontos a validar

- **Arquivo extra na função**: `database/depara.py` lê em runtime
  `database/importacao/depara_cadastro.json`. Se o `/api/status` responder
  500 puxando esse JSON, confira na documentação atual da Vercel como incluir
  arquivos extras na função.
- **Tamanho de upload**: a Vercel limita o corpo da requisição a 4,5 MB, e a
  aplicação recusa antes, com mensagem própria, qualquer upload acima de
  4 MB (`MAX_CONTENT_LENGTH` no `app.py`).
- **Tempo de execução**: se algum endpoint pesado (planilha grande,
  `edicao-massa`) esbarrar no timeout padrão da função, ajuste `maxDuration`
  no `vercel.json` depois de medir.

## Testar localmente antes de subir

- `python app.py` sobe só a API em `http://127.0.0.1:5000`, sem servir o
  frontend.
- `vercel dev` (Vercel CLI) reproduz o comportamento de produção localmente
  (build do frontend, função da API e redirects do `vercel.json`). É o jeito
  mais fiel de pegar problema de configuração antes do deploy real.
