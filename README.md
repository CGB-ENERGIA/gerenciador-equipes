# Gerenciador de Equipes

Sistema para administrar equipes, vagas, colaboradores e alocações.

- **Backend:** Flask + SQLAlchemy (`app.py`, `auth.py`), banco Postgres na Neon.
- **Frontend:** Vue 3 + Quasar (`frontend/`), roteador em modo hash (`/#/...`).
- **Hospedagem:** Vercel. O frontend compilado (`frontend/dist/spa`) é servido
  como site estático e a API (`/api/*`) roda como função serverless em
  `api/index.py`, que só importa o `app` do `app.py`. Detalhes em
  [DEPLOY.md](DEPLOY.md).

## Telas

| Tela | Arquivo | Permissão |
|---|---|---|
| Login | `frontend/src/pages/login.vue` | — |
| Resumo (`/`, `/resumo`) | `frontend/src/pages/index.vue` | `ver_resumo` |
| Banco de Dados | `frontend/src/pages/banco-dados.vue` | `ver_equipes` |
| Cadastro de Vagas | `frontend/src/pages/cadastro-vagas.vue` | `gerenciar_vagas` |
| Usuários | `frontend/src/pages/usuarios.vue` | `gerenciar_usuarios` |

## Configuração local

1. Crie um ambiente virtual e instale as dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Copie `.env.example` para `.env` e preencha `DATABASE_URL` e `SECRET_KEY`.

3. Rode as migrations de `migrations/` em ordem numérica (ver abaixo).

4. Suba a API:

```powershell
python app.py
```

A API responde em `http://127.0.0.1:5000`. Ela **não** serve o frontend: para
ver as telas, rode `npm run dev` dentro de `frontend/`, ou use `vercel dev`,
que reproduz o ambiente de produção (build + função da API + redirects do
`vercel.json`).

`AUTO_CREATE_SCHEMA=true` cria as tabelas automaticamente. Use só em bancos
descartáveis.

## Migrations

Não há Alembic nem tabela de controle: cada arquivo é aplicado à mão, em
ordem, e quase todos usam `IF NOT EXISTS`, então rodar de novo não quebra
nada. Cada arquivo traz no cabeçalho o que conferir antes de rodar.

- `001_add_unique_team.sql`: impede duas equipes com a mesma BASE + PREFIXO.
- `002_add_unique_membro_chapa.sql`: impede o mesmo colaborador em duas vagas.
- `003_add_setor_supervisor_coordenador.sql`: SETOR, SUPERVISOR e COORDENADOR por vaga.
- `004_add_usuarios.sql`: usuários do sistema e os vínculos de cada um.
- `005_add_origem_vaga.sql`: marca a vaga como PADRAO ou EXTRA (Folguista Extra).
- `006_renomear_mestre_para_administrador.sql`: nível MESTRE vira ADMINISTRADOR.
- `007_add_niveis_permissoes.sql`: permissões por nível, personalizáveis pelo Administrador.
- `008_add_hierarquia_usuarios.sql`: hierarquia Gerente → Coordenador → Supervisor (`RESPONSAVEL_ID`).
- `009_add_indice_equipe_id.sql`: índice em `composicoes_equipes.equipe_id`.
- `010_add_secao_tratada_tipo_ccusto.sql`: SEÇÃO_TRATADA e TIPO_CCUSTO em colaboradores (ver `database/depara.py`). Depois de aplicar, rode `python -m database.importacao.recalcular_secao_tipo_ccusto`.
- `011_add_afastado.sql`: status de afastado do colaborador, com justificativa.
- `012_add_tipo_funcao.sql`: TIPO_FUNÇÃO (DIRETO/INDIRETO). Só colaboradores DIRETO aparecem como disponíveis para alocação.
- `013_add_tentativas_login.sql`: registra tentativas de login que falharam, para o limite contra força bruta.
- `014_add_afastado_por.sql`: quem marcou o colaborador como afastado e quando (coluna "Afastado por" nas tabelas). **Rode antes de publicar o código**: sem essas colunas, as consultas de colaboradores falham.

## Acesso

Toda a API exige login, exceto `/api/login`, `/api/logout`, `/api/sessao` e `/api/status`.
Para criar o primeiro usuário, ou recuperar o acesso se ninguém mais consegue
entrar:

```powershell
.\.venv\Scripts\python.exe -m database.criar_usuario_administrador
```

A senha vai para o banco só como hash (scrypt), nunca em texto puro.

### Níveis

Definidos em `auth.py`, em `NIVEIS`. A tela de Usuários lê essa tabela, então
um nível novo aparece no formulário sem mexer no frontend.

| Nível | Permissões padrão | Escopo |
|---|---|---|
| `ADMINISTRADOR` | todas (fixas, não editáveis) | ignora vínculos: vê tudo |
| `GERENTE` | ver resumo/equipes, alocar, editar e remover alocação | herda o escopo dos Coordenadores e Supervisores abaixo dele |
| `COORDENADOR` | idem | herda o escopo dos Supervisores abaixo dele |
| `SUPERVISOR` | idem | só os próprios vínculos |

As permissões de Gerente, Coordenador e Supervisor podem ser personalizadas
em **Usuários > Níveis de acesso** (tabela `niveis_permissoes`). Sem
personalização, valem as do código. O nível `ANALISTA` foi descontinuado
(migration 008).

### Vínculos e hierarquia

- Os **vínculos** dizem quais equipes o usuário enxerga. São pares TIPO/VALOR:
  `BASE`, `TIPO_EQUIPE`, `SETOR` e `EQUIPE` (id de uma equipe específica).
- Cada tipo de vínculo só restringe se estiver cadastrado. Quem tem apenas
  `SETOR=GSTC` vê todo o GSTC, em qualquer base. Quem tem `BASE=BACABAL` +
  `TIPO_EQUIPE=CONSTRUÇÃO` vê só a construção de Bacabal. Os filtros
  presentes valem todos ao mesmo tempo (`auth._escopo_cobre`).
- **Sem nenhum vínculo, o usuário não vê nada.** A regra falha fechada, para
  que uma conta sem escopo nunca vire um curinga.
- A hierarquia é o campo **"Responde a"** (`RESPONSAVEL_ID`): um Supervisor
  responde a um Coordenador, e um Coordenador a um Gerente. Gerente e
  Coordenador enxergam o que **cada** Supervisor abaixo deles enxerga, avaliado
  pessoa a pessoa, mais o vínculo da própria conta. A soma não é misturada,
  para não liberar combinações de base e tipo que nenhum Supervisor tem
  sozinho (`auth.escopos_efetivos`).
- Os vínculos decidem o que o usuário **vê** no Resumo, no Banco de Dados e no
  Cadastro de Vagas (`auth.equipe_visivel`). Já **alocar, editar e remover**
  dependem só da permissão do nível (`auth.pode_realizar_operacao`). Assim um
  Supervisor consegue transferir um colaborador que está numa vaga de outra
  disciplina: a tela mostra de onde ele sai e pede confirmação antes de mover.

### Sessão e login

- `SECRET_KEY` assina o cookie de sessão, que dura 12 horas e é `HttpOnly`,
  `SameSite=Lax` e `Secure` na Vercel. Trocar a chave desloga todo mundo; sem
  ela, cada instância gera a própria chave e as sessões caem de forma
  imprevisível.
- **Limite de tentativas:** 5 falhas por login ou 30 por IP em 15 minutos
  bloqueiam novas tentativas (HTTP 429) até a janela passar. As falhas ficam no
  banco (`tentativas_login`), porque na Vercel cada requisição pode cair numa
  instância diferente. Um login bem-sucedido zera o contador daquele usuário.
  Quem tem `gerenciar_usuarios` vê o selo **bloqueado** na tela de Usuários e
  pode liberar a conta na hora pelo cadeado (`POST /api/usuarios/<id>/desbloquear`).
  O limite por IP não é liberado por conta: ele cai sozinho quando a janela passa.
  A troca da própria senha (`/api/minha-senha`) tem o mesmo limite para a
  senha atual. Se a migration 013 não tiver sido aplicada, o limite
  simplesmente não atua, e o login continua funcionando.
- O filtro de base das telas Resumo e Banco de Dados fica salvo no navegador,
  separado por usuário, e é apagado ao sair.
- Depois do login, a tela volta para a página que a pessoa tentou abrir
  (parâmetro `destino`). Só são aceitos caminhos internos do sistema.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -q
```

Os testes não tocam o banco: as regras são exercitadas com objetos de
mentira, então podem rodar com o `.env` apontando para produção. Não há
testes automatizados do frontend.
