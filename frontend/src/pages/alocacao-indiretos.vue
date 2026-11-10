<template>
  <q-layout view="lHh Lpr lFf">
    <MarcaDaguaFundo />

    <CabecalhoApp titulo="Indiretos" :carregando="carregando" @atualizar="carregar" />

    <q-page-container>
      <q-page class="q-pa-md">
        <!-- ================================================== -->
        <!-- CABEÇALHO -->
        <!-- ================================================== -->

        <div class="row items-end q-col-gutter-md q-mb-md">
          <div class="col">
            <div class="text-h5">Alocação de Indiretos</div>
            <div class="text-subtitle2 text-grey-7">
              Pessoal indireto por setor, base e responsável, com as vagas do BID
            </div>
          </div>

          <!-- um botão só: o diálogo baixa a planilha atual e recebe a preenchida -->
          <div v-if="podeEditar" class="col-auto">
            <q-btn
              class="btn-exportar"
              color="positive"
              text-color="white"
              no-caps
              label="Planilha"
              @click="abrirPlanilha"
            />
          </div>
        </div>

        <q-banner v-if="erro" class="bg-red-1 text-negative q-mb-md" rounded>
          {{ erro }}
        </q-banner>

        <q-banner v-if="sucesso" class="bg-green-1 text-positive q-mb-md" rounded>
          {{ sucesso }}
        </q-banner>

        <!-- ================================================== -->
        <!-- FILTROS -->
        <!-- ================================================== -->

        <q-card flat bordered class="q-mb-md barra-filtros">
          <q-card-section>
            <div class="row items-center q-col-gutter-md">
              <div class="col-12 col-sm-6 col-md">
                <SelectFiltroMultiplo
                  :model-value="filtroBases"
                  :options="opcoesBases"
                  icon="place"
                  label="Base"
                  @update:model-value="v => (filtroBases = proximaSelecaoMultipla(filtroBases, v, TODOS))"
                />
              </div>

              <div class="col-12 col-sm-6 col-md">
                <SelectFiltroMultiplo
                  :model-value="filtroSetores"
                  :options="opcoesSetores"
                  icon="apartment"
                  label="Setor"
                  @update:model-value="v => (filtroSetores = proximaSelecaoMultipla(filtroSetores, v, TODOS))"
                />
              </div>

              <div class="col-12 col-sm-6 col-md">
                <SelectFiltroMultiplo
                  :model-value="filtroSubsetores"
                  :options="opcoesSubsetores"
                  icon="account_tree"
                  label="Subsetor"
                  @update:model-value="
                    v => (filtroSubsetores = proximaSelecaoMultipla(filtroSubsetores, v, TODOS))
                  "
                />
              </div>

              <div class="col-12 col-sm-6 col-md">
                <SelectFiltroMultiplo
                  :model-value="filtroResponsaveis"
                  :options="opcoesResponsaveis"
                  icon="supervisor_account"
                  label="Responsável"
                  @update:model-value="
                    v => (filtroResponsaveis = proximaSelecaoMultipla(filtroResponsaveis, v, TODOS))
                  "
                />
              </div>

              <div class="col-auto">
                <q-btn
                  flat
                  dense
                  rounded
                  no-caps
                  icon="filter_alt_off"
                  label="Limpar filtros"
                  color="grey-8"
                  @click="limparFiltros"
                />
              </div>
            </div>

            <q-separator class="q-my-md" />

            <div class="row items-center q-col-gutter-md q-mt-none">
              <div class="col-12 col-md-4">
                <q-input
                  v-model="busca"
                  outlined
                  dense
                  clearable
                  placeholder="Nome, chapa ou função..."
                >
                  <template #prepend>
                    <q-icon name="search" />
                  </template>
                </q-input>
              </div>
              <q-space />
              <div class="col-auto">
                <q-btn
                  color="primary"
                  no-caps
                  label="Organograma geral"
                  @click="abrirVisaoGeral"
                />
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- ================================================== -->
        <!-- INDICADORES (pessoas e vagas do BID) -->
        <!-- ================================================== -->

        <!-- uma linha de números; clicar num deles filtra (de novo, limpa) -->
        <div class="faixa-indicadores q-mb-md">
          <button
            v-for="indicador in indicadores"
            :key="indicador.chave"
            type="button"
            class="faixa-indicadores__item"
            :class="[
              `faixa-indicadores__item--${indicador.chave || 'todos'}`,
              { 'faixa-indicadores__item--ativo': filtroStatus === indicador.chave && indicador.chave }
            ]"
            @click="alternarStatus(indicador.chave)"
          >
            <span class="faixa-indicadores__valor">{{ indicador.valor }}</span>
            <span class="faixa-indicadores__rotulo">{{ indicador.rotulo.toLowerCase() }}</span>
          </button>
        </div>

        <!-- ================================================== -->
        <!-- CONTEÚDO -->
        <!-- ================================================== -->

        <!-- carregando: o formato da tela, para ela não pular quando os dados chegam -->
        <div v-if="carregando && primeiraCarga" class="mural-setores" aria-busy="true">
          <div v-for="n in 4" :key="n" class="mural-setores__item">
            <q-card flat bordered class="cartao-setor q-pa-md">
              <q-skeleton type="text" width="40%" class="q-mb-sm" />
              <q-skeleton type="text" width="25%" class="q-mb-md" />
              <div v-for="l in 6" :key="l" class="row no-wrap q-gutter-sm q-mb-xs">
                <q-skeleton type="text" width="30%" />
                <q-skeleton type="text" width="12%" />
                <q-skeleton type="text" class="col" />
              </div>
            </q-card>
          </div>
        </div>

        <div v-else class="row q-col-gutter-md">
          <!-- SETORES -->
          <div :class="podeEditar ? 'col-12 col-lg-8 coluna-setores' : 'col-12'">
            <div class="row items-center q-mb-sm">
              <div class="text-h6">Setores</div>
              <q-chip dense class="q-ml-sm">{{ gruposSetor.length }}</q-chip>
            </div>

            <div v-if="!gruposSetor.length" class="estado-vazio">
              <q-icon name="search_off" size="40px" />
              <div>
                {{
                  pessoas.some(p => p.alocacao)
                    ? 'Nenhum setor com esses filtros.'
                    : podeEditar
                      ? 'Ninguém alocado ainda. Use "Alocar" na lista ao lado ou o botão "Planilha".'
                      : 'Ninguém alocado ainda.'
                }}
              </div>
            </div>

            <!--
              Mural: duas colunas que empilham os cartões sem deixar buraco
              (cada cartão tem a altura do próprio conteúdo). A ordem segue
              coluna a coluna.
            -->
            <div class="mural-setores">
              <!--
                Um cartão por SETOR; dentro, uma seção por BASE; dentro da base,
                as pessoas agrupadas por RESPONSÁVEL (o responsável é por
                pessoa — pode haver mais de um no mesmo setor e base).
              -->
              <div
                v-for="grupo in gruposSetor"
                :key="grupo.nome"
                class="mural-setores__item"
              >
                <q-card class="cartao-setor">
                  <div class="cartao-setor__faixa" />

                  <q-card-section class="q-pb-sm">
                    <div class="row items-center no-wrap">
                      <div>
                        <div class="cartao-setor__nome">{{ grupo.nome }}</div>
                        <div class="text-caption">
                          {{ grupo.bases.length }}
                          {{ grupo.bases.length === 1 ? 'base' : 'bases' }}
                        </div>
                        <!-- BID do setor em texto; quem edita clica para definir as vagas -->
                        <button
                          v-if="textoResumoVagas(grupo.nome) || podeEditar"
                          type="button"
                          class="resumo-vagas"
                          :disabled="!podeEditar"
                          @click="abrirVagasDoSetor(grupo.nome)"
                        >
                          {{ textoResumoVagas(grupo.nome) || 'Definir vagas do BID' }}
                        </button>
                      </div>

                      <div class="col q-px-md">
                        <button
                          v-if="grupo.responsavelPrincipal"
                          type="button"
                          class="responsavel-chip"
                          :disabled="!podeEditar"
                          @click="abrirTrocaResponsavel(grupo.responsavelPrincipal)"
                        >
                          <span v-if="grupo.responsavelPrincipal.responsavel" class="responsavel-chip__texto">
                            <strong>{{ nomeCurto(grupo.responsavelPrincipal.responsavel.nome) }}</strong>
                            <small>
                              {{ grupo.responsavelPrincipal.responsavel.chapa }}
                              <template v-if="grupo.responsavelPrincipal.responsavel.funcao">
                                · {{ grupo.responsavelPrincipal.responsavel.funcao }}
                              </template>
                            </small>
                          </span>
                          <span v-else class="sem-responsavel">Definir responsável</span>
                          <q-icon
                            v-if="podeEditar"
                            name="edit"
                            size="14px"
                            class="responsavel-chip__editar"
                          />
                          <q-tooltip v-if="podeEditar">
                            Responsável mais alto do setor · clique para trocar quem responde direto a ele
                          </q-tooltip>
                        </button>
                      </div>

                      <q-btn
                        flat
                        round
                        dense
                        icon="account_tree"
                        color="primary"
                        class="q-mr-sm"
                        aria-label="Ver como organograma"
                        @click="abrirOrganograma(grupo)"
                      >
                        <q-tooltip>Ver como organograma</q-tooltip>
                      </q-btn>

                      <div class="cartao-setor__contagem">
                        <div class="cartao-setor__numero">{{ grupo.total }}</div>
                        <div class="cartao-setor__legenda">
                          {{ grupo.total === 1 ? 'pessoa' : 'pessoas' }}
                        </div>
                      </div>
                    </div>
                  </q-card-section>

                  <!--
                    Como o BID: uma linha por vaga, na ordem do BID (ocupada ou
                    vazia), e no fim os extras. Base ao lado do nome; a função
                    real fica à direita, só em texto. Setor sem BID: as pessoas
                    pelo nome.
                  -->
                  <q-list class="lista-pessoas lista-bid">
                    <q-item
                      v-for="linha in linhasDoCartao(grupo)"
                      :key="linha.chave"
                      dense
                      class="linha-bid"
                      :class="{
                        'linha-vaga-vazia': !linha.pessoa,
                        'linha-extra': linha.extra,
                        'linha-afastado': linha.pessoa?.afastado
                      }"
                    >
                      <q-item-section avatar class="secao-chapa">
                        <span class="chapa-pessoa" :class="{ 'chapa-pessoa--vazia': !linha.pessoa }">
                          {{ linha.pessoa ? linha.pessoa.chapa : '—' }}
                        </span>
                      </q-item-section>

                      <!-- BID: o cargo previsto da vaga; extra = em branco -->
                      <q-item-section v-if="setoresComBid.has(grupo.nome)" side class="secao-bid">
                        <span class="bid-pessoa" :title="linha.vaga ? linha.vaga.funcao : 'Extra: sem vaga no BID'">
                          {{ linha.vaga ? linha.vaga.funcao : '' }}
                        </span>
                      </q-item-section>

                      <q-item-section>
                        <!-- base à esquerda do nome, na mesma linha -->
                        <q-item-label class="row items-center no-wrap">
                          <span
                            class="base-pessoa"
                            :class="{ 'base-pessoa--vazia': !(linha.pessoa ? linha.pessoa.alocacao.base : linha.vaga.base) }"
                            :style="{ '--cor-base': corDaBase(linha.pessoa ? linha.pessoa.alocacao.base : linha.vaga.base) }"
                          >
                            {{ (linha.pessoa ? linha.pessoa.alocacao.base : linha.vaga.base) || '—' }}
                          </span>
                          <span
                            v-if="linha.pessoa"
                            v-caber-na-linha
                            class="col nome-pessoa"
                            :title="[linha.pessoa.nome, linha.pessoa.alocacao.observacao].filter(Boolean).join(' · ')"
                          >
                            {{ linha.pessoa.nome }}
                          </span>
                          <span v-else class="col texto-vaga-vazia">vaga vazia</span>
                        </q-item-label>
                      </q-item-section>

                      <q-item-section side>
                        <div class="row items-center no-wrap linha-bid__direita">
                          <template v-if="linha.pessoa">
                            <span v-if="linha.pessoa.afastado" class="marca-afastado">afastado</span>
                            <span v-if="linha.extra" class="marca-extra">extra</span>
                            <span
                              class="funcao-real"
                              :title="
                                linha.pessoa.alocacao.funcao
                                  ? `${linha.pessoa.alocacao.funcao} (no cadastro: ${linha.pessoa.funcao || '—'})`
                                  : linha.pessoa.funcao
                              "
                            >
                              {{ funcaoExibida(linha.pessoa) }}
                            </span>
                          </template>
                          <template v-if="podeEditar">
                            <!-- alocar nas vagas direto na linha -->
                            <button
                              v-if="!linha.pessoa"
                              type="button"
                              class="acao-texto"
                              @click="abrirOcuparVaga(linha.vaga)"
                            >
                              Ocupar
                            </button>
                            <button
                              v-else-if="linha.extra && vagasVaziasDoSetor(grupo.nome).length"
                              type="button"
                              class="acao-texto"
                              @click="abrirPorNaVaga(linha.pessoa)"
                            >
                              Pôr na vaga
                            </button>
                            <q-btn
                              v-if="linha.pessoa"
                              flat
                              round
                              dense
                              icon="edit"
                              size="sm"
                              class="linha-bid__editar"
                              aria-label="Editar colaborador"
                              @click="abrirAlocacao(linha.pessoa)"
                            >
                              <q-tooltip>Editar colaborador</q-tooltip>
                            </q-btn>
                          </template>
                        </div>
                      </q-item-section>
                    </q-item>
                  </q-list>

                  <q-card-actions v-if="podeEditar">
                    <q-btn
                      flat
                      no-caps
                      color="primary"
                      label="Adicionar pessoa"
                      @click="abrirAdicionarNoSetor(grupo.nome)"
                    />
                  </q-card-actions>
                </q-card>
              </div>
            </div>
          </div>

          <!-- SEM SETOR (só para quem edita: é a lista de quem falta alocar) -->
          <div v-if="podeEditar" class="col-12 col-lg-4 coluna-sem-setor">
            <q-card class="cartao-sem-setor">
              <q-card-section>
                <div class="row items-center no-wrap">
                  <div class="text-h6">Sem setor</div>
                  <q-chip dense class="q-ml-sm bg-orange-1">
                    {{ semSetorFiltrados.length }}
                  </q-chip>
                  <!-- busca só desta lista (soma com a busca geral do topo) -->
                  <q-input
                    v-model="buscaSemSetor"
                    dense
                    outlined
                    clearable
                    placeholder="Pesquisar..."
                    class="col q-ml-sm"
                  >
                    <template #prepend><q-icon name="search" size="18px" /></template>
                  </q-input>
                </div>
                <div class="text-caption ellipsis q-mt-xs">
                  Ainda não alocados. Clique para alocar.
                </div>
              </q-card-section>

              <q-separator />

              <q-list separator class="lista-sem-setor">
                <q-item
                  v-for="pessoa in semSetorFiltrados"
                  :key="pessoa.chapa"
                  clickable
                  :class="{ 'linha-afastado': pessoa.afastado }"
                  @click="abrirAlocacao(pessoa)"
                >

                  <q-item-section>
                    <q-item-label class="text-weight-medium">{{ pessoa.nome }}</q-item-label>
                    <q-item-label caption>
                      {{ pessoa.chapa }} · {{ pessoa.funcao }}
                      <template v-if="pessoa.base_cadastro">· {{ pessoa.base_cadastro }}</template>
                    </q-item-label>
                  </q-item-section>

                  <q-item-section side>
                    <q-chip
                      v-if="pessoa.afastado"
                      dense
                      class="bg-afastado text-afastado"
                      label="afastado"
                    />
                    <q-icon v-else name="chevron_right" />
                  </q-item-section>
                </q-item>

                <q-item v-if="!semSetorFiltrados.length">
                  <q-item-section class="text-center text-grey-7 q-py-md">
                    <q-icon name="task_alt" size="32px" color="positive" class="q-mb-xs" />
                    Ninguém sem setor com esses filtros.
                  </q-item-section>
                </q-item>
              </q-list>
            </q-card>
          </div>
        </div>
      </q-page>
    </q-page-container>

    <!-- ================================================== -->
    <!-- ORGANOGRAMA DO SETOR -->
    <!-- ================================================== -->

    <q-dialog v-model="organograma.aberto" full-width>
      <q-card class="cartao-organograma">
        <q-card-section class="row items-center no-wrap">
          <q-icon name="account_tree" color="primary" size="26px" class="q-mr-sm" />
          <div v-if="naVisaoGeral">
            <div class="text-h6">Organograma geral</div>
            <div class="text-caption">
              {{ gruposDaVisaoGeral.length }} setores · {{ alocados.length }} pessoas. Clique
              num setor ou numa base para abrir o organograma dele
            </div>
          </div>
          <div v-else>
            <div class="text-h6">{{ tituloOrganograma }}</div>
            <div v-if="grupoOrganograma" class="text-caption">
              {{ totalDoOrganograma }}
              {{ totalDoOrganograma === 1 ? 'pessoa' : 'pessoas' }}
              <template v-if="!organograma.bases.length && !organograma.topos.length">
                · {{ grupoOrganograma.bases.length }}
                {{ grupoOrganograma.bases.length === 1 ? 'base' : 'bases' }}
              </template>
            </div>
          </div>
          <q-space />
          <template v-if="naVisaoGeral && podeEditar">
            <q-btn
              flat
              no-caps
              color="primary"
              label="Adicionar gerente"
              class="q-mr-sm"
              @click="abrirAdicionarNoSetor(SETOR_GERENCIA)"
            />
            <q-btn
              v-if="gerentes.length"
              outline
              no-caps
              color="primary"
              label="Editar gerentes"
              class="q-mr-sm"
              @click="abrirDaVisaoGeral(SETOR_GERENCIA, [])"
            />
          </template>
          <q-btn
            v-if="!naVisaoGeral && podeEditar"
            outline
            no-caps
            color="primary"
            label="Vagas (BID)"
            class="q-mr-sm"
            @click="abrirVagasDoSetor(organograma.setor)"
          />
          <q-btn
            class="btn-exportar q-mr-sm"
            color="positive"
            text-color="white"
            no-caps
            label="Exportar imagem"
            :loading="exportandoOrganograma"
            @click="exportarOrganograma"
          >
            <q-tooltip>
              PNG 4K (3840 × 2160). Se não ficar legível numa imagem só, divide em partes
            </q-tooltip>
          </q-btn>
          <q-btn v-close-popup flat round dense icon="close" />
        </q-card-section>

        <q-separator />

        <div v-if="podeEditar && naVisaoGeral && gerentes.length" class="dica-arraste">
          <q-icon name="pan_tool" size="16px" />
          Arraste um setor ou um gerente sobre um gerente: no lado direito da caixa, vira apoio
          dele; no resto, fica abaixo dele, com todas as bases. O nome de um responsável leva só
          ele e quem está abaixo dele. Um gerente solto na parte de cima da caixa fica acima do
          outro.
          <q-spinner v-if="salvandoOrganograma" size="16px" color="primary" class="q-ml-sm" />
        </div>

        <div v-if="podeEditar && !naVisaoGeral" class="dica-arraste">
          <q-icon name="pan_tool" size="16px" />
          Arraste uma pessoa sobre outra: no meio ou embaixo da caixa, passa a
          responder a ela; em cima, fica acima dela; no lado direito, vira
          assessoria dela; na caixa da base, volta ao nível da base. Clique na pessoa
          para mudar o subsetor ou as bases dela. Vaga vazia (azul): arraste para alguém
          (fica abaixo dela) ou para uma base; solte uma pessoa nela para ocupar; clique
          para escolher quem ocupa.
          <q-spinner v-if="salvandoOrganograma" size="16px" color="primary" class="q-ml-sm" />
        </div>

        <q-banner
          v-if="avisoOrganograma.texto"
          dense
          :class="avisoOrganograma.tipo === 'erro' ? 'bg-red-1 text-negative' : 'bg-green-1 text-positive'"
          class="q-mx-md q-mt-sm"
          rounded
        >
          {{ avisoOrganograma.texto }}
          <template #action>
            <q-btn flat dense round icon="close" @click="avisoOrganograma = { tipo: '', texto: '' }" />
          </template>
        </q-banner>

        <q-card-section v-if="naVisaoGeral" class="area-organograma">
          <div ref="desenhoOrganograma" class="org-raizes">
            <div class="org-legenda">
              <span class="org-legenda__item">
                <span class="org-legenda__cor org-legenda__cor--geral" />
                Gerência
              </span>
              <span v-for="grupo in gruposDaVisaoGeral" :key="grupo.nome" class="org-legenda__item">
                <span
                  class="org-legenda__cor"
                  :style="{
                    '--sub-fundo': coresDosSetores[grupo.nome].fundo,
                    '--sub-borda': coresDosSetores[grupo.nome].borda,
                    '--sub-fundo-escuro': coresDosSetores[grupo.nome].fundoEscuro,
                    '--sub-borda-escura': coresDosSetores[grupo.nome].bordaEscura
                  }"
                />
                {{ grupo.nome }}
              </span>
            </div>
            <div class="org-topos">
              <div v-for="raiz in arvoreDaVisaoGeral" :key="raiz.id" class="org-topos__ramo">
                <OrganogramaNo :no="raiz" />
              </div>
            </div>
          </div>
        </q-card-section>

        <q-card-section v-else class="area-organograma">
          <div class="org-navegacao">
          <!-- nível mais alto: volta para a visão geral (fora da imagem exportada) -->
          <button type="button" class="org-voltar" @click="abrirVisaoGeral">
            <q-icon name="arrow_upward" size="16px" />
            <span>{{ tituloOrganograma }}</span>
            <q-tooltip>Voltar para o organograma geral</q-tooltip>
          </button>
          <div class="org-voltar__linha" />
          <div ref="desenhoOrganograma" class="org-raizes">
            <div v-if="subsetoresDoOrganograma.length" class="org-legenda">
              <span class="org-legenda__item">
                <span class="org-legenda__cor org-legenda__cor--geral" />
                Geral
              </span>
              <span v-for="nome in subsetoresDoOrganograma" :key="nome" class="org-legenda__item">
                <span
                  class="org-legenda__cor"
                  :style="{
                    '--sub-fundo': coresDosSubsetores[nome].fundo,
                    '--sub-borda': coresDosSubsetores[nome].borda,
                    '--sub-fundo-escuro': coresDosSubsetores[nome].fundoEscuro,
                    '--sub-borda-escura': coresDosSubsetores[nome].bordaEscura
                  }"
                />
                {{ nome }}
              </span>
            </div>
            <div class="org-topos">
              <div v-for="raiz in arvoreOrganograma" :key="raiz.id" class="org-topos__ramo">
                <OrganogramaNo :no="raiz" />
              </div>
            </div>
          </div>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- A QUEM DO GRUPO RESPONDE (soltar sobre um cartão agrupado) -->
    <q-dialog v-model="escolhaDoChefe.aberto">
      <q-card style="width: 420px; max-width: 94vw">
        <q-card-section class="row items-center">
          <q-icon name="account_tree" color="primary" size="26px" class="q-mr-sm" />
          <div class="text-h6">Onde fica?</div>
          <q-space />
          <q-btn v-close-popup flat round dense icon="close" />
        </q-card-section>
        <q-separator />
        <q-card-section v-if="escolhaDoChefe.origem">
          <div class="text-body2 q-mb-sm">
            Onde fica <strong>{{ escolhaDoChefe.origem.nome }}</strong>? Abaixo do bloco
            {{ escolhaDoChefe.cargo }} todo, ou de uma pessoa dele?
          </div>
          <q-option-group v-model="escolhaDoChefe.chapa" :options="opcoesEscolhaDoChefe" dense />
          <div class="text-caption q-mt-sm">
            Dica: soltar direto sobre um nome dentro do cartão já escolhe a pessoa.
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Cancelar" />
          <q-btn
            color="primary"
            label="Confirmar"
            :disable="!escolhaDoChefe.chapa"
            :loading="salvandoOrganograma"
            @click="confirmarEscolhaDoChefe"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- EDITAR NO ORGANOGRAMA (clicar na pessoa): subsetor e bases -->
    <q-dialog v-model="basesDaPessoa.aberto">
      <q-card style="width: 440px; max-width: 94vw">
        <q-card-section class="row items-center">
          <q-icon name="account_tree" color="primary" size="26px" class="q-mr-sm" />
          <div>
            <div class="text-h6">Editar no organograma</div>
            <div class="text-caption">{{ basesDaPessoa.nome }} · {{ organograma.setor || SETOR_GERENCIA }}</div>
          </div>
          <q-space />
          <q-btn v-close-popup flat round dense icon="close" />
        </q-card-section>
        <q-separator />
        <q-card-section class="q-gutter-md">
          <q-select
            v-model="basesDaPessoa.subsetor"
            outlined
            dense
            use-input
            hide-selected
            fill-input
            clearable
            input-debounce="0"
            new-value-mode="add-unique"
            label="Subsetor"
            :hint="dicaSubsetorDaPessoa"
            :options="opcoesSubsetorOrganograma"
            @filter="filtrarSubsetoresOrganograma"
            @input-value="valor => digitarSubsetor(basesDaPessoa, valor)"
            @clear="digitarSubsetor(basesDaPessoa, '')"
          >
          </q-select>

          <q-select
            v-model="basesDaPessoa.bases"
            outlined
            dense
            multiple
            use-chips
            clearable
            options-dense
            label="Responsável pelas bases"
            :hint="
              marcandoBasesDeGerente
                ? 'Os setores destas bases aparecem abaixo dele no organograma geral.'
                : 'Uma base: a caixa dele vira a da base. Várias: ele em cima e as bases abaixo.'
            "
            :options="basesDoSetorOrganograma"
          >
          </q-select>

          <div v-if="!marcandoBasesDeGerente" class="text-caption">
            Ao marcar uma base, quem dela respondia ao chefe dele passa a responder
            a ele; ao desmarcar, volta para o chefe.
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Cancelar" />
          <q-btn color="primary" label="Salvar" :loading="salvandoOrganograma" @click="salvarBasesDaPessoa" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ================================================== -->
    <!-- ALOCAR / MOVER (pessoa + setor + base + responsável) -->
    <!-- ================================================== -->

    <q-dialog v-model="alocacao.aberto">
      <q-card style="width: 520px; max-width: 94vw">
        <q-card-section class="row items-center">
          <q-icon
            :name="alocacao.modo === 'setor' ? 'person_add' : 'apartment'"
            color="primary"
            size="26px"
            class="q-mr-sm"
          />
          <div class="text-h6">{{ tituloAlocacao }}</div>
          <q-space />
          <q-btn v-close-popup flat round dense icon="close" />
        </q-card-section>

        <q-separator />

        <q-card-section class="q-gutter-md">
          <div v-if="alocacao.modo === 'pessoa' && pessoaAlocacao" class="pessoa-fixa">
            <div class="q-ml-sm">
              <div class="text-weight-medium">{{ pessoaAlocacao.nome }}</div>
              <div class="text-caption">
                {{ pessoaAlocacao.chapa }} · {{ pessoaAlocacao.funcao }}
                <template v-if="pessoaAlocacao.base_cadastro">
                  · cadastro em {{ pessoaAlocacao.base_cadastro }}
                </template>
              </div>
            </div>
          </div>

          <q-select
            v-else
            v-model="alocacao.chapa"
            outlined
            dense
            emit-value
            map-options
            use-input
            input-debounce="0"
            label="Indireto *"
            :options="opcoesPessoas"
            @filter="filtrarPessoas"
          >
            <template #option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.nome }}</q-item-label>
                  <q-item-label caption>
                    {{ scope.opt.value }} · {{ scope.opt.funcao }}
                  </q-item-label>
                </q-item-section>
              </q-item>
            </template>
            <template #no-option>
              <q-item>
                <q-item-section class="text-grey-7">Ninguém sem setor encontrado</q-item-section>
              </q-item>
            </template>
          </q-select>

          <div class="row q-col-gutter-sm">
            <div class="col-12 col-sm-7">
              <!-- escolhe um setor existente ou digita um novo -->
              <q-select
                v-model="alocacao.setor"
                outlined
                dense
                use-input
                hide-selected
                fill-input
                input-debounce="0"
                new-value-mode="add-unique"
                label="Setor *"
                :options="opcoesSetorDialogo"
                :readonly="alocacao.modo === 'setor'"
                @filter="filtrarSetores"
                @input-value="valor => (alocacao.setorDigitado = valor)"
              >
              </q-select>
            </div>

            <div class="col-12 col-sm-5">
              <q-select
                v-if="alocandoGerente"
                v-model="alocacao.basesGerente"
                outlined
                dense
                multiple
                use-chips
                clearable
                options-dense
                label="Bases"
                hint="Vazio: fica acima de todos"
                :options="bases"
              >
              </q-select>
              <q-select
                v-else
                v-model="alocacao.base"
                outlined
                dense
                label="Base *"
                :options="bases"
              >
              </q-select>
            </div>
          </div>

          <!-- vaga do BID: só quando o setor já tem vagas -->
          <q-select
            v-if="setorEscolhidoTemBid"
            v-model="alocacao.vagaId"
            outlined
            dense
            emit-value
            map-options
            label="Vaga do BID"
            :options="opcoesVagaDialogo"
          >
            <template #option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.label }}</q-item-label>
                  <q-item-label caption>{{ scope.opt.caption }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <!-- subsetor: opcional; não aparece nos cartões, só no filtro e no organograma -->
          <q-select
            v-model="alocacao.subsetor"
            outlined
            dense
            use-input
            hide-selected
            fill-input
            clearable
            input-debounce="0"
            new-value-mode="add-unique"
            label="Subsetor (opcional)"
            :hint="dicaSubsetor"
            :options="opcoesSubsetorDialogo"
            @filter="filtrarSubsetores"
            @input-value="valor => digitarSubsetor(alocacao, valor)"
            @clear="digitarSubsetor(alocacao, '')"
          >
          </q-select>

          <q-select
            v-model="alocacao.responsavelChapa"
            outlined
            dense
            emit-value
            map-options
            use-input
            input-debounce="0"
            :label="alocandoGerente ? 'Responsável' : 'Responsável *'"
            :clearable="alocandoGerente"
            :hint="alocandoGerente ? 'Vazio: fica acima de todos' : undefined"
            :options="opcoesResponsavelSelect"
            @filter="filtrarResponsaveis"
          >
            <template #option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.nome }}</q-item-label>
                  <q-item-label caption>
                    {{ scope.opt.chapa }} · {{ scope.opt.funcao }}
                  </q-item-label>
                </q-item-section>
              </q-item>
            </template>
            <template #no-option>
              <q-item>
                <q-item-section class="text-grey-7">
                  Digite parte do nome ou a chapa
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <!-- função mostrada na página: só as que já existem no cadastro -->
          <q-select
            v-model="alocacao.funcao"
            outlined
            dense
            use-input
            hide-selected
            fill-input
            clearable
            input-debounce="0"
            label="Função"
            placeholder="Comece a digitar..."
            :options="opcoesFuncao"
            :hint="
              pessoaAlocacao
                ? `Só nesta página; no cadastro é ${pessoaAlocacao.funcao || 'sem função'}.`
                : 'Vazio: a do cadastro.'
            "
            @filter="filtrarFuncoes"
          >
            <template #no-option>
              <q-item>
                <q-item-section class="text-grey-7">Nenhuma função encontrada</q-item-section>
              </q-item>
            </template>
          </q-select>

          <q-input
            v-model="alocacao.observacao"
            outlined
            dense
            autogrow
            label="Observação (opcional)"
          >
          </q-input>

          <q-banner v-if="setorNovo" dense rounded class="bg-blue-1">
            <template #avatar><q-icon name="add_circle" color="primary" /></template>
            {{ setorEscolhido }} é um setor novo: ele aparece na tela assim que
            esta pessoa for alocada.
          </q-banner>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            v-if="alocacao.modo === 'pessoa' && pessoaAlocacao?.alocacao"
            flat
            no-caps
            color="negative"
            label="Tirar do setor"
            @click="removerDoSetor(pessoaAlocacao)"
          />
          <q-space />
          <q-btn v-close-popup flat label="Cancelar" />
          <q-btn
            color="primary"
            label="Salvar"
            :disable="!alocacaoCompleta"
            :loading="salvando"
            @click="confirmarAlocacao"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ================================================== -->
    <!-- VAGAS DO SETOR (BID): quantas por função e quem ocupa -->
    <!-- ================================================== -->

    <q-dialog v-model="vagasSetor.aberto">
      <q-card style="width: 920px; max-width: 96vw">
        <q-card-section class="row items-center no-wrap">
          <q-icon name="event_seat" color="primary" size="26px" class="q-mr-sm" />
          <div>
            <div class="text-h6">Vagas · {{ vagasSetor.setor }}</div>
            <div class="text-caption">
              {{ textoResumoVagas(vagasSetor.setor) || 'Sem vagas no BID ainda' }}
            </div>
          </div>
          <q-space />
          <q-spinner v-if="vagasSetor.salvando" size="18px" color="primary" class="q-mr-sm" />
          <q-btn v-close-popup flat round dense icon="close" />
        </q-card-section>

        <q-separator />

        <q-banner
          v-if="vagasSetor.aviso.texto"
          dense
          rounded
          class="q-mx-md q-mt-sm"
          :class="vagasSetor.aviso.tipo === 'erro' ? 'bg-red-1 text-negative' : 'bg-green-1 text-positive'"
        >
          {{ vagasSetor.aviso.texto }}
        </q-banner>

        <q-card-section class="vagas-dialogo">
          <div class="text-caption q-mb-sm">
            Defina as funções e quantas vagas cada uma tem, todas de uma vez, na ordem do BID
            (arraste pela alça para mudar a ordem), e salve. Para pôr as pessoas nas vagas,
            use "Ocupar" na vaga vazia ou "Pôr na vaga" no extra, no cartão do setor.
          </div>

          <!-- 1) BID: várias funções de uma vez; o nome do cargo sugere as
               funções do cadastro, mas é editável -->
          <div class="vagas-secao__titulo">Vagas previstas (BID)</div>
          <div class="vagas-tabela">
            <div class="vagas-tabela__cabecalho">
              <span class="vagas-tabela__alca" />
              <span class="col">Cargo (BID)</span>
              <span class="vagas-tabela__qtd">Vagas</span>
              <span class="vagas-tabela__ocupadas">Ocupadas</span>
              <span class="vagas-tabela__acao" />
            </div>
            <div
              v-for="linha in vagasSetor.linhas"
              :key="linha.chave"
              class="vagas-tabela__linha"
              :class="{
                'vagas-tabela__linha--apagar': linha.atual && Number(linha.quantidade) === 0,
                'vagas-tabela__linha--arrastando': linhaArrastada === linha,
                'vagas-tabela__linha--alvo': linhaAlvo === linha
              }"
              @dragover="evento => sobreLinha(evento, linha)"
              @dragleave="linhaAlvo === linha && (linhaAlvo = null)"
              @drop.prevent="soltarNaLinha(linha)"
            >
              <!-- arraste pela alça para mudar a ordem do BID -->
              <span
                class="vagas-tabela__alca"
                draggable="true"
                title="Arraste para cima ou para baixo para mudar a ordem do BID"
                @dragstart="evento => iniciarArrasteDaLinha(evento, linha)"
                @dragend="encerrarArrasteDaLinha"
              >
                <q-icon name="drag_indicator" size="20px" />
              </span>
              <q-select
                v-model="linha.funcao"
                outlined
                dense
                use-input
                hide-selected
                fill-input
                input-debounce="0"
                new-value-mode="add-unique"
                class="col"
                placeholder="Escolha ou digite o cargo"
                :options="opcoesFuncaoVaga"
                :disable="vagasSetor.salvando"
                @filter="filtrarFuncoesVaga"
                @input-value="valor => (linha.funcao = valor || null)"
              >
                <template #no-option>
                  <q-item>
                    <q-item-section class="text-grey-7">Cargo novo: fica como digitado</q-item-section>
                  </q-item>
                </template>
              </q-select>
              <q-input
                v-model.number="linha.quantidade"
                outlined
                dense
                type="number"
                min="0"
                class="vagas-tabela__qtd"
                :disable="vagasSetor.salvando"
              />
              <span class="vagas-tabela__ocupadas">{{ linha.ocupadas || '—' }}</span>
              <q-btn
                flat
                round
                dense
                size="sm"
                icon="delete"
                class="vagas-tabela__acao"
                :aria-label="linha.atual ? 'Apagar as vagas desta função' : 'Tirar a linha'"
                :disable="vagasSetor.salvando"
                @click="removerLinhaDasVagas(linha)"
              >
                <q-tooltip>{{ linha.atual ? 'Zerar (apaga só vagas vazias)' : 'Tirar a linha' }}</q-tooltip>
              </q-btn>
            </div>
          </div>

          <div class="row items-center q-mt-sm">
            <q-btn
              flat
              no-caps
              color="primary"
              label="Adicionar função"
              :disable="vagasSetor.salvando"
              @click="adicionarLinhaDasVagas"
            />
            <q-space />
            <span v-if="problemaDasVagas" class="text-caption text-negative q-mr-sm">
              {{ problemaDasVagas }}
            </span>
            <span v-else class="text-caption q-mr-sm">Total: {{ totalDaTabela }}</span>
            <q-btn
              color="primary"
              no-caps
              label="Salvar vagas"
              :disable="!vagasMudaram || Boolean(problemaDasVagas)"
              :loading="vagasSetor.salvando"
              @click="salvarDefinicaoDasVagas"
            />
          </div>

        </q-card-section>

        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Fechar" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ================================================== -->
    <!-- OCUPAR VAGA: na vaga vazia escolhe a pessoa; no extra, a vaga -->
    <!-- ================================================== -->

    <q-dialog v-model="ocupar.aberto">
      <q-card style="width: 500px; max-width: 94vw">
        <q-card-section class="row items-center no-wrap">
          <q-icon name="event_seat" color="primary" size="26px" class="q-mr-sm" />
          <div>
            <div class="text-h6">
              {{ ocupar.modo === 'vaga' ? 'Ocupar vaga' : 'Pôr na vaga' }}
            </div>
            <div class="text-caption">
              {{ ocupar.setor }}
              <template v-if="ocupar.modo === 'vaga' && ocupar.vaga"> · {{ ocupar.vaga.funcao }}</template>
              <template v-else-if="ocupar.pessoa"> · {{ ocupar.pessoa.nome }}</template>
            </div>
          </div>
          <q-space />
          <q-btn v-close-popup flat round dense icon="close" />
        </q-card-section>

        <q-separator />

        <q-card-section class="q-gutter-md">
          <q-banner v-if="ocupar.erro" dense rounded class="bg-red-1 text-negative">
            {{ ocupar.erro }}
          </q-banner>

          <!-- vaga vazia: quem vai ocupar -->
          <q-select
            v-if="ocupar.modo === 'vaga'"
            v-model="ocupar.chapa"
            outlined
            dense
            emit-value
            map-options
            use-input
            input-debounce="0"
            label="Quem ocupa *"
            :options="opcoesOcupar"
            @filter="filtrarOcupantes"
          >
            <template #option="scope">
              <q-item-label
                v-if="scope.index === 0 || opcoesOcupar[scope.index - 1].grupo !== scope.opt.grupo"
                header
                class="q-py-xs"
              >
                {{
                  { extra: 'Extras do setor', livre: 'Sem setor', outro: 'De outro setor (muda de setor)' }[
                    scope.opt.grupo
                  ]
                }}
              </q-item-label>
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.label }}</q-item-label>
                  <q-item-label caption>{{ scope.opt.caption }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>
            <template #no-option>
              <q-item>
                <q-item-section class="text-grey-7">Ninguém encontrado. Digite parte do nome.</q-item-section>
              </q-item>
            </template>
          </q-select>

          <!-- extra: em qual vaga vazia -->
          <q-option-group
            v-else
            v-model="ocupar.vagaId"
            :options="opcoesVagaParaOcupar"
            type="radio"
            dense
          />

          <!-- quem vem de fora do setor é alocado nele junto -->
          <template v-if="ocuparAlocaNoSetor && !ocuparNaGerencia">
            <div class="text-caption">
              {{ pessoaParaOcupar.nome }} vai para {{ ocupar.setor }}: confira a base e o responsável.
            </div>
            <div class="row q-col-gutter-sm">
              <div class="col-12 col-sm-4">
                <q-select v-model="ocupar.base" outlined dense label="Base *" :options="bases">
                </q-select>
              </div>
              <div class="col-12 col-sm-8">
                <q-select
                  v-model="ocupar.responsavelChapa"
                  outlined
                  dense
                  emit-value
                  map-options
                  use-input
                  input-debounce="0"
                  label="Responsável *"
                  :options="opcoesResponsavelSelect"
                  @filter="filtrarResponsaveis"
                >
                  <template #option="scope">
                    <q-item v-bind="scope.itemProps">
                      <q-item-section>
                        <q-item-label>{{ scope.opt.nome }}</q-item-label>
                        <q-item-label caption>{{ scope.opt.chapa }} · {{ scope.opt.funcao }}</q-item-label>
                      </q-item-section>
                    </q-item>
                  </template>
                </q-select>
              </div>
            </div>
          </template>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Cancelar" />
          <q-btn
            color="primary"
            label="Confirmar"
            :disable="!ocuparCompleto"
            :loading="ocupar.salvando"
            @click="confirmarOcupar"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ================================================== -->
    <!-- TROCAR RESPONSÁVEL (de uma pessoa ou de um grupo) -->
    <!-- ================================================== -->

    <q-dialog v-model="trocaResponsavel.aberto">
      <q-card style="width: 460px; max-width: 94vw">
        <q-card-section class="row items-center">
          <q-icon name="supervisor_account" color="primary" size="26px" class="q-mr-sm" />
          <div class="text-h6">Trocar responsável</div>
          <q-space />
          <q-btn v-close-popup flat round dense icon="close" />
        </q-card-section>

        <q-separator />

        <q-card-section class="q-gutter-md">
          <div class="text-body2">
            Vale para
            <strong>
              {{
                trocaResponsavel.pessoas.length === 1
                  ? trocaResponsavel.pessoas[0].nome
                  : `${trocaResponsavel.pessoas.length} pessoas`
              }}
            </strong>
            <template v-if="trocaResponsavel.responsavelAtual">
              (hoje com {{ trocaResponsavel.responsavelAtual.nome }})</template>.
          </div>

          <q-select
            v-model="trocaResponsavel.chapa"
            outlined
            dense
            emit-value
            map-options
            use-input
            input-debounce="0"
            label="Novo responsável *"
            :options="opcoesResponsavelSelect"
            @filter="filtrarResponsaveis"
          >
            <template #option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.nome }}</q-item-label>
                  <q-item-label caption>
                    {{ scope.opt.chapa }} · {{ scope.opt.funcao }}
                  </q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-select>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Cancelar" />
          <q-btn
            color="primary"
            label="Salvar"
            :disable="!trocaResponsavel.chapa"
            :loading="salvando"
            @click="salvarResponsavel"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ================================================== -->
    <!-- PLANILHA (baixar a atual / enviar a preenchida) -->
    <!-- ================================================== -->

    <q-dialog v-model="planilha.aberto">
      <q-card style="width: 640px; max-width: 94vw">
        <q-card-section class="row items-center">
          <q-icon name="table_view" color="primary" size="26px" class="q-mr-sm" />
          <div class="text-h6">Planilha de indiretos</div>
          <q-space />
          <q-btn v-close-popup flat round dense icon="close" />
        </q-card-section>

        <q-separator />

        <q-card-section class="q-gutter-md">
          <div class="text-body2">
            Uma planilha só, no formato do BID: à esquerda o previsto (setor e função do
            BID), à direita o real (quem ocupa, base e responsável). Uma linha por vaga, na
            ordem do BID, e no fim de cada setor os extras com a função do BID em branco.
            Cada setor da planilha fica com as vagas dela; quem não estiver na planilha
            continua onde está.
          </div>

          <q-markup-table flat bordered dense class="tabela-modelo">
            <thead>
              <tr class="tabela-ocupacao__grupos">
                <th colspan="2" class="tabela-ocupacao__grupo-bid">BID</th>
                <th colspan="3" class="tabela-ocupacao__grupo-real">REAL</th>
              </tr>
              <tr>
                <th>SETOR</th>
                <th>FUNÇÃO (BID)</th>
                <th>CHAPA INDIRETO</th>
                <th>BASE</th>
                <th>CHAPA RESPONSÁVEL</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>GOMAN</td>
                <td>SUPERVISOR OPERACIONAL</td>
                <td>12345</td>
                <td>BCB</td>
                <td>19837</td>
              </tr>
              <tr class="linha-vaga-vazia">
                <td>GOMAN</td>
                <td>SUPERVISOR OPERACIONAL</td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
              <tr class="linha-extra">
                <td>GOMAN</td>
                <td></td>
                <td>23456</td>
                <td>BCB</td>
                <td>19837</td>
              </tr>
            </tbody>
          </q-markup-table>

          <div class="row q-col-gutter-sm items-center">
            <div class="col-12 col-sm-auto">
              <q-btn
                outline
                no-caps
                color="primary"
                label="Baixar planilha atual"
                :loading="baixando"
                @click="baixarPlanilha"
              />
            </div>
            <div class="col">
              <q-file
                v-model="planilha.arquivo"
                outlined
                dense
                clearable
                accept=".xlsx"
                label="Escolher planilha (.xlsx)"
                @update:model-value="planilha.previa = null"
              >
              </q-file>
            </div>
          </div>

          <!-- PRÉVIA -->
          <template v-if="planilha.previa">
            <div class="row q-gutter-sm">
              <q-chip class="bg-green-1 text-positive" icon="person_add">
                {{ planilha.previa.alocar.length }} a alocar
              </q-chip>
              <q-chip class="bg-blue-1" icon="swap_horiz">
                {{ planilha.previa.mover.length }} a mover
              </q-chip>
              <q-chip class="bg-orange-1" icon="edit">
                {{ planilha.previa.atualizar.length }} a atualizar
              </q-chip>
              <q-chip icon="check">{{ planilha.previa.sem_mudanca }} sem mudança</q-chip>
              <q-chip v-if="planilha.previa.vagas?.length" class="chip-vaga-vazia" icon="event_seat">
                BID: {{ planilha.previa.vagas.length }}
                {{ planilha.previa.vagas.length === 1 ? 'setor muda' : 'setores mudam' }}
              </q-chip>
              <q-chip
                v-if="planilha.previa.erros.length"
                class="bg-red-1 text-negative"
                icon="error"
              >
                {{ planilha.previa.erros.length }} com erro
              </q-chip>
            </div>

            <q-list
              v-if="planilha.previa.erros.length"
              bordered
              dense
              separator
              class="rounded-borders lista-previa"
            >
              <q-item-label header class="text-negative">
                Corrija estas linhas e envie de novo — nada é gravado enquanto houver erro
              </q-item-label>
              <q-item v-for="item in planilha.previa.erros" :key="`e${item.linha}`">
                <q-item-section>
                  <q-item-label>Linha {{ item.linha }} · {{ item.chapa }}</q-item-label>
                  <q-item-label caption class="text-negative">{{ item.erro }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>

            <q-list
              v-else-if="mudancasPrevia.length"
              bordered
              dense
              separator
              class="rounded-borders lista-previa"
            >
              <q-item v-for="item in mudancasPrevia" :key="`${item.tipo}${item.chapa}`">
                <q-item-section avatar>
                  <q-icon :name="item.icone" :color="item.cor" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ item.nome }} ({{ item.chapa }})</q-item-label>
                  <q-item-label caption>{{ item.texto }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>

            <div v-else-if="!planilha.previa.vagas?.length" class="text-caption">
              Nada muda com esta planilha.
            </div>

            <q-list
              v-if="!planilha.previa.erros.length && planilha.previa.vagas?.length"
              bordered
              dense
              separator
              class="rounded-borders lista-previa"
            >
              <q-item-label header>Vagas do BID</q-item-label>
              <q-item v-for="item in planilha.previa.vagas" :key="`v${item.setor}`">
                <q-item-section avatar>
                  <q-icon name="event_seat" color="primary" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ item.setor }}</q-item-label>
                  <q-item-label caption>{{ textoPreviaVagas(item) }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </template>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Fechar" />
          <q-btn
            v-if="!podeAplicar"
            color="primary"
            label="Analisar"
            :disable="!planilha.arquivo"
            :loading="planilha.analisando"
            @click="analisarPlanilha"
          />
          <q-btn
            v-else
            color="positive"
            label="Aplicar"
            :loading="planilha.aplicando"
            @click="aplicarPlanilha"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-layout>
</template>

<script setup>
import { computed, nextTick, onMounted, provide, reactive, ref, watch } from 'vue'
import { toCanvas } from 'html-to-image'

import CabecalhoApp from '../components/CabecalhoApp.vue'
import MarcaDaguaFundo from '../components/MarcaDaguaFundo.vue'
import OrganogramaNo from '../components/OrganogramaNo.vue'
import SelectFiltroMultiplo from '../components/SelectFiltroMultiplo.vue'
import { PODE_VER_EQUIPES, useSessao } from '../composables/useSessao'
import { useConfirmacao } from '../composables/useConfirmacao'
import { proximaSelecaoMultipla } from '../utils/equipes'

// mesmas regras do Banco de Dados; enquanto a página está em liberação
// gradual, só o Administrador abre (ver router/index.js e indiretos.py)
definePage({ meta: { permissao: PODE_VER_EQUIPES } })

// Todos que veem equipes consultam a página; editar (alocar, mover, trocar
// responsável, planilha) é só do Administrador — o servidor também barra.
const { usuario } = useSessao()
const podeEditar = computed(() => Boolean(usuario.value?.ignora_vinculos))

const { confirmar } = useConfirmacao()

// ============================================================
// DADOS (GET /api/indiretos)
// ============================================================

// pessoas: os indiretos do cadastro, cada um com `alocacao` (setor, base,
// responsável...) ou null. responsaveis: o cadastro inteiro (qualquer
// colaborador pode ser responsável).
const pessoas = ref([])
const responsaveis = ref([])
const bases = ref([])
const setoresGerencia = ref([])
const funcoes = ref([])
// vagas do BID: { id, setor, funcao }; quem ocupa vem em alocacao.vaga_id
const vagas = ref([])
const carregando = ref(false)
const primeiraCarga = ref(true)
const erro = ref('')
const sucesso = ref('')

let sequenciaCarga = 0

async function carregar() {
  const minhaSequencia = ++sequenciaCarga
  carregando.value = true
  erro.value = ''
  try {
    const resposta = await fetch('/api/indiretos')
    const dados = await resposta.json()
    if (!resposta.ok || dados.erro) {
      throw new Error(dados.erro || 'Erro ao carregar os indiretos.')
    }
    if (minhaSequencia !== sequenciaCarga) return
    pessoas.value = dados.pessoas || []
    responsaveis.value = dados.responsaveis || []
    bases.value = dados.bases || []
    setoresGerencia.value = dados.setores_gerencia || []
    funcoes.value = dados.funcoes || []
    vagas.value = dados.vagas || []
  } catch (e) {
    if (minhaSequencia === sequenciaCarga) {
      erro.value = e.message || 'Erro ao carregar os indiretos.'
    }
  } finally {
    if (minhaSequencia === sequenciaCarga) {
      carregando.value = false
      primeiraCarga.value = false
    }
  }
}

onMounted(carregar)

const responsaveisPorChapa = computed(
  () => new Map(responsaveis.value.map(r => [r.chapa, r]))
)

function responsavelPorChapa(chapa) {
  return responsaveisPorChapa.value.get(chapa) || null
}

// Primeiro e segundo nome ("CAMILA CORREA ARAUJO" -> "CAMILA CORREA")
// v-caber-na-linha: diminui a fonte do texto (até 70% do tamanho normal) para
// ele caber numa linha só; acompanha a largura do cartão. Se nem assim
// couber, corta com reticências.
const REDUCAO_MAXIMA = 0.7

function caberNaLinha(el) {
  el.style.fontSize = ''
  const normal = parseFloat(getComputedStyle(el).fontSize)
  let tamanho = normal
  while (el.scrollWidth > el.clientWidth && tamanho > normal * REDUCAO_MAXIMA) {
    tamanho -= 0.5
    el.style.fontSize = `${tamanho}px`
  }
}

const vCaberNaLinha = {
  mounted(el) {
    el.style.whiteSpace = 'nowrap'
    el.style.overflow = 'hidden'
    el.style.textOverflow = 'ellipsis'
    caberNaLinha(el)
    el._observador = new ResizeObserver(() => caberNaLinha(el))
    el._observador.observe(el)
  },
  updated(el) {
    caberNaLinha(el)
  },
  unmounted(el) {
    el._observador?.disconnect()
  }
}

// Dois primeiros nomes; se o segundo for partícula (DA, DE, DOS...), entra
// também o seguinte: "JUNIEL DA SILVA", e não "JUNIEL DA".
const PARTICULAS = new Set(['DA', 'DE', 'DO', 'DAS', 'DOS', 'E', "D'"])

function nomeCurto(nome) {
  const partes = String(nome || '').trim().split(/\s+/)
  const curto = partes.slice(0, 2)
  let i = 2
  while (PARTICULAS.has(curto[curto.length - 1]?.toUpperCase()) && i < partes.length) {
    curto.push(partes[i++])
  }
  return curto.join(' ')
}

async function chamarApi(url, opcoes, mensagemErro) {
  const resposta = await fetch(url, opcoes)
  const dados = await resposta.json().catch(() => ({}))
  if (!resposta.ok || dados.erro) {
    throw new Error(dados.erro || mensagemErro)
  }
  return dados
}

// ============================================================
// FILTROS
// ============================================================

// Igual às outras telas: cada filtro começa em "Todos"; escolher um item
// tira o "Todos", e "Limpar filtros" volta tudo ao início.
const TODOS = 'TODOS'
const filtroBases = ref([TODOS])
const filtroSetores = ref([TODOS])
const filtroSubsetores = ref([TODOS])
// quem não tem subsetor é do setor geral: opção "Geral" do filtro
const SEM_SUBSETOR = '__SEM_SUBSETOR__'
// mesmo nome de indiretos.py: SETOR_GERENCIA
const SETOR_GERENCIA = 'GERÊNCIA'
const filtroResponsaveis = ref([TODOS])
const busca = ref('')
const buscaSemSetor = ref('')

// o que está de fato escolhido (vazio = todos)
const escolhidos = selecao => (selecao.includes(TODOS) ? [] : selecao)
const basesAtivas = computed(() => escolhidos(filtroBases.value))
const setoresAtivos = computed(() => escolhidos(filtroSetores.value))
const subsetoresAtivos = computed(() => escolhidos(filtroSubsetores.value))
const responsaveisAtivos = computed(() => escolhidos(filtroResponsaveis.value))

function limparFiltros() {
  filtroBases.value = [TODOS]
  filtroSetores.value = [TODOS]
  filtroSubsetores.value = [TODOS]
  filtroResponsaveis.value = [TODOS]
  busca.value = ''
  buscaSemSetor.value = ''
  filtroStatus.value = ''
}
// clicar num indicador filtra por status; clicar de novo limpa
const filtroStatus = ref('')

const alocados = computed(() => pessoas.value.filter(p => p.alocacao))

// Quem é responsável por alguém já tem lugar (lidera um setor), mesmo sem
// alocação própria: conta como alocado e não aparece em "Sem setor".
const chapasResponsaveis = computed(
  () => new Set(alocados.value.map(p => p.alocacao.responsavel_chapa).filter(Boolean))
)

function estaAlocado(pessoa) {
  return Boolean(pessoa.alocacao) || chapasResponsaveis.value.has(pessoa.chapa)
}

function opcoesUnicas(valores) {
  return [...new Set(valores.filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'pt-BR'))
    .map(valor => ({ label: valor, value: valor }))
}

const nomesSetores = computed(() =>
  [...new Set(alocados.value.map(p => p.alocacao.setor))].sort((a, b) =>
    a.localeCompare(b, 'pt-BR')
  )
)
const opcoesBases = computed(() => [
  { label: 'Todas as bases', value: TODOS },
  ...opcoesUnicas(alocados.value.map(p => p.alocacao.base))
])
const opcoesSubsetores = computed(() => {
  const alocadosDosSetores = setoresAtivos.value.length
    ? alocados.value.filter(p => setoresAtivos.value.includes(p.alocacao.setor))
    : alocados.value
  return [
    { label: 'Todos os subsetores', value: TODOS },
    // sem subsetor atribuído = o setor geral
    { label: 'Geral', value: SEM_SUBSETOR },
    ...opcoesUnicas(alocadosDosSetores.map(subsetorEfetivo))
  ]
})

const opcoesSetores = computed(() => [
  { label: 'Todos os setores', value: TODOS },
  ...opcoesUnicas(nomesSetores.value)
])
// só os dois primeiros nomes, como no chip; se dois ficarem iguais, a chapa
// desempata
// Responsável é uma CADEIA (coordenador > supervisor > analista...): o filtro
// lista só o topo de cada cadeia — o mesmo responsável dos cartões — e
// escolher alguém traz a cadeia inteira dele.
const opcoesResponsaveis = computed(() => {
  const opcoes = [...new Set(alocados.value.map(topoDaCadeia).filter(Boolean))]
    .map(chapa => ({ label: nomeCurto(responsavelPorChapa(chapa)?.nome) || chapa, value: chapa }))
  const repetidos = new Set(
    opcoes.map(o => o.label).filter((label, i, todos) => todos.indexOf(label) !== i)
  )
  return [
    { label: 'Todos os responsáveis', value: TODOS },
    ...opcoes
      .map(o => (repetidos.has(o.label) ? { ...o, label: `${o.label} (${o.value})` } : o))
      .sort((a, b) => a.label.localeCompare(b.label, 'pt-BR'))
  ]
})

function casaComBusca(pessoa, texto = busca.value) {
  const termo = (texto || '').trim().toLowerCase()
  if (!termo) return true
  return [pessoa.nome, pessoa.chapa, pessoa.funcao, funcaoExibida(pessoa)].some(valor =>
    String(valor || '').toLowerCase().includes(termo)
  )
}

function casaComStatus(pessoa) {
  if (filtroStatus.value === 'afastados') return Boolean(pessoa.afastado)
  if (filtroStatus.value === 'alocados') return estaAlocado(pessoa)
  if (filtroStatus.value === 'semSetor') return !estaAlocado(pessoa)
  if (filtroStatus.value === 'extras') return ehExtra(pessoa)
  // os setores que têm vaga vazia (com todo mundo deles)
  if (filtroStatus.value === 'vagasVazias') {
    return Boolean(pessoa.alocacao && resumoVagasPorSetor.value.get(pessoa.alocacao.setor)?.vazias)
  }
  return true
}

// ============================================================
// VAGAS (BID)
// ============================================================
//
// Cada vaga é uma linha do BID: setor + função. Quem a ocupa é a pessoa com
// alocacao.vaga_id dela, mesmo com outra função real. Alocado sem vaga num
// setor que já tem BID = EXTRA; setor ainda sem BID não marca ninguém.

const vagaPorId = computed(() => new Map(vagas.value.map(v => [v.id, v])))
const ocupantePorVaga = computed(
  () => new Map(alocados.value.filter(p => p.alocacao.vaga_id).map(p => [p.alocacao.vaga_id, p]))
)
const setoresComBid = computed(() => new Set(vagas.value.map(v => v.setor)))

function vagaDe(pessoa) {
  return vagaPorId.value.get(pessoa.alocacao?.vaga_id) || null
}

function ehExtra(pessoa) {
  return Boolean(
    pessoa.alocacao && !vagaDe(pessoa) && setoresComBid.value.has(pessoa.alocacao.setor)
  )
}

// setor -> { total, ocupadas, vazias, extras }
const resumoVagasPorSetor = computed(() => {
  const resumo = new Map()
  const doSetor = setor => {
    if (!resumo.has(setor)) resumo.set(setor, { total: 0, ocupadas: 0, vazias: 0, extras: 0 })
    return resumo.get(setor)
  }
  for (const vaga of vagas.value) {
    const r = doSetor(vaga.setor)
    r.total++
    if (ocupantePorVaga.value.has(vaga.id)) r.ocupadas++
    else r.vazias++
  }
  for (const pessoa of alocados.value) {
    if (ehExtra(pessoa)) doSetor(pessoa.alocacao.setor).extras++
  }
  return resumo
})

function textoResumoVagas(setor) {
  const r = resumoVagasPorSetor.value.get(setor)
  if (!r?.total) return ''
  return [
    `${r.total} ${r.total === 1 ? 'vaga' : 'vagas'}`,
    r.vazias ? `${r.vazias} ${r.vazias === 1 ? 'vazia' : 'vazias'}` : '',
    r.extras ? `${r.extras} ${r.extras === 1 ? 'extra' : 'extras'}` : ''
  ]
    .filter(Boolean)
    .join(', ')
}

// vagas vazias no cartão do setor: somem com os filtros que só pessoas
// têm (base, subsetor, responsável, busca, extras, afastados)
function vagasVaziasNoCartao(setor) {
  if (
    basesAtivas.value.length ||
    subsetoresAtivos.value.length ||
    responsaveisAtivos.value.length ||
    (busca.value || '').trim() ||
    !['', 'vagasVazias', 'alocados'].includes(filtroStatus.value)
  ) {
    return []
  }
  return vagasDoSetorPorFuncao(setor).flatMap(f => f.vagas.filter(v => !v.ocupante))
}

// vagas de um setor agrupadas por função, na ordem do BID (o servidor já
// manda as vagas ordenadas: setor, ordem, id)
function vagasDoSetorPorFuncao(setor) {
  const porFuncao = new Map()
  for (const vaga of vagas.value.filter(v => v.setor === setor)) {
    if (!porFuncao.has(vaga.funcao)) porFuncao.set(vaga.funcao, [])
    porFuncao.get(vaga.funcao).push({ ...vaga, ocupante: ocupantePorVaga.value.get(vaga.id) || null })
  }
  return [...porFuncao.entries()].map(([funcao, lista]) => ({ funcao, vagas: lista }))
}

const alocadosFiltrados = computed(() =>
  alocados.value.filter(pessoa => {
    const a = pessoa.alocacao
    if (basesAtivas.value.length && !basesAtivas.value.includes(a.base)) return false
    if (setoresAtivos.value.length && !setoresAtivos.value.includes(a.setor)) return false
    if (
      subsetoresAtivos.value.length &&
      !subsetoresAtivos.value.includes(subsetorEfetivo(pessoa) || SEM_SUBSETOR)
    ) {
      return false
    }
    if (
      responsaveisAtivos.value.length &&
      !responsaveisAtivos.value.includes(topoDaCadeia(pessoa))
    ) {
      return false
    }
    return casaComBusca(pessoa) && casaComStatus(pessoa)
  })
)

const semSetorFiltrados = computed(() =>
  pessoas.value.filter(
    pessoa =>
      !estaAlocado(pessoa) &&
      filtroStatus.value !== 'alocados' &&
      casaComStatus(pessoa) &&
      !setoresAtivos.value.length &&
      !subsetoresAtivos.value.length &&
      !responsaveisAtivos.value.length &&
      (!basesAtivas.value.length || basesAtivas.value.includes(pessoa.base_cadastro)) &&
      casaComBusca(pessoa) &&
      casaComBusca(pessoa, buscaSemSetor.value)
  )
)

// maiúsculas e sem acento, para comparar textos
function normalizarTexto(texto) {
  return String(texto || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
}

// Ordem do BID: a posição da vaga que a pessoa ocupa (as vagas já vêm
// ordenadas por setor, ordem do BID e id). Extra ou setor sem BID vai depois,
// e aí desempata o nome. Não há mais ordem pelo nome da função.
const SEM_POSICAO_NO_BID = Number.MAX_SAFE_INTEGER
const posicaoNoBid = computed(() => new Map(vagas.value.map((v, i) => [v.id, i])))

function ordemBid(chapa) {
  const vaga = vagaDe(alocadoPorChapa.value.get(chapa) || {})
  return vaga ? posicaoNoBid.value.get(vaga.id) : SEM_POSICAO_NO_BID
}

// setor -> base -> responsável -> pessoas
// O responsável é o chefe DIRETO (o organograma mostra a cadeia). Nos
// cartões, a pessoa fica no grupo do TOPO da cadeia dentro do setor: quem
// responde ao Rikelme, que responde à Camila, aparece sob a Camila.
const alocadoPorChapa = computed(() => new Map(alocados.value.map(p => [p.chapa, p])))

// Subsetor herdado: sem um próprio, a pessoa usa o do chefe (e assim por
// diante na cadeia, dentro do mesmo setor). Luís em OBRAS -> a equipe dele
// também. Quem tem subsetor próprio fica com o dele. "" = setor geral.
function subsetorEfetivo(pessoa) {
  const setor = pessoa.alocacao?.setor
  const vistos = new Set()
  let atual = pessoa
  while (atual?.alocacao && !vistos.has(atual.chapa)) {
    if (atual.alocacao.subsetor) return atual.alocacao.subsetor
    // pendurado abaixo de um bloco ("CARGO|SUBSETOR"): herda o do bloco
    const doBloco = (atual.alocacao.abaixo_de_funcao || '').split('|')[1]
    if (doBloco) return doBloco
    vistos.add(atual.chapa)
    const chefe = alocadoPorChapa.value.get(atual.alocacao.responsavel_chapa)
    if (!chefe || chefe.alocacao.setor !== setor) return ''
    atual = chefe
  }
  return ''
}

function topoDaCadeia(pessoa) {
  let chapa = pessoa.alocacao.responsavel_chapa || ''
  const vistos = new Set([pessoa.chapa])
  while (chapa && !vistos.has(chapa)) {
    vistos.add(chapa)
    const chefe = alocadoPorChapa.value.get(chapa)
    const acima = chefe?.alocacao.responsavel_chapa
    // o chefe está no mesmo setor e responde a outra pessoa: sobe mais um
    if (!chefe || chefe.alocacao.setor !== pessoa.alocacao.setor || !acima || acima === chapa) break
    chapa = acima
  }
  return chapa
}

function montarGruposSetor(lista) {
  const porSetor = new Map()
  for (const pessoa of lista) {
    const { setor, base } = pessoa.alocacao
    const chapaResp = topoDaCadeia(pessoa)
    if (!porSetor.has(setor)) porSetor.set(setor, new Map())
    const porBase = porSetor.get(setor)
    if (!porBase.has(base)) porBase.set(base, new Map())
    const porResp = porBase.get(base)
    const chave = chapaResp || ''
    if (!porResp.has(chave)) porResp.set(chave, [])
    porResp.get(chave).push(pessoa)
  }

  const porFuncaoENome = (a, b) =>
    ordemBid(a.chapa) - ordemBid(b.chapa) || a.nome.localeCompare(b.nome, 'pt-BR')

  return [...porSetor.entries()]
    .map(([nome, porBase]) => {
      const secoes = [...porBase.entries()]
        .map(([base, porResp]) => {
          const times = [...porResp.entries()]
            .map(([chapa, lista]) => ({
              chapa,
              responsavel: responsavelPorChapa(chapa),
              pessoas: lista.slice().sort(porFuncaoENome)
            }))
            .sort((a, b) => b.pessoas.length - a.pessoas.length)
          return {
            base,
            responsaveis: times,
            total: times.reduce((soma, t) => soma + t.pessoas.length, 0)
          }
        })
        .sort((a, b) => a.base.localeCompare(b.base))
      // O cabeçalho mostra só o responsável mais alto do setor (o topo da
      // cadeia com mais gente); quem responde a quem fica no organograma.
      const porTopo = new Map()
      for (const time of secoes.flatMap(s => s.responsaveis)) {
        if (!porTopo.has(time.chapa)) porTopo.set(time.chapa, [])
        porTopo.get(time.chapa).push(...time.pessoas)
      }
      const [chapaPrincipal, pessoasDoPrincipal] =
        [...porTopo.entries()].sort((a, b) => b[1].length - a[1].length)[0] || []
      return {
        nome,
        bases: secoes,
        total: secoes.reduce((soma, s) => soma + s.total, 0),
        responsavelPrincipal: chapaPrincipal !== undefined
          ? {
              chapa: chapaPrincipal,
              responsavel: responsavelPorChapa(chapaPrincipal),
              pessoas: pessoasDoPrincipal
            }
          : null
      }
    })
    .sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'))
}

const gruposSetor = computed(() => montarGruposSetor(alocadosFiltrados.value))

// ============================================================
// INDICADORES
// ============================================================

// ============================================================
// ORGANOGRAMA DO SETOR
// ============================================================
//
// Pessoa a pessoa: cada caixa é uma pessoa (cargo + nome) e fica abaixo de
// quem ela responde — o mesmo "Responsável" dos cartões da página. Quem é
// ASSESSORIA do chefe aparece ao lado da linha dele, fora da cadeia
// principal. A base entra só no cargo, "(BCB)", quando o setor tem mais de
// uma. Responsável de fora do setor aparece no topo, tracejado.

// setor: '' = visão geral (todos os setores). bases: só estas bases do setor
// (vazio = todas). topos: só estes responsáveis e quem está abaixo deles (vazio
// = todos). completo: veio da visão geral, ignora os filtros da página.
const organograma = reactive({ aberto: false, setor: '', bases: [], topos: [], completo: false })
const naVisaoGeral = computed(() => !organograma.setor)
const tituloOrganograma = computed(() =>
  [
    organograma.setor || 'Geral',
    ...(organograma.topos.length && organograma.topos.length <= 2
      ? [organograma.topos.map(c => nomeCurto(responsavelPorChapa(c)?.nome || c)).join(', ')]
      : []),
    ...(organograma.bases.length ? [organograma.bases.join(', ')] : [])
  ].join(' · ')
)
const salvandoOrganograma = ref(false)
// erro e aviso mostrados dentro do diálogo (o banner da página fica atrás dele)
const avisoOrganograma = ref({ tipo: '', texto: '' })

// no organograma, irmãos na ordem do BID (depois o nome)
const posicaoDoNo = no => no.ordemNoBid ?? ordemBid(no.chapa)
const porCargoENome = (a, b) =>
  posicaoDoNo(a) - posicaoDoNo(b) || a.nomeCompleto.localeCompare(b.nomeCompleto, 'pt-BR')

// a visão geral mostra todo mundo, independente dos filtros da página
const gruposCompletos = computed(() => montarGruposSetor(alocados.value))

const grupoOrganograma = computed(() =>
  (organograma.completo ? gruposCompletos : gruposSetor).value.find(g => g.nome === organograma.setor)
)

function estaNoRecorteDoOrganograma(pessoa) {
  const { bases: asBases, topos } = organograma
  return (
    (!asBases.length || asBases.includes(pessoa.alocacao.base)) &&
    (!topos.length || topos.includes(topoDaCadeia(pessoa)))
  )
}

const pessoasDoOrganograma = computed(() => {
  const grupo = grupoOrganograma.value
  if (!grupo) return []
  const todas = grupo.bases.flatMap(s => s.responsaveis.flatMap(t => t.pessoas))
  if (!organograma.bases.length && !organograma.topos.length) return todas
  // só uma parte: quem está nela e a cadeia acima, para não perder os níveis de cima
  const porChapa = new Map(todas.map(p => [p.chapa, p]))
  const escolhidas = new Set()
  for (const pessoa of todas.filter(estaNoRecorteDoOrganograma)) {
    let atual = pessoa
    while (atual && !escolhidas.has(atual)) {
      escolhidas.add(atual)
      atual = porChapa.get(atual.alocacao.responsavel_chapa)
    }
  }
  return todas.filter(p => escolhidas.has(p))
})

const totalDoOrganograma = computed(() => {
  const grupo = grupoOrganograma.value
  if (!grupo) return 0
  return pessoasDoOrganograma.value.filter(estaNoRecorteDoOrganograma).length
})

// Gerência: um setor como os outros, com a mesma cadeia de responsáveis e
// "Responsável pelas bases". Não entra como setor na cascata: é o topo dela.
const gruposDaVisaoGeral = computed(() =>
  gruposCompletos.value.filter(g => g.nome !== SETOR_GERENCIA)
)

const gerentes = computed(() => alocados.value.filter(p => p.alocacao.setor === SETOR_GERENCIA))

// parte de um setor: só estas bases (null = todas) e estes topos da cadeia
// (null = todos). Sem ninguém nesse recorte: null.
function noDoSetor(grupo, bases, prefixo, topos = null, toposLigados = null) {
  const secoes = grupo.bases
    .filter(b => !bases || bases.includes(b.base))
    .map(b => {
      const times = b.responsaveis.filter(t => !topos || topos.includes(t.chapa))
      return { base: b.base, times, total: times.reduce((soma, t) => soma + t.pessoas.length, 0) }
    })
    .filter(b => b.total)
  if (!secoes.length) return null
  const chapas = [...new Set(secoes.flatMap(b => b.times.map(t => t.chapa)).filter(Boolean))]
  const todosOsTopos = new Set(grupo.bases.flatMap(b => b.responsaveis.map(t => t.chapa)))
  return {
    tipo: 'setor',
    id: `${prefixo}-${grupo.nome}`,
    nome: grupo.nome,
    total: secoes.reduce((soma, b) => soma + b.total, 0),
    // todas as bases ou todos os topos: abre o setor sem aquele filtro
    filtroBases: bases && secoes.length < grupo.bases.length ? secoes.map(b => b.base) : [],
    filtroTopos: topos && topos.length < todosOsTopos.size ? topos : [],
    toposLigados,
    bases: secoes.map(b => ({ base: b.base, total: b.total })),
    responsaveis: chapas
      .map(chapa => {
        const dados = responsavelPorChapa(chapa)
        const dele = secoes
          .map(b => ({
            base: b.base,
            total: b.times.find(t => t.chapa === chapa)?.pessoas.length || 0
          }))
          .filter(b => b.total)
        return {
          chapa,
          nome: nomeCurto(dados?.nome || chapa),
          funcao: dados?.funcao || '',
          total: dele.reduce((soma, b) => soma + b.total, 0),
          bases: dele,
          // setor de uma base só mostra a base; em várias, "Todas as bases"
          todasAsBases: grupo.bases.length > 1 && dele.length === grupo.bases.length
        }
      })
      .sort(
        (a, b) =>
          ordemBid(a.chapa) - ordemBid(b.chapa) || a.nome.localeCompare(b.nome, 'pt-BR')
      )
  }
}

// Gerente geral > gerentes > setores > bases. Setor arrastado para um gerente
// fica inteiro com ele (abaixo ou como apoio); responsável arrastado sozinho
// leva só ele e quem está abaixo dele, em outro cartão do mesmo setor; o resto
// segue as bases marcadas em cada gerente. Quem está no topo sem base marcada fica acima de
// todos: os outros topos respondem a ele e o que nenhum gerente pegou fica
// direto abaixo dele. Sem ninguém assim, isso vai para "Sem gerente" (ninguém
// some da visão).
const cascataDaVisaoGeral = computed(() => {
  const grupos = gruposDaVisaoGeral.value
  if (!gerentes.value.length) return grupos.map(g => noDoSetor(g, null, 'geral'))

  // ligação para quem saiu da Gerência não vale: volta à regra das bases
  const ligacoes = setoresGerencia.value.filter(v =>
    gerentes.value.some(p => p.chapa === v.gerente_chapa)
  )
  // cada setor: a ligação do setor todo, as partes ligadas e o resto
  const repartidos = grupos.map(grupo => {
    const todosOsTopos = [...new Set(grupo.bases.flatMap(b => b.responsaveis.map(t => t.chapa)))]
    const inteiro = ligacoes.find(v => v.setor === grupo.nome && !v.responsavel_chapa)
    const partes = ligacoes.filter(
      v =>
        v.setor === grupo.nome &&
        todosOsTopos.includes(v.responsavel_chapa) &&
        // no mesmo lugar do setor todo: não precisa de outro cartão
        !(inteiro && inteiro.gerente_chapa === v.gerente_chapa && inteiro.apoio === v.apoio)
    )
    const ligados = partes.map(v => v.responsavel_chapa)
    return { grupo, inteiro, partes, resto: todosOsTopos.filter(c => !ligados.includes(c)) }
  })
  const soltos = repartidos.filter(r => !r.inteiro && r.resto.length)
  const setoresDasBases = (bases, prefixo) =>
    bases.length
      ? soltos.map(r => noDoSetor(r.grupo, bases, prefixo, r.resto)).filter(Boolean)
      : []
  const nos = new Map(
    gerentes.value.map(p => {
      const bases = [...(p.alocacao.bases_responsavel || [])].sort((a, b) => a.localeCompare(b, 'pt-BR'))
      return [
        p.chapa,
        {
          tipo: 'gerente',
          id: p.chapa,
          nome: nomeCurto(p.nome),
          funcao: funcaoExibida(p),
          bases,
          responsavel: p.alocacao.responsavel_chapa,
          assessoria: Boolean(p.alocacao.assessoria),
          filhos: [],
          apoios: []
        }
      ]
    })
  )
  let raizes = []
  for (const no of nos.values()) {
    const chefe = no.responsavel !== no.id ? nos.get(no.responsavel) : null
    if (chefe) (no.assessoria ? chefe.apoios : chefe.filhos).push(no)
    else raizes.push(no)
  }
  const acimaDeTodos = raizes.filter(no => !no.bases.length)
  acimaDeTodos.forEach(no => {
    no.acimaDeTodos = true
  })
  if (acimaDeTodos.length) {
    acimaDeTodos[0].filhos.push(...raizes.filter(no => no.bases.length))
    raizes = acimaDeTodos
  }
  // ciclo não acontece (o backend recusa); os setores vêm depois dos gerentes
  for (const no of nos.values()) no.filhos.push(...setoresDasBases(no.bases, no.id))
  const pendurar = (chapa, apoio, cartao) => {
    if (cartao) (apoio ? nos.get(chapa).apoios : nos.get(chapa).filhos).push(cartao)
  }
  for (const { grupo, inteiro, partes, resto } of repartidos) {
    if (inteiro) {
      const id = `ligado-${inteiro.gerente_chapa}-${inteiro.apoio}`
      pendurar(inteiro.gerente_chapa, inteiro.apoio, noDoSetor(grupo, null, id, resto))
    }
    // partes do setor no mesmo gerente e posição ficam num cartão só
    const destinos = new Map()
    for (const v of partes) {
      const chave = `${v.gerente_chapa}-${v.apoio}`
      if (!destinos.has(chave)) destinos.set(chave, { ...v, topos: [] })
      destinos.get(chave).topos.push(v.responsavel_chapa)
    }
    for (const [chave, v] of destinos) {
      const cartao = noDoSetor(grupo, null, `parte-${chave}`, v.topos, v.topos)
      pendurar(v.gerente_chapa, v.apoio, cartao)
    }
  }

  const cobertas = new Set([...nos.values()].flatMap(no => no.bases))
  const basesDosSoltos = soltos.flatMap(
    r => noDoSetor(r.grupo, null, '', r.resto)?.bases.map(b => b.base) || []
  )
  const semGerente = [...new Set(basesDosSoltos)].filter(
    base => !cobertas.has(base)
  )
  const sobras = setoresDasBases(semGerente, acimaDeTodos[0]?.id || 'sem-gerente')
  if (sobras.length && acimaDeTodos.length) {
    acimaDeTodos[0].filhos.push(...sobras)
  } else if (sobras.length) {
    const noSem = {
      tipo: 'gerente',
      id: 'sem-gerente',
      semGerente: true,
      nome: 'Sem gerente',
      funcao: '',
      bases: semGerente,
      filhos: sobras,
      apoios: []
    }
    // abaixo do gerente geral quando existe um só no topo
    if (raizes.length === 1) raizes[0].filhos.push(noSem)
    else raizes.push(noSem)
  }
  return raizes
})

// Desenho da visão geral: os mesmos nós do organograma do setor. Gerente é
// uma pessoa. Setor com um responsável só é um cartão único (o setor na faixa,
// como "a caixa da base e a dele viram uma só" no organograma do setor). Com
// vários, setor é uma pílula e cada responsável um cartão na cor do setor.
function detalheDoResponsavel(responsavel) {
  const bases = responsavel.todasAsBases
    ? 'Todas as bases'
    : responsavel.bases.map(b => b.base).join(' · ')
  return `${bases} · ${responsavel.total} ${responsavel.total === 1 ? 'pessoa' : 'pessoas'}`
}

function noDeResponsavel(setor, responsavel) {
  return {
    id: `${setor.id}-${responsavel.chapa}`,
    tipo: 'pessoa',
    chapa: responsavel.chapa,
    cargo: responsavel.funcao,
    nome: responsavel.nome,
    detalhe: detalheDoResponsavel(responsavel),
    cor: coresDosSetores.value[setor.nome],
    externo: false,
    naoRecebe: true,
    arrastarComo: { setor: setor.nome, nome: responsavel.nome, responsaveis: [responsavel.chapa] },
    aoClicar: () => abrirDaVisaoGeral(setor.nome, setor.filtroBases, [responsavel.chapa]),
    filhos: [],
    assessores: []
  }
}

function noDaVisaoGeral(no) {
  if (no.tipo === 'setor') {
    const arrastarComo = { setor: no.nome, nome: no.nome, responsaveis: no.toposLigados || [] }
    const aoClicar = () => abrirDaVisaoGeral(no.nome, no.filtroBases, no.filtroTopos)
    if (no.responsaveis.length === 1) {
      return {
        ...noDeResponsavel(no, no.responsaveis[0]),
        id: no.id,
        baseTitulo: no.nome,
        iconeFaixa: 'apartment',
        arrastarComo,
        aoClicar
      }
    }
    return {
      id: no.id,
      tipo: 'base',
      icone: 'apartment',
      titulo: no.nome,
      subtitulo: `${no.total} ${no.total === 1 ? 'pessoa' : 'pessoas'}`,
      naoRecebe: true,
      // cartão com só parte do setor, ligada a um gerente: leva só essa parte
      arrastarComo,
      aoClicar,
      filhos: no.responsaveis.map(r => noDeResponsavel(no, r)),
      assessores: []
    }
  }
  if (no.semGerente) {
    return {
      id: no.id,
      tipo: 'base',
      icone: 'help_outline',
      titulo: no.nome,
      subtitulo: '',
      semGerente: true,
      filhos: no.filhos.map(noDaVisaoGeral),
      assessores: []
    }
  }
  return {
    id: no.id,
    tipo: 'pessoa',
    chapa: no.id,
    cargo: no.funcao,
    nome: no.nome,
    externo: false,
    acimaDeTodos: no.acimaDeTodos,
    apoioDosDoisLados: true,
    filhos: no.filhos.map(noDaVisaoGeral),
    assessores: no.apoios.map(noDaVisaoGeral)
  }
}

const arvoreDaVisaoGeral = computed(() => {
  const nos = cascataDaVisaoGeral.value.map(noDaVisaoGeral)
  if (gerentes.value.length) return nos
  return [
    {
      id: 'gerencia',
      tipo: 'base',
      icone: 'corporate_fare',
      titulo: 'Gerência',
      subtitulo: '',
      naoRecebe: true,
      filhos: nos,
      assessores: []
    }
  ]
})

// Paleta discreta, uma cor por subsetor do organograma aberto: os tons são
// espalhados igualmente no círculo de cores, então crescem ou diminuem com a
// quantidade de subsetores. "Geral" (sem subsetor) fica neutro, sem cor.
const subsetoresDoOrganograma = computed(() =>
  [...new Set(pessoasDoOrganograma.value.map(subsetorEfetivo).filter(Boolean))].sort(
    (a, b) => a.localeCompare(b, 'pt-BR')
  )
)

function paletaDe(nomes) {
  const cores = {}
  nomes.forEach((nome, i) => {
    const matiz = Math.round((200 + (i * 360) / nomes.length) % 360)
    cores[nome] = {
      fundo: `hsl(${matiz} 60% 97%)`,
      borda: `hsl(${matiz} 45% 62%)`,
      fundoEscuro: `hsl(${matiz} 22% 19%)`,
      bordaEscura: `hsl(${matiz} 40% 55%)`
    }
  })
  return cores
}

const coresDosSubsetores = computed(() => paletaDe(subsetoresDoOrganograma.value))
const coresDosSetores = computed(() => paletaDe(gruposDaVisaoGeral.value.map(g => g.nome)))

// subsetores juntos (Geral primeiro), depois cargo e nome
const porSubsetorCargoENome = (a, b) =>
  (a.subsetor || '').localeCompare(b.subsetor || '', 'pt-BR') || porCargoENome(a, b)

// Bases separadas: quando os subordinados de alguém estão em bases
// diferentes da base em que ele já está desenhado, eles vão para caixas de
// base (BCB, BDC...) logo abaixo dele. Equipe toda na mesma base: sem caixa.
// Responsável por UMA base: a caixa dele já é a da base (faixa no topo).
// Responsável por VÁRIAS: ele em cima, as bases dele abaixo, a equipe em
// cada base.
function separarPorBase(no, baseAtual) {
  // com filtro de bases, só as caixas das bases que estão no desenho
  const minhas = (no.basesResponsavel || []).filter(
    b => !organograma.bases.length || organograma.bases.includes(b)
  )
  if (minhas.length === 1) {
    no.baseTitulo = minhas[0]
    baseAtual = minhas[0]
  }
  const forcar = minhas.length > 1
  // quem responde por várias bases fica direto abaixo do chefe (as bases
  // dele aparecem abaixo dele), sem ir para a caixa da base em que está
  const variosLideres = no.filhos.filter(f => (f.basesResponsavel || []).length > 1)
  // vaga vazia sem base (chefe sem base própria): direto abaixo dele
  const vagasSemBase = no.filhos.filter(f => f.tipo === 'vaga' && !f.base)
  const demais = no.filhos.filter(f => !variosLideres.includes(f) && !vagasSemBase.includes(f))
  variosLideres.forEach(f => separarPorBase(f, null))
  const bases = [...new Set(demais.map(f => f.base))]
  if (!forcar && (!bases.length || (bases.length === 1 && bases[0] === baseAtual))) {
    demais.forEach(f => separarPorBase(f, baseAtual))
    return
  }
  const lista = forcar ? [...new Set([...minhas, ...bases])] : bases
  no.filhos = [
    ...variosLideres,
    ...vagasSemBase,
    ...lista
      .sort((a, b) => a.localeCompare(b, 'pt-BR'))
      .flatMap(base => caixaDaBase(no, base, demais, forcar))
  ]
}

// Para economizar espaço: irmãos com a mesma função que não lideram ninguém
// (sem subordinados, sem assessoria, sem base própria) viram um cartão só,
// com o cargo e a lista de nomes. chefe = a pessoa acima (uma caixa de base
// no meio não muda o chefe).
// mesma função E mesmo subsetor (a base já vem separada pelas caixas),
// sem subordinados: viram um cartão de grupo. assessoria = grupo ao lado
// da linha (soltar alguém da mesma função nele também vira assessoria)
function agruparFolhas(lista, prefixo, chefe, assessoria) {
  const folha = f =>
    f.tipo === 'pessoa' && !f.filhos.length && !f.assessores.length && !f.baseTitulo && !f.externo
  const chave = f => `${f.cargo}|${f.subsetor}`
  const porCargo = new Map()
  for (const f of lista.filter(folha)) {
    if (!porCargo.has(chave(f))) porCargo.set(chave(f), [])
    porCargo.get(chave(f)).push(f)
  }
  const emitidos = new Set()
  return lista.flatMap(f => {
    const iguais = folha(f) ? porCargo.get(chave(f)) : null
    if (!iguais || iguais.length < 2) return [f]
    if (emitidos.has(chave(f))) return []
    emitidos.add(chave(f))
    return [
      {
        id: `grupo-${prefixo}-${chave(f)}`,
        tipo: 'grupo',
        cargo: f.cargo,
        subsetor: f.subsetor,
        cor: f.cor,
        assessoria,
        chefe: chefe.chapa || '',
        chefeNome: chefe.nome || '',
        pessoas: iguais
          .map(i => ({ chapa: i.chapa, nome: i.nome, nomeCompleto: i.nomeCompleto, extra: i.extra, detalhe: i.detalhe }))
          .sort((a, b) => a.nomeCompleto.localeCompare(b.nomeCompleto, 'pt-BR')),
        filhos: [],
        assessores: []
      }
    ]
  })
}

function agruparMesmaFuncao(no, chefe) {
  const chefeDosFilhos = no.tipo === 'base' ? chefe : no
  // quem foi pendurado abaixo de um bloco de função (abaixoDeFuncao =
  // "CARGO" ou "CARGO|SUBSETOR") sai da lista agora e entra abaixo daquele
  // bloco exato — pode haver dois blocos da mesma função (subsetores
  // diferentes, ou um cartão individual e um agrupado)
  const casaComBloco = (o, f) => {
    const [cargo, subsetor] = f.abaixoDeFuncao.split('|')
    return (
      o !== f &&
      !o.abaixoDeFuncao &&
      o.cargo === cargo &&
      (subsetor === undefined || (o.subsetor || '') === subsetor)
    )
  }
  const temBloco = f => f.abaixoDeFuncao && no.filhos.some(o => casaComBloco(o, f))
  const pendurados = no.filhos.filter(temBloco)
  no.filhos = no.filhos.filter(f => !pendurados.includes(f))
  no.filhos = agruparFolhas(no.filhos, `${no.id}`, chefeDosFilhos, false)
  // a assessoria também junta quem tem a mesma função num cartão só
  no.assessores = agruparFolhas(no.assessores, `${no.id}-assessoria`, no, true)
  // pendura cada um abaixo do bloco da função escolhida; entre eles, quem
  // tiver a mesma função vira um cartão só (agrupado no passo recursivo)
  for (const f of pendurados) {
    // o cartão agrupado tem preferência sobre um cartão individual do mesmo cargo
    const bloco =
      no.filhos.find(o => o.tipo === 'grupo' && casaComBloco(o, f)) ||
      no.filhos.find(o => casaComBloco(o, f))
    bloco.filhos.push(f)
  }
  no.filhos.forEach(f => agruparMesmaFuncao(f, chefeDosFilhos))
  no.assessores.forEach(f => agruparMesmaFuncao(f, no))
}

// caixa de uma base com os subordinados daquela base
function caixaDaBase(no, base, filhos, forcar) {
  const daBase = filhos.filter(f => f.base === base)
  daBase.forEach(f => separarPorBase(f, base))
  // quem responde só por esta base já é a caixa dela
  if (!forcar && daBase.length && daBase.every(f => f.baseTitulo === base)) return daBase
  const total = daBase.reduce((soma, f) => soma + contarPessoas(f), 0)
  return [
    {
      id: `base-${no.id}-${base}`,
      tipo: 'base',
      titulo: base,
      // soltar alguém na caixa da base = responder a quem está acima dela
      chefe: no.chapa || '',
      chefeNome: no.nome || '',
      subtitulo: `${total} ${total === 1 ? 'pessoa' : 'pessoas'}`,
      filhos: daBase,
      assessores: []
    }
  ]
}

function contarPessoas(no) {
  if (no.tipo === 'grupo') return no.pessoas.length
  const propria = no.tipo === 'pessoa' && !no.externo ? 1 : 0
  return propria + [...no.filhos, ...no.assessores].reduce((soma, f) => soma + contarPessoas(f), 0)
}

const arvoreOrganograma = computed(() => {
  const grupo = grupoOrganograma.value
  if (!grupo) return []
  // a Gerência não se divide em caixas: as bases dos gerentes são as que eles
  // cuidam nos outros setores, não onde eles estão
  const variasBases =
    grupo.nome !== SETOR_GERENCIA &&
    new Set(pessoasDoOrganograma.value.filter(estaNoRecorteDoOrganograma).map(p => p.alocacao.base)).size > 1
  const nos = new Map()

  for (const pessoa of pessoasDoOrganograma.value) {
    // cargo do cartão: o da vaga do BID que ocupa; só o extra mostra a função real
    const funcao = vagaDe(pessoa)?.funcao || funcaoExibida(pessoa) || 'SEM FUNÇÃO'
    nos.set(pessoa.chapa, {
      id: pessoa.chapa,
      chapa: pessoa.chapa,
      funcao,
      tipo: 'pessoa',
      base: pessoa.alocacao.base,
      basesResponsavel: pessoa.alocacao.bases_responsavel || [],
      cargo: funcao,
      abaixoDeFuncao: pessoa.alocacao.abaixo_de_funcao || '',
      subsetor: subsetorEfetivo(pessoa),
      cor: coresDosSubsetores.value[subsetorEfetivo(pessoa)] || null,
      nome: nomeCurto(pessoa.nome),
      nomeCompleto: pessoa.nome,
      assessoria: Boolean(pessoa.alocacao.assessoria),
      externo: false,
      responsavel: pessoa.alocacao.responsavel_chapa || '',
      // BID: sem vaga = extra (selo laranja)
      extra: ehExtra(pessoa),
      filhos: [],
      assessores: []
    })
  }
  // chefe que não está no desenho, no topo: tracejado se estiver alocado em
  // OUTRO setor ("fora do setor") ou escondido pelos filtros ("fora do
  // filtro"); normal se não estiver alocado em lugar nenhum (lidera o setor)
  for (const no of nos.values()) {
    const chapa = no.responsavel
    if (!chapa || chapa === no.chapa || nos.has(chapa)) continue
    const dados = responsavelPorChapa(chapa)
    const setorDele = alocadoPorChapa.value.get(chapa)?.alocacao.setor
    const externo = !setorDele ? false : setorDele === grupo.nome ? 'fora do filtro' : 'fora do setor'
    nos.set(chapa, {
      id: chapa,
      chapa,
      funcao: dados?.funcao || '',
      tipo: 'pessoa',
      base: '',
      basesResponsavel: [],
      semAlocacao: !setorDele,
      cargo: dados?.funcao || '',
      subsetor: '',
      cor: null,
      nome: nomeCurto(dados?.nome || chapa),
      nomeCompleto: dados?.nome || chapa,
      assessoria: false,
      externo,
      responsavel: '',
      filhos: [],
      assessores: []
    })
  }

  // liga cada um ao chefe; ciclo (A responde a B e B a A) vira topo
  const chefe = no => (no.responsavel && no.responsavel !== no.chapa ? nos.get(no.responsavel) : null)
  const raizes = []
  for (const no of nos.values()) {
    let acima = chefe(no)
    const vistos = new Set([no])
    while (acima && !vistos.has(acima)) {
      vistos.add(acima)
      acima = chefe(acima)
    }
    const pai = acima ? null : chefe(no)
    if (!pai) raizes.push(no)
    else (no.assessoria ? pai.assessores : pai.filhos).push(no)
  }
  // vagas vazias arrastadas para alguém (ou só para uma base): entram na
  // cadeia, na base delas; as outras (ou as de quem está fora do desenho)
  // ficam na caixa "Vagas vazias"
  const naCaixa = []
  if (!organograma.topos.length) {
    for (const lista of vagasVaziasAgrupadas(grupo.nome)) {
      const [vaga] = lista
      if (organograma.bases.length && vaga.base && !organograma.bases.includes(vaga.base)) continue
      const chefeDaVaga = vaga.responsavel_chapa ? nos.get(vaga.responsavel_chapa) : null
      const pai =
        chefeDaVaga ||
        (vaga.base && !vaga.responsavel_chapa
          ? raizes.find(r => r.base === vaga.base) || raizes.find(r => r.tipo === 'pessoa')
          : null)
      if (pai) pai.filhos.push(noDeVagas(lista, vaga.base || pai.base))
      else naCaixa.push(...lista)
    }
  }
  const ordenar = lista => {
    lista.sort(porSubsetorCargoENome)
    lista.forEach(no => {
      ordenar(no.filhos)
      ordenar(no.assessores)
    })
    return lista
  }
  ordenar(raizes)
  // um setor de base única não precisa da caixa da base
  if (variasBases) raizes.forEach(raiz => separarPorBase(raiz, raiz.base || null))
  raizes.forEach(raiz => agruparMesmaFuncao(raiz, raiz))
  const caixa = organograma.topos.length ? null : caixaDasVagasVazias(naCaixa)
  return caixa ? [...raizes, caixa] : raizes
})

// vagas vazias do setor juntas por função e lugar no desenho (chefe + base),
// na ordem do BID
function vagasVaziasAgrupadas(setor) {
  const grupos = new Map()
  for (const vaga of vagasVaziasDoSetor(setor)) {
    const chave = `${vaga.funcao}|${vaga.responsavel_chapa}|${vaga.base}`
    if (!grupos.has(chave)) grupos.set(chave, [])
    grupos.get(chave).push(vaga)
  }
  return [...grupos.values()]
}

// cartão de vagas vazias da mesma função ("2 vagas vazias")
function noDeVagas(lista, base) {
  const [vaga] = lista
  return {
    id: `vaga-${vaga.id}`,
    tipo: 'vaga',
    cargo: vaga.funcao,
    vagaIds: lista.map(v => v.id),
    quantidade: lista.length,
    base: base || '',
    subsetor: '',
    nomeCompleto: '',
    ordemNoBid: posicaoNoBid.value.get(vaga.id),
    filhos: [],
    assessores: []
  }
}

// Vagas do BID sem lugar no desenho: uma caixa ao lado do organograma, com
// um cartão por função. Arraste o cartão para alguém (fica abaixo dela) ou
// para uma base; solte uma pessoa do setor nele para pôr na vaga. A caixa
// aparece também vazia quando o setor tem vagas posicionadas, para receber
// de volta as que forem tiradas da cadeia.
function caixaDasVagasVazias(lista) {
  const temPosicionadas = vagasVaziasDoSetor(organograma.setor).length > lista.length
  if (!lista.length && !(temPosicionadas && podeEditar.value)) return null
  const porFuncao = new Map()
  for (const vaga of lista) {
    if (!porFuncao.has(vaga.funcao)) porFuncao.set(vaga.funcao, [])
    porFuncao.get(vaga.funcao).push(vaga)
  }
  return {
    id: 'vagas-vazias',
    tipo: 'base',
    titulo: 'Vagas vazias',
    icone: 'event_seat',
    subtitulo: lista.length
      ? `${lista.length} ${lista.length === 1 ? 'vaga' : 'vagas'} sem lugar`
      : 'solte aqui para tirar da cadeia',
    naoRecebe: true,
    recebeVagas: true,
    filhos: [...porFuncao.values()].map(vagasDaFuncao => noDeVagas(vagasDaFuncao, '')),
    assessores: []
  }
}

function abrirOrganograma(grupo) {
  avisoOrganograma.value = { tipo: '', texto: '' }
  Object.assign(organograma, { aberto: true, setor: grupo.nome, bases: [], topos: [], completo: false })
}

function abrirVisaoGeral() {
  avisoOrganograma.value = { tipo: '', texto: '' }
  Object.assign(organograma, { aberto: true, setor: '', bases: [], topos: [], completo: true })
}

function abrirDaVisaoGeral(setor, basesDoSetor, topos = []) {
  avisoOrganograma.value = { tipo: '', texto: '' }
  Object.assign(organograma, { aberto: true, setor, bases: basesDoSetor, topos, completo: true })
}

// Desenho maior que a janela abriria rolado para a esquerda, com o topo (que
// fica no meio) fora da vista. Só ao abrir ou trocar de visão: depois de
// arrastar alguém, a rolagem fica onde a pessoa deixou.
watch(
  () => [organograma.aberto, organograma.setor, organograma.completo],
  async () => {
    if (!organograma.aberto) {
      return
    }
    await nextTick()
    const area = desenhoOrganograma.value?.closest('.area-organograma')
    if (area) {
      area.scrollLeft = (area.scrollWidth - area.clientWidth) / 2
    }
  }
)

// ---------- arrastar (só quem edita; ver OrganogramaNo.vue)

const emArraste = ref(null)

function chefeDe(chapa) {
  const responsavel = alocadoPorChapa.value.get(chapa)?.alocacao.responsavel_chapa
  return responsavel && responsavel !== chapa ? responsavel : ''
}

// "b" está abaixo de "a" na cadeia de responsáveis?
function estaAbaixoDe(b, a) {
  const vistos = new Set()
  let atual = chefeDe(b)
  while (atual && !vistos.has(atual)) {
    if (atual === a) return true
    vistos.add(atual)
    atual = chefeDe(atual)
  }
  return false
}

async function salvarOrganograma(mudancas, mensagem) {
  salvandoOrganograma.value = true
  avisoOrganograma.value = { tipo: '', texto: '' }
  try {
    await chamarApi(
      '/api/indiretos/organograma',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mudancas })
      },
      'Não foi possível mover no organograma.'
    )
    avisoOrganograma.value = { tipo: 'ok', texto: mensagem }
    await carregar()
  } catch (e) {
    avisoOrganograma.value = { tipo: 'erro', texto: e.message }
  } finally {
    salvandoOrganograma.value = false
  }
}

function soltarNoOrganograma(origem, alvo, posicao) {
  // visão geral: setor ou responsável de setor solto num gerente
  if (origem.setor) {
    soltarSetorNoGerente(origem, alvo, posicao)
    return
  }
  if (origem.vagaIds) {
    posicionarVagas(origem, alvo)
    return
  }
  if (alvo.vaga) {
    soltarNaVaga(origem, alvo)
    return
  }
  // soltou sobre um cartão agrupado (várias pessoas da mesma função)
  if (alvo.grupo) {
    soltarNoGrupo(origem, alvo)
    return
  }
  // cartão de grupo arrastado: todas as pessoas dele vão juntas
  if (origem.chapas) {
    moverGrupo(origem, alvo, posicao)
    return
  }
  if (origem.chapa === alvo.chapa) return
  const quem = origem.nome
  const de = alvo.nome
  if (posicao !== 'acima' && estaAbaixoDe(alvo.chapa, origem.chapa)) {
    avisoOrganograma.value = {
      tipo: 'erro',
      texto: `${de} já está abaixo de ${quem}: primeiro mova ${de} para outro lugar.`
    }
    return
  }
  if (posicao === 'lado') {
    salvarOrganograma(
      [{ chapa: origem.chapa, responsavel_chapa: alvo.chapa, assessoria: true }],
      `${quem} agora é assessoria de ${de}.`
    )
    return
  }
  if (posicao === 'acima') {
    // quem foi arrastado fica com o chefe do alvo, e o alvo passa a responder a ele
    // (acima de quem não tem chefe: vira o novo topo, respondendo a si mesmo)
    const chefeAtual = chefeDe(alvo.chapa)
    const chefeDoAlvo = chefeAtual || origem.chapa
    if (alvo.externo || !alocadoPorChapa.value.has(alvo.chapa) || chefeAtual === origem.chapa) {
      avisoOrganograma.value = { tipo: 'erro', texto: `Não dá para pôr ${quem} acima de ${de}.` }
      return
    }
    salvarOrganograma(
      [
        { chapa: origem.chapa, responsavel_chapa: chefeDoAlvo, assessoria: false },
        { chapa: alvo.chapa, responsavel_chapa: origem.chapa, assessoria: false }
      ],
      `${quem} agora fica acima de ${de}.`
    )
    return
  }
  salvarOrganograma(
    [{ chapa: origem.chapa, responsavel_chapa: alvo.chapa, assessoria: false }],
    `${quem} agora responde a ${de}.`
  )
}

// ---------- responsável por base (clicar na pessoa)

const basesDaPessoa = reactive({
  aberto: false,
  chapa: '',
  nome: '',
  bases: [],
  basesOriginais: [],
  subsetor: null,
  subsetorDigitado: '',
  subsetorOriginal: ''
})

// todas as bases do setor (sem filtro): as que dá para marcar
const marcandoBasesDeGerente = computed(
  () => naVisaoGeral.value || organograma.setor === SETOR_GERENCIA
)

const basesDoSetorOrganograma = computed(() =>
  marcandoBasesDeGerente.value
    ? bases.value
    : [...new Set(alocados.value.filter(p => p.alocacao.setor === organograma.setor).map(p => p.alocacao.base))]
        .sort((a, b) => a.localeCompare(b, 'pt-BR'))
)

// subsetores que já existem no setor (pode digitar um novo)
const termoSubsetorOrganograma = ref('')
const opcoesSubsetorOrganograma = computed(() => {
  const termo = termoSubsetorOrganograma.value.toLowerCase()
  return [
    ...new Set(
      alocados.value
        .filter(p => p.alocacao.setor === organograma.setor && p.alocacao.subsetor)
        .map(p => p.alocacao.subsetor)
    )
  ]
    .sort((a, b) => a.localeCompare(b, 'pt-BR'))
    .filter(nome => !termo || nome.toLowerCase().includes(termo))
})

function filtrarSubsetoresOrganograma(termo, atualizar) {
  atualizar(() => {
    termoSubsetorOrganograma.value = termo || ''
  })
}

const subsetorDaPessoaEscolhido = computed(() =>
  String(basesDaPessoa.subsetor || basesDaPessoa.subsetorDigitado || '')
    .trim()
    .replace(/\s+/g, ' ')
    .toUpperCase()
)

// vazio: mostra o que herda do chefe
const dicaSubsetorDaPessoa = computed(() => {
  const pessoa = alocadoPorChapa.value.get(basesDaPessoa.chapa)
  const chefe = pessoa ? alocadoPorChapa.value.get(pessoa.alocacao.responsavel_chapa) : null
  const herdado =
    chefe && chefe !== pessoa && chefe.alocacao.setor === pessoa.alocacao.setor
      ? subsetorEfetivo(chefe)
      : ''
  if (subsetorDaPessoaEscolhido.value) return 'Quem estiver abaixo dele também passa a ser deste subsetor.'
  return herdado
    ? `Vazio: herda de ${nomeCurto(chefe.nome)} (${herdado}).`
    : 'Vazio: setor geral. Escolha um ou digite um novo.'
})

function abrirBasesDaPessoa(chapa) {
  const pessoa = alocadoPorChapa.value.get(chapa)
  if (!pessoa) return
  termoSubsetorOrganograma.value = ''
  const bases = [...(pessoa.alocacao.bases_responsavel || [])]
  Object.assign(basesDaPessoa, {
    aberto: true,
    chapa,
    nome: nomeCurto(pessoa.nome),
    bases,
    basesOriginais: [...bases],
    subsetor: pessoa.alocacao.subsetor || null,
    subsetorDigitado: '',
    subsetorOriginal: pessoa.alocacao.subsetor || ''
  })
}

// grava só o que mudou: subsetor (pela alocação) e/ou bases
async function salvarBasesDaPessoa() {
  const pessoa = alocadoPorChapa.value.get(basesDaPessoa.chapa)
  if (!pessoa) return
  const subsetor = subsetorDaPessoaEscolhido.value
  const mudouSubsetor = subsetor !== basesDaPessoa.subsetorOriginal
  const mudouBases =
    [...basesDaPessoa.bases].sort().join(',') !== [...basesDaPessoa.basesOriginais].sort().join(',')
  if (!mudouSubsetor && !mudouBases) {
    basesDaPessoa.aberto = false
    return
  }
  salvandoOrganograma.value = true
  avisoOrganograma.value = { tipo: '', texto: '' }
  const avisos = []
  try {
    if (mudouSubsetor) {
      const a = pessoa.alocacao
      await chamarApi(
        '/api/indiretos/alocar',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chapa: pessoa.chapa,
            setor: a.setor,
            base: a.base,
            responsavel_chapa: a.responsavel_chapa,
            observacao: a.observacao,
            subsetor
          })
        },
        'Não foi possível salvar o subsetor.'
      )
      avisos.push(subsetor ? `subsetor ${subsetor}` : 'subsetor removido')
    }
    if (mudouBases) {
      const dados = await chamarApi(
        '/api/indiretos/responsavel-base',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ chapa: basesDaPessoa.chapa, bases: basesDaPessoa.bases })
        },
        'Não foi possível salvar o responsável pela base.'
      )
      const bases = basesDaPessoa.bases
      avisos.push(
        bases.length
          ? `responde por ${bases.join(', ')} (${dados.movidos} ${dados.movidos === 1 ? 'pessoa passou' : 'pessoas passaram'} a responder a ele)`
          : 'não responde mais por nenhuma base'
      )
    }
    avisoOrganograma.value = { tipo: 'ok', texto: `${basesDaPessoa.nome}: ${avisos.join('; ')}.` }
    basesDaPessoa.aberto = false
    await carregar()
  } catch (e) {
    avisoOrganograma.value = { tipo: 'erro', texto: e.message }
    await carregar()
  } finally {
    salvandoOrganograma.value = false
  }
}

// Mesma função do grupo: entra nele (passa a responder ao mesmo chefe).
// Outra função: pergunta a qual pessoa do grupo passa a responder — ex.:
// auxiliares soltos no cartão dos almoxarifes escolhem o almoxarife.
// BLOCO = opção "abaixo do bloco todo" (sem ligar a uma pessoa)
const BLOCO = '__BLOCO__'
const escolhaDoChefe = reactive({
  aberto: false,
  origem: null,
  cargo: '',
  subsetor: '',
  chefe: '',
  chefeNome: '',
  pessoas: [],
  chapa: null
})

const opcoesEscolhaDoChefe = computed(() => [
  { label: `Abaixo do bloco ${escolhaDoChefe.cargo} (todos)`, value: BLOCO },
  ...escolhaDoChefe.pessoas.map(p => ({ label: p.nomeCompleto, value: p.chapa }))
])

function soltarNoGrupo(origem, alvo) {
  if (origem.cargo === alvo.cargo) {
    if (!alvo.chefe) return
    // grupo da assessoria: entra também como assessoria do mesmo chefe
    soltarNoOrganograma(
      origem,
      { chapa: alvo.chefe, nome: alvo.chefeNome },
      alvo.assessoria ? 'lado' : 'abaixo'
    )
    return
  }
  Object.assign(escolhaDoChefe, {
    aberto: true,
    origem,
    cargo: alvo.cargo,
    subsetor: alvo.subsetor || '',
    chefe: alvo.chefe,
    chefeNome: alvo.chefeNome,
    pessoas: alvo.pessoas,
    chapa: BLOCO
  })
}

function confirmarEscolhaDoChefe() {
  if (escolhaDoChefe.chapa === BLOCO) {
    escolhaDoChefe.aberto = false
    pendurarNoBloco(escolhaDoChefe.origem, escolhaDoChefe)
    return
  }
  const escolhido = escolhaDoChefe.pessoas.find(p => p.chapa === escolhaDoChefe.chapa)
  if (!escolhido) return
  escolhaDoChefe.aberto = false
  soltarNoOrganograma(escolhaDoChefe.origem, { chapa: escolhido.chapa, nome: escolhido.nome }, 'abaixo')
}

// abaixo do bloco: responde ao chefe do bloco e aparece pendurado nele
function pendurarNoBloco(origem, bloco) {
  if (!bloco.chefe) return
  const chapas = origem.chapas || [origem.chapa]
  salvarOrganograma(
    chapas.map(chapa => ({
      chapa,
      responsavel_chapa: bloco.chefe,
      assessoria: false,
      // guarda o bloco exato: função e, se tiver, subsetor
      abaixo_de_funcao: bloco.subsetor ? `${bloco.cargo}|${bloco.subsetor}` : bloco.cargo
    })),
    `${origem.nome} agora ${chapas.length > 1 ? 'ficam' : 'fica'} abaixo do bloco ${bloco.cargo}.`
  )
}

function moverGrupo(origem, alvo, posicao) {
  const chapas = origem.chapas.filter(chapa => chapa !== alvo.chapa)
  if (chapas.some(chapa => estaAbaixoDe(alvo.chapa, chapa))) {
    avisoOrganograma.value = {
      tipo: 'erro',
      texto: `${alvo.nome} está abaixo de alguém do grupo: mova ${alvo.nome} primeiro.`
    }
    return
  }
  const assessoria = posicao === 'lado'
  salvarOrganograma(
    chapas.map(chapa => ({ chapa, responsavel_chapa: alvo.chapa, assessoria })),
    `${origem.nome} agora ${assessoria ? 'são assessoria de' : 'respondem a'} ${alvo.nome}.`
  )
}

// Setor solto num gerente: fica inteiro com ele, abaixo ou como apoio. Nome de
// um responsável: só ele e quem está abaixo dele. Em "Sem gerente" (ou o nome
// solto em quem está acima de todos), desfaz a ligação e volta com o resto.
async function soltarSetorNoGerente(origem, alvo, posicao) {
  const apoio = posicao === 'lado'
  const responsaveis = origem.responsaveis || []
  const desfazer = alvo.semGerente || (responsaveis.length && alvo.acimaDeTodos && !apoio)
  salvandoOrganograma.value = true
  avisoOrganograma.value = { tipo: '', texto: '' }
  try {
    await chamarApi(
      '/api/indiretos/setor-gerente',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          setor: origem.setor,
          responsaveis,
          gerente_chapa: desfazer ? '' : alvo.chapa,
          apoio
        })
      },
      'Não foi possível ligar ao gerente.'
    )
    let texto = `${origem.nome} agora fica abaixo de ${alvo.nome}.`
    if (desfazer) texto = `${origem.nome} voltou para o resto do setor ${origem.setor}.`
    else if (apoio) texto = `${origem.nome} agora é apoio de ${alvo.nome}.`
    avisoOrganograma.value = { tipo: 'ok', texto }
    await carregar()
  } catch (e) {
    avisoOrganograma.value = { tipo: 'erro', texto: e.message }
  } finally {
    salvandoOrganograma.value = false
  }
}

provide('arrasteOrganograma', {
  habilitado: computed(() => podeEditar.value && !salvandoOrganograma.value),
  emArraste,
  soltar: soltarNoOrganograma,
  abrirBases: abrirBasesDaPessoa,
  abrirVaga: id => vagaPorId.value.get(id) && abrirOcuparVaga(vagaPorId.value.get(id))
})

// ---------- exportar

// Exporta o organograma em imagens 4K (3840 × 2160, 16:9), no tema da tela.
// As medidas abaixo são de uma tela 1920 × 1080, dobradas na hora de gerar. Se o desenho inteiro cabe numa imagem com o texto legível (ao menos
// LEITURA_MINIMA do tamanho da tela), sai um arquivo só; senão, divide pelos
// galhos do primeiro nível abaixo do topo — o máximo que ainda fica legível
// em cada imagem — e cada imagem repete o topo.
const desenhoOrganograma = ref(null)
const exportandoOrganograma = ref(false)
const LARGURA_EXPORTACAO = 1920
const ALTURA_EXPORTACAO = 1080
const MARGEM_EXPORTACAO = 40
const TOPO_EXPORTACAO = 96
const LEITURA_MINIMA = 0.85
const ESCALA_SAIDA = 2

const ESPACO_L = LARGURA_EXPORTACAO - MARGEM_EXPORTACAO * 2
const ESPACO_A = ALTURA_EXPORTACAO - TOPO_EXPORTACAO - MARGEM_EXPORTACAO

const escalaDoDesenho = elemento =>
  Math.min(ESPACO_L / elemento.scrollWidth, ESPACO_A / elemento.scrollHeight)

// a linha de galhos que divide as páginas: os vários topos, ou os galhos
// logo abaixo do topo quando ele é um só
function linhaDosGalhos(elemento) {
  const topos = elemento.querySelector('.org-topos')
  if (topos && topos.children.length > 1) return topos
  return elemento.querySelector('.org-ramos')
}

// grupos de galhos por imagem; [null] = tudo numa imagem só
function paginasDoOrganograma(elemento) {
  const linha = linhaDosGalhos(elemento)
  const ramos = linha ? [...linha.children] : []
  if (ramos.length < 2 || escalaDoDesenho(elemento) >= LEITURA_MINIMA) return [null]

  const paginas = []
  let atual = []
  for (const ramo of ramos) {
    const tentativa = [...atual, ramo]
    mostrarSoEstes(linha, tentativa)
    if (atual.length && escalaDoDesenho(elemento) < LEITURA_MINIMA) {
      paginas.push(atual)
      atual = [ramo]
    } else {
      atual = tentativa
    }
  }
  paginas.push(atual)
  mostrarSoEstes(linha, null)
  return paginas
}

// esconde os outros galhos (e a linha horizontal que os ligaria); null = todos
function mostrarSoEstes(linha, ramos) {
  linha.classList.toggle('org-quebra', Boolean(ramos))
  for (const ramo of linha.children) {
    ramo.style.display = !ramos || ramos.includes(ramo) ? '' : 'none'
  }
}

function baixarImagem(tela, nome) {
  const link = document.createElement('a')
  link.download = nome
  link.href = tela.toDataURL('image/png')
  link.click()
}

async function desenharPagina(elemento, cores, legenda) {
  const largura = elemento.scrollWidth
  const altura = elemento.scrollHeight
  const escala = escalaDoDesenho(elemento) * ESCALA_SAIDA
  // nitidez: já desenha no tamanho final, sem ampliar nem reduzir depois
  const desenho = await toCanvas(elemento, {
    backgroundColor: cores.fundo,
    width: largura,
    height: altura,
    pixelRatio: escala
  })

  const tela = document.createElement('canvas')
  tela.width = LARGURA_EXPORTACAO * ESCALA_SAIDA
  tela.height = ALTURA_EXPORTACAO * ESCALA_SAIDA
  const ctx = tela.getContext('2d')
  ctx.fillStyle = cores.fundo
  ctx.fillRect(0, 0, tela.width, tela.height)
  ctx.scale(ESCALA_SAIDA, ESCALA_SAIDA)

  ctx.textBaseline = 'top'
  ctx.fillStyle = cores.titulo
  ctx.font = "700 36px 'Barlow Semi Condensed', 'Segoe UI', sans-serif"
  ctx.fillText(`Organograma · ${tituloOrganograma.value}`, MARGEM_EXPORTACAO, 28)
  ctx.fillStyle = cores.fraca
  ctx.font = "400 18px 'Inter', 'Segoe UI', sans-serif"
  ctx.textAlign = 'right'
  ctx.fillText(
    [legenda, new Date().toLocaleDateString('pt-BR')].filter(Boolean).join('   ·   '),
    LARGURA_EXPORTACAO - MARGEM_EXPORTACAO,
    40
  )

  ctx.setTransform(1, 0, 0, 1, 0, 0)
  const x = (tela.width - desenho.width) / 2
  const y = (TOPO_EXPORTACAO + (ESPACO_A - altura * escala / ESCALA_SAIDA) / 2) * ESCALA_SAIDA
  ctx.drawImage(desenho, Math.round(x), Math.round(y))
  return tela
}

async function exportarOrganograma() {
  const elemento = desenhoOrganograma.value
  if (!elemento) return
  exportandoOrganograma.value = true
  avisoOrganograma.value = { tipo: '', texto: '' }
  const linha = linhaDosGalhos(elemento)
  try {
    const estilo = getComputedStyle(document.body)
    const cores = {
      fundo: estilo.getPropertyValue('--superficie').trim() || '#ffffff',
      titulo: estilo.getPropertyValue('--titulo').trim() || '#4f1723',
      fraca: estilo.getPropertyValue('--tinta-fraca').trim() || '#6d5f63'
    }
    const nomeBase = `organograma-${tituloOrganograma.value.toLowerCase().replace(/[\s·,]+/g, '-')}`
    const paginas = paginasDoOrganograma(elemento)

    for (const [indice, ramos] of paginas.entries()) {
      if (ramos) mostrarSoEstes(linha, ramos)
      const legenda = paginas.length > 1 ? `Página ${indice + 1} de ${paginas.length}` : ''
      const tela = await desenharPagina(elemento, cores, legenda)
      baixarImagem(
        tela,
        paginas.length > 1 ? `${nomeBase}-${indice + 1}-de-${paginas.length}.png` : `${nomeBase}.png`
      )
    }
    if (paginas.length > 1) {
      avisoOrganograma.value = {
        tipo: 'ok',
        texto: `Organograma exportado em ${paginas.length} imagens para o texto ficar legível.`
      }
    }
  } catch (e) {
    avisoOrganograma.value = { tipo: 'erro', texto: 'Não foi possível exportar o organograma.' }
    console.error(e)
  } finally {
    if (linha) mostrarSoEstes(linha, null)
    exportandoOrganograma.value = false
  }
}

const indicadores = computed(() => [
  { chave: '', rotulo: 'Indiretos', icone: 'groups', valor: pessoas.value.length },
  {
    chave: 'alocados',
    rotulo: 'Alocados',
    icone: 'how_to_reg',
    valor: pessoas.value.filter(estaAlocado).length
  },
  {
    chave: 'semSetor',
    rotulo: 'Sem setor',
    icone: 'person_search',
    valor: pessoas.value.filter(p => !estaAlocado(p)).length
  },
  {
    chave: 'vagasVazias',
    rotulo: 'Vagas vazias',
    icone: 'event_seat',
    valor: vagas.value.filter(v => !ocupantePorVaga.value.has(v.id)).length
  },
  {
    chave: 'extras',
    rotulo: 'Extras',
    icone: 'person_add_alt',
    valor: alocados.value.filter(ehExtra).length
  },
  {
    chave: 'afastados',
    rotulo: 'Afastados',
    icone: 'event_busy',
    valor: pessoas.value.filter(p => p.afastado).length
  }
  // quem só consulta não vê a lista "Sem setor", então nem o indicador dela;
  // sem BID nenhum ainda, os de vagas não dizem nada
]
  .filter(indicador => podeEditar.value || indicador.chave !== 'semSetor')
  .filter(indicador => vagas.value.length || !['vagasVazias', 'extras'].includes(indicador.chave)))

function alternarStatus(chave) {
  filtroStatus.value = filtroStatus.value === chave ? '' : chave
}

// ============================================================
// RESPONSÁVEL: pesquisa (os dois diálogos usam)
// ============================================================

// o cadastro tem ~1.000 pessoas: só lista depois de 2 letras digitadas, e
// no máximo 50 opções, para o campo não travar
const termoResponsavel = ref('')

const opcoesResponsavelSelect = computed(() => {
  const termo = termoResponsavel.value.trim().toLowerCase()
  const selecionadas = [alocacao.responsavelChapa, trocaResponsavel.chapa, ocupar.responsavelChapa].filter(Boolean)
  const lista = termo.length < 2
    ? responsaveis.value.filter(r => selecionadas.includes(r.chapa))
    : responsaveis.value
      .filter(r => `${r.nome} ${r.chapa}`.toLowerCase().includes(termo))
      .slice(0, 50)
  return lista.map(r => ({ label: `${r.nome} (${r.chapa})`, value: r.chapa, ...r }))
})

function filtrarResponsaveis(termo, atualizar) {
  atualizar(() => {
    termoResponsavel.value = termo || ''
  })
}

// ============================================================
// ALOCAR / MOVER / ADICIONAR
// ============================================================

// modo 'pessoa': veio da pessoa (fixa; escolhe setor)
// modo 'setor': veio do botão do cartão (setor fixo; escolhe a pessoa)
const alocacao = reactive({
  aberto: false,
  modo: 'pessoa',
  chapa: null,
  setor: null,
  setorDigitado: '',
  base: null,
  basesGerente: [],
  responsavelChapa: null,
  funcao: null,
  subsetor: null,
  subsetorDigitado: '',
  observacao: '',
  // vaga do BID que ocupa (null = extra)
  vagaId: null
})
const salvando = ref(false)
const termoPessoa = ref('')
const termoSetor = ref('')

const pessoaAlocacao = computed(() => pessoas.value.find(p => p.chapa === alocacao.chapa))

const tituloAlocacao = computed(() => {
  if (alocacao.modo === 'setor') return `Adicionar em ${alocacao.setor}`
  return pessoaAlocacao.value?.alocacao ? 'Editar colaborador' : 'Alocar em um setor'
})

const opcoesPessoas = computed(() => {
  const termo = termoPessoa.value.toLowerCase()
  return pessoas.value
    .filter(p => !p.alocacao)
    .filter(p => !termo || `${p.nome} ${p.chapa}`.toLowerCase().includes(termo))
    .slice(0, 80)
    .map(p => ({ label: `${p.nome} (${p.chapa})`, value: p.chapa, nome: p.nome, funcao: p.funcao }))
})

function filtrarPessoas(termo, atualizar) {
  atualizar(() => {
    termoPessoa.value = termo || ''
  })
}

const opcoesSetorDialogo = computed(() => {
  const termo = termoSetor.value.toLowerCase()
  return nomesSetores.value.filter(nome => !termo || nome.toLowerCase().includes(termo))
})

function filtrarSetores(termo, atualizar) {
  atualizar(() => {
    termoSetor.value = termo || ''
  })
}

// o setor pode ter sido só digitado (sem Enter): vale o texto do campo
const setorEscolhido = computed(() =>
  String(alocacao.setor || alocacao.setorDigitado || '')
    .trim()
    .replace(/\s+/g, ' ')
    .toUpperCase()
)

const alocandoGerente = computed(() => setorEscolhido.value === SETOR_GERENCIA)

// subsetores que já existem no setor escolhido (pode digitar um novo)
const termoSubsetor = ref('')
const opcoesSubsetorDialogo = computed(() => {
  const termo = termoSubsetor.value.toLowerCase()
  const nomes = new Set(
    alocados.value
      .filter(p => p.alocacao.setor === setorEscolhido.value && p.alocacao.subsetor)
      .map(p => p.alocacao.subsetor)
  )
  return [...nomes]
    .sort((a, b) => a.localeCompare(b, 'pt-BR'))
    .filter(nome => !termo || nome.toLowerCase().includes(termo))
})

function filtrarSubsetores(termo, atualizar) {
  atualizar(() => {
    termoSubsetor.value = termo || ''
  })
}

// O texto do campo de subsetor É o valor: digitar um novo ou escolher da
// lista. Guardar só o texto à parte não basta — ao clicar fora do campo (no
// Salvar) o Quasar limpa o texto em edição e o subsetor ia vazio.
function digitarSubsetor(alvo, valor) {
  alvo.subsetorDigitado = valor || ''
  alvo.subsetor = valor || null
}

// campo vazio: mostra o que a pessoa herda do responsável escolhido
const dicaSubsetor = computed(() => {
  const chefe = alocadoPorChapa.value.get(alocacao.responsavelChapa)
  const herdado =
    chefe && chefe.alocacao.setor === setorEscolhido.value ? subsetorEfetivo(chefe) : ''
  if (herdado && !subsetorEscolhido.value) {
    return `Herdado de ${nomeCurto(chefe.nome)}: ${herdado}. Preencha só para usar outro.`
  }
  return ''
})

// como no setor: vale o texto digitado mesmo sem Enter
const subsetorEscolhido = computed(() =>
  String(alocacao.subsetor || alocacao.subsetorDigitado || '')
    .trim()
    .replace(/\s+/g, ' ')
    .toUpperCase()
)

const setorNovo = computed(
  () => Boolean(setorEscolhido.value) && !nomesSetores.value.includes(setorEscolhido.value)
)

// sugestão de responsável: o mais comum no setor + base escolhidos
watch(
  () => [setorEscolhido.value, alocacao.base],
  ([setor, base]) => {
    if (!setor || !base || alocacao.responsavelChapa) return
    const contagem = new Map()
    for (const p of alocados.value) {
      if (p.alocacao.setor === setor && p.alocacao.base === base && p.alocacao.responsavel_chapa) {
        const chapa = p.alocacao.responsavel_chapa
        contagem.set(chapa, (contagem.get(chapa) || 0) + 1)
      }
    }
    const [maisComum] = [...contagem.entries()].sort((a, b) => b[1] - a[1])
    if (maisComum) alocacao.responsavelChapa = maisComum[0]
  }
)

const alocacaoCompleta = computed(() =>
  Boolean(
    alocacao.chapa &&
      setorEscolhido.value &&
      (alocandoGerente.value || (alocacao.base && alocacao.responsavelChapa))
  )
)

function abrirAlocacao(pessoa) {
  termoResponsavel.value = ''
  termoSetor.value = ''
  opcoesFuncao.value = funcoes.value
  const atual = pessoa.alocacao
  Object.assign(alocacao, {
    aberto: true,
    modo: 'pessoa',
    chapa: pessoa.chapa,
    setor: atual?.setor || null,
    setorDigitado: '',
    base: atual?.base || null,
    basesGerente: [...(atual?.bases_responsavel || [])],
    responsavelChapa: atual?.responsavel_chapa || null,
    funcao: funcaoExibida(pessoa) || null,
    subsetor: atual?.subsetor || null,
    subsetorDigitado: '',
    observacao: atual?.observacao || '',
    vagaId: atual?.vaga_id || null
  })
}

function abrirAdicionarNoSetor(nomeSetor) {
  termoPessoa.value = ''
  termoResponsavel.value = ''
  opcoesFuncao.value = funcoes.value
  Object.assign(alocacao, {
    aberto: true,
    modo: 'setor',
    chapa: null,
    setor: nomeSetor,
    setorDigitado: '',
    base: null,
    basesGerente: [],
    responsavelChapa: null,
    funcao: null,
    subsetor: null,
    subsetorDigitado: '',
    observacao: '',
    vagaId: null
  })
}

async function confirmarAlocacao() {
  salvando.value = true
  erro.value = ''
  sucesso.value = ''
  try {
    await chamarApi(
      '/api/indiretos/alocar',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chapa: alocacao.chapa,
          setor: setorEscolhido.value,
          // gerente: a base dele é a que ele cuida (abaixo), não onde está
          base: alocandoGerente.value ? '' : alocacao.base,
          responsavel_chapa: alocacao.responsavelChapa,
          // vazio ou igual à do cadastro: o servidor volta a usar a do cadastro
          funcao: alocacao.funcao || '',
          subsetor: subsetorEscolhido.value,
          observacao: alocacao.observacao,
          vaga_id: setorEscolhidoTemBid.value ? alocacao.vagaId : null
        })
      },
      'Não foi possível alocar.'
    )
    if (alocandoGerente.value) {
      await chamarApi(
        '/api/indiretos/responsavel-base',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ chapa: alocacao.chapa, bases: alocacao.basesGerente || [] })
        },
        'Não foi possível salvar as bases do gerente.'
      )
    }
    const onde = alocandoGerente.value ? alocacao.basesGerente || [] : [alocacao.base]
    sucesso.value = `${pessoaAlocacao.value?.nome || 'Indireto'} salvo em ${[setorEscolhido.value, ...onde].join(' · ')}.`
    alocacao.aberto = false
    // aberto pela visão geral: o aviso da página ficaria atrás do organograma
    if (organograma.aberto) avisoOrganograma.value = { tipo: 'ok', texto: sucesso.value }
    await carregar()
  } catch (e) {
    erro.value = e.message
    if (organograma.aberto) avisoOrganograma.value = { tipo: 'erro', texto: e.message }
  } finally {
    salvando.value = false
  }
}

async function removerDoSetor(pessoa) {
  const { setor, base } = pessoa.alocacao
  if (
    !(await confirmar(`Tirar ${pessoa.nome} do setor ${setor} (${base})?`, {
      textoConfirmar: 'Tirar do setor'
    }))
  ) {
    return
  }
  erro.value = ''
  sucesso.value = ''
  try {
    await chamarApi(
      `/api/indiretos/alocacao/${encodeURIComponent(pessoa.chapa)}`,
      { method: 'DELETE' },
      'Não foi possível tirar do setor.'
    )
    sucesso.value = `${pessoa.nome} saiu de ${setor} · ${base}.`
    alocacao.aberto = false
    await carregar()
  } catch (e) {
    erro.value = e.message
  }
}

// ============================================================
// VAGAS DO SETOR (BID): quantidade por função e quem ocupa cada uma
// ============================================================

// linhas: a tabela do BID que se edita de uma vez ({ chave, atual, funcao,
// quantidade, ocupadas }); atual = nome de hoje ('' = função nova)
// aviso: mostrado dentro do diálogo (o banner da página fica atrás dele)
const vagasSetor = reactive({
  aberto: false,
  setor: '',
  linhas: [],
  salvando: false,
  aviso: { tipo: '', texto: '' }
})
const opcoesFuncaoVaga = ref([])
let proximaChaveLinha = 0

const funcoesDasVagas = computed(() => vagasDoSetorPorFuncao(vagasSetor.setor))
function linhaDaTabela(atual = '', quantidade = 1, ocupadas = 0) {
  return { chave: ++proximaChaveLinha, atual, funcao: atual || null, quantidade, ocupadas }
}

// a tabela parte do BID de hoje; setor sem BID começa com uma linha em branco
function montarLinhasDasVagas() {
  const linhas = funcoesDasVagas.value.map(f =>
    linhaDaTabela(f.funcao, f.vagas.length, f.vagas.filter(v => v.ocupante).length)
  )
  vagasSetor.linhas = linhas.length ? linhas : [linhaDaTabela()]
}

function abrirVagasDoSetor(setor) {
  opcoesFuncaoVaga.value = sugestoesDeCargo.value
  Object.assign(vagasSetor, { aberto: true, setor, salvando: false, aviso: { tipo: '', texto: '' } })
  montarLinhasDasVagas()
}

function adicionarLinhaDasVagas() {
  vagasSetor.linhas.push(linhaDaTabela())
}

// função que já existe vai a 0 (apaga as vagas vazias); linha nova sai da tabela
function removerLinhaDasVagas(linha) {
  if (linha.atual) linha.quantidade = 0
  else vagasSetor.linhas = vagasSetor.linhas.filter(l => l !== linha)
}

// Nome do cargo da vaga: sugere as funções do cadastro e as que já estão no
// BID, mas é texto livre (o BID pode usar um nome que o cadastro não tem)
const sugestoesDeCargo = computed(() =>
  [...new Set([...funcoes.value, ...vagas.value.map(v => v.funcao)])].sort((a, b) =>
    a.localeCompare(b, 'pt-BR')
  )
)

function cargoDigitado(valor) {
  return String(valor || '').trim().replace(/\s+/g, ' ').toUpperCase()
}

// primeiro os que começam com o texto, depois os que o contêm; a primeira
// já fica marcada (Enter completa com ela) e o texto continua editável
function filtrarFuncoesVaga(texto, atualizar) {
  atualizar(
    () => {
      const termo = normalizarTexto(texto)
      if (!termo) {
        opcoesFuncaoVaga.value = sugestoesDeCargo.value
        return
      }
      const comecam = []
      const contem = []
      for (const funcao of sugestoesDeCargo.value) {
        const nome = normalizarTexto(funcao)
        if (nome.startsWith(termo)) comecam.push(funcao)
        else if (nome.includes(termo)) contem.push(funcao)
      }
      opcoesFuncaoVaga.value = [...comecam, ...contem]
    },
    campo => {
      if (texto && campo.options.length) {
        campo.setOptionIndex(-1)
        campo.moveOptionSelection(1, true)
      }
    }
  )
}

// linhas que vão para o servidor: as em branco (sem cargo) de função nova são ignoradas
const linhasParaSalvar = computed(() =>
  vagasSetor.linhas
    .filter(l => l.atual || cargoDigitado(l.funcao))
    .map(l => ({ atual: l.atual, funcao: cargoDigitado(l.funcao), quantidade: Number(l.quantidade) }))
)

const problemaDasVagas = computed(() => {
  const linhas = linhasParaSalvar.value
  if (linhas.some(l => !l.funcao)) return 'Preencha o nome do cargo de todas as linhas.'
  if (linhas.some(l => !Number.isInteger(l.quantidade) || l.quantidade < 0)) {
    return 'A quantidade precisa ser um número inteiro (0 apaga as vagas).'
  }
  const nomes = linhas.filter(l => l.quantidade > 0 || l.atual).map(l => l.funcao)
  const repetido = nomes.find((n, i) => nomes.indexOf(n) !== i)
  if (repetido) return `${repetido} aparece em mais de uma linha: junte numa só.`
  return ''
})

const vagasMudaram = computed(() => {
  const hoje = new Map(funcoesDasVagas.value.map(f => [f.funcao, f.vagas.length]))
  const ordemDeHoje = funcoesDasVagas.value.map(f => f.funcao).join('|')
  const ordemDaTabela = vagasSetor.linhas.filter(l => l.atual).map(l => l.atual).join('|')
  return (
    ordemDaTabela !== ordemDeHoje ||
    linhasParaSalvar.value.some(
      l => !l.atual || l.funcao !== l.atual || l.quantidade !== hoje.get(l.atual)
    )
  )
})

// ---------- arrastar o cargo para cima ou para baixo (ordem do BID)
const linhaArrastada = ref(null)
const linhaAlvo = ref(null)

function iniciarArrasteDaLinha(evento, linha) {
  linhaArrastada.value = linha
  evento.dataTransfer.effectAllowed = 'move'
  evento.dataTransfer.setData('text/plain', linha.funcao || '')
}

function sobreLinha(evento, linha) {
  if (!linhaArrastada.value || linhaArrastada.value === linha) return
  evento.preventDefault()
  evento.dataTransfer.dropEffect = 'move'
  linhaAlvo.value = linha
}

function soltarNaLinha(linha) {
  const origem = linhaArrastada.value
  linhaArrastada.value = null
  linhaAlvo.value = null
  if (!origem || origem === linha) return
  const lista = vagasSetor.linhas.filter(l => l !== origem)
  const destino = vagasSetor.linhas.indexOf(linha) > vagasSetor.linhas.indexOf(origem)
    ? lista.indexOf(linha) + 1
    : lista.indexOf(linha)
  lista.splice(destino, 0, origem)
  vagasSetor.linhas = lista
}

function encerrarArrasteDaLinha() {
  linhaArrastada.value = null
  linhaAlvo.value = null
}

const totalDaTabela = computed(() =>
  linhasParaSalvar.value.reduce((soma, l) => soma + (l.quantidade > 0 ? l.quantidade : 0), 0)
)

async function salvarDefinicaoDasVagas() {
  // função nova com 0 vagas não precisa ir
  const linhas = linhasParaSalvar.value.filter(l => l.atual || l.quantidade > 0)
  if (!linhas.length || problemaDasVagas.value) return
  if (
    await salvarNasVagas(
      '/api/indiretos/vagas/definir',
      { setor: vagasSetor.setor, linhas },
      `${vagasSetor.setor}: BID salvo, ${totalDaTabela.value} ${totalDaTabela.value === 1 ? 'vaga' : 'vagas'}.`
    )
  ) {
    montarLinhasDasVagas()
  }
}

async function salvarNasVagas(url, corpo, mensagem) {
  vagasSetor.salvando = true
  vagasSetor.aviso = { tipo: '', texto: '' }
  try {
    await chamarApi(
      url,
      { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corpo) },
      'Não foi possível salvar as vagas.'
    )
    vagasSetor.aviso = { tipo: 'ok', texto: mensagem }
    await carregar()
    return true
  } catch (e) {
    vagasSetor.aviso = { tipo: 'erro', texto: e.message }
    return false
  } finally {
    vagasSetor.salvando = false
  }
}

// ---------- linhas do cartão do setor (como o BID)

function peloNome(a, b) {
  return a.nome.localeCompare(b.nome, 'pt-BR')
}

// Cada base com uma cor fixa (a paleta das disciplinas, que já se ajusta ao
// modo escuro): a mesma base tem a mesma cor em todos os setores
const CORES_DAS_BASES = {
  BCB: 'var(--tipo-p8)',
  BDC: 'var(--tipo-p1)',
  ITM: 'var(--tipo-p3)',
  PDS: 'var(--tipo-p4)',
  PDT: 'var(--tipo-p5)',
  STI: 'var(--tipo-p2)',
  'SPOT STI': 'var(--tipo-p9)'
}
const CORES_DE_SOBRA = ['var(--tipo-p6)', 'var(--tipo-p7)', 'var(--tipo-p10)']
// gerente sem base (indiretos.py: BASE_GERENCIA) fica neutro
const BASE_GERAL = 'GERAL'

function corDaBase(base) {
  if (!base || base === BASE_GERAL) return null
  if (CORES_DAS_BASES[base]) return CORES_DAS_BASES[base]
  const soma = [...base].reduce((total, letra) => total + letra.charCodeAt(0), 0)
  return CORES_DE_SOBRA[soma % CORES_DE_SOBRA.length]
}

// vagas vazias do setor (sem olhar os filtros)
function vagasVaziasDoSetor(setor) {
  return vagas.value.filter(v => v.setor === setor && !ocupantePorVaga.value.has(v.id))
}

// Uma linha por vaga, na ordem do BID (com quem ocupa, ou vazia), e no fim os
// extras. Só entra quem passou nos filtros da página; vaga vazia some com os
// filtros que só pessoas têm. Setor sem BID: as pessoas pelo nome.
function linhasDoCartao(grupo) {
  const pessoasDoGrupo = grupo.bases.flatMap(b => b.responsaveis.flatMap(t => t.pessoas))
  if (!setoresComBid.value.has(grupo.nome)) {
    return pessoasDoGrupo
      .slice()
      .sort(peloNome)
      .map(pessoa => ({ chave: pessoa.chapa, pessoa, vaga: null, extra: false }))
  }
  const visiveis = new Set(pessoasDoGrupo.map(p => p.chapa))
  const comVazias = vagasVaziasNoCartao(grupo.nome).length > 0
  const linhas = []
  for (const vaga of vagas.value.filter(v => v.setor === grupo.nome)) {
    const ocupante = ocupantePorVaga.value.get(vaga.id)
    if (ocupante ? visiveis.has(ocupante.chapa) : comVazias) {
      linhas.push({ chave: `vaga-${vaga.id}`, pessoa: ocupante || null, vaga, extra: false })
    }
  }
  for (const pessoa of pessoasDoGrupo.filter(p => !vagaDe(p)).sort(peloNome)) {
    linhas.push({ chave: pessoa.chapa, pessoa, vaga: null, extra: true })
  }
  return linhas
}

// ============================================================
// OCUPAR VAGA (na linha do cartão)
// ============================================================
//
// modo 'vaga': clicou "Ocupar" numa vaga vazia e escolhe a pessoa (extras do
// setor primeiro, depois quem está sem setor e, por último, de outro setor).
// Quem não é do setor é alocado nele na hora: pede só base e responsável.
// modo 'pessoa': clicou "Pôr na vaga" num extra e escolhe a vaga vazia.

const ocupar = reactive({
  aberto: false,
  modo: 'vaga',
  setor: '',
  vaga: null,
  pessoa: null,
  chapa: null,
  vagaId: null,
  base: null,
  responsavelChapa: null,
  salvando: false,
  erro: ''
})
const termoOcupante = ref('')

function abrirOcuparVaga(vaga) {
  termoOcupante.value = ''
  termoResponsavel.value = ''
  Object.assign(ocupar, {
    aberto: true,
    modo: 'vaga',
    setor: vaga.setor,
    vaga,
    pessoa: null,
    chapa: null,
    vagaId: vaga.id,
    base: null,
    responsavelChapa: null,
    salvando: false,
    erro: ''
  })
}

function abrirPorNaVaga(pessoa) {
  const setor = pessoa.alocacao.setor
  const vazias = vagasVaziasDoSetor(setor)
  // sugere a vaga da mesma função da pessoa, se houver
  const mesma = vazias.find(v => normalizarTexto(v.funcao) === normalizarTexto(funcaoExibida(pessoa)))
  Object.assign(ocupar, {
    aberto: true,
    modo: 'pessoa',
    setor,
    vaga: null,
    pessoa,
    chapa: pessoa.chapa,
    vagaId: (mesma || vazias[0] || {}).id || null,
    base: null,
    responsavelChapa: null,
    salvando: false,
    erro: ''
  })
}

// modo 'pessoa': uma opção por função com vaga vazia, na ordem do BID
// (vagas da mesma função são iguais: vale a primeira)
const opcoesVagaParaOcupar = computed(() => {
  const porFuncao = new Map()
  for (const vaga of vagasVaziasDoSetor(ocupar.setor)) {
    if (!porFuncao.has(vaga.funcao)) porFuncao.set(vaga.funcao, [])
    porFuncao.get(vaga.funcao).push(vaga)
  }
  return [...porFuncao.entries()].map(([funcao, lista]) => ({
    label: `${funcao} · ${lista.length} ${lista.length === 1 ? 'vaga vazia' : 'vagas vazias'}`,
    value: lista[0].id
  }))
})

// modo 'vaga': quem pode ocupar
const opcoesOcupar = computed(() => {
  const termo = normalizarTexto(termoOcupante.value)
  const casa = p => !termo || normalizarTexto(`${p.nome} ${p.chapa} ${funcaoExibida(p)}`).includes(termo)
  const extras = alocados.value
    .filter(p => p.alocacao.setor === ocupar.setor && !vagaDe(p))
    .filter(casa)
    .sort(peloNome)
    .map(p => ({ value: p.chapa, label: p.nome, caption: `${funcaoExibida(p)} · extra no setor`, grupo: 'extra' }))
  const semSetor = pessoas.value
    .filter(p => !p.alocacao)
    .filter(casa)
    .sort(peloNome)
    .map(p => ({ value: p.chapa, label: p.nome, caption: `${p.funcao || 'sem função'} · sem setor`, grupo: 'livre' }))
  const outros = alocados.value
    .filter(p => p.alocacao.setor !== ocupar.setor)
    .filter(casa)
    .sort(peloNome)
    .map(p => ({
      value: p.chapa,
      label: p.nome,
      caption: `${funcaoExibida(p)} · hoje em ${p.alocacao.setor}`,
      grupo: 'outro'
    }))
  // de outro setor só depois de digitar (são muitos)
  return [...extras, ...semSetor, ...(termo.length >= 2 ? outros.slice(0, 40) : [])]
})

function filtrarOcupantes(termo, atualizar) {
  atualizar(() => {
    termoOcupante.value = termo || ''
  })
}

const pessoaParaOcupar = computed(() =>
  ocupar.modo === 'pessoa' ? ocupar.pessoa : pessoas.value.find(p => p.chapa === ocupar.chapa) || null
)
// quem não está no setor da vaga é alocado nele junto (precisa de base e responsável)
const ocuparAlocaNoSetor = computed(
  () => Boolean(pessoaParaOcupar.value && pessoaParaOcupar.value.alocacao?.setor !== ocupar.setor)
)
const ocuparNaGerencia = computed(() => ocupar.setor === SETOR_GERENCIA)

// escolheu alguém de fora: sugere a base e o responsável mais comuns do setor
watch(
  () => ocupar.chapa,
  () => {
    if (!ocupar.aberto || ocupar.modo !== 'vaga' || !ocuparAlocaNoSetor.value) return
    const doSetor = alocados.value.filter(p => p.alocacao.setor === ocupar.setor)
    const maisComum = valores => {
      const contagem = new Map()
      for (const v of valores.filter(Boolean)) contagem.set(v, (contagem.get(v) || 0) + 1)
      return [...contagem.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || null
    }
    // a vaga posicionada no organograma já diz a base e o chefe
    ocupar.base = ocupar.vaga?.base || maisComum(doSetor.map(p => p.alocacao.base))
    ocupar.responsavelChapa =
      ocupar.vaga?.responsavel_chapa ||
      maisComum(doSetor.filter(p => p.alocacao.base === ocupar.base).map(p => p.alocacao.responsavel_chapa))
  }
)

const ocuparCompleto = computed(() => {
  if (!ocupar.chapa || !ocupar.vagaId) return false
  if (!ocuparAlocaNoSetor.value || ocuparNaGerencia.value) return true
  return Boolean(ocupar.base && ocupar.responsavelChapa)
})

async function confirmarOcupar() {
  const pessoa = pessoaParaOcupar.value
  const vaga = vagaPorId.value.get(ocupar.vagaId)
  if (!pessoa || !vaga) return
  ocupar.salvando = true
  ocupar.erro = ''
  try {
    if (ocuparAlocaNoSetor.value) {
      await chamarApi(
        '/api/indiretos/alocar',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chapa: pessoa.chapa,
            setor: ocupar.setor,
            base: ocuparNaGerencia.value ? '' : ocupar.base,
            responsavel_chapa: ocupar.responsavelChapa,
            vaga_id: vaga.id
          })
        },
        'Não foi possível alocar na vaga.'
      )
    } else {
      await chamarApi(
        '/api/indiretos/vagas/ocupar',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ vaga_id: vaga.id, chapa: pessoa.chapa })
        },
        'Não foi possível ocupar a vaga.'
      )
    }
    sucesso.value = `${pessoa.nome} agora ocupa a vaga de ${vaga.funcao} em ${ocupar.setor}.`
    erro.value = ''
    ocupar.aberto = false
    await carregar()
  } catch (e) {
    ocupar.erro = e.message
  } finally {
    ocupar.salvando = false
  }
}

// organograma: vagas arrastadas ficam abaixo de alguém e/ou numa base; na
// caixa "Vagas vazias", saem da cadeia
async function posicionarVagas(origem, alvo) {
  let corpo
  let mensagem
  const quantas = origem.vagaIds.length === 1 ? 'A vaga' : `As ${origem.vagaIds.length} vagas`
  if (alvo.limparVagas) {
    corpo = {}
    mensagem = `${quantas} de ${origem.cargo} ${origem.vagaIds.length === 1 ? 'saiu' : 'saíram'} da cadeia.`
  } else {
    const chefe = alvo.grupo ? alvo.chefe : alvo.chapa
    const nomeDoChefe = alvo.grupo ? alvo.chefeNome : alvo.nome
    const base = alvo.base || alocadoPorChapa.value.get(chefe)?.alocacao.base || ''
    if (alvo.externo) {
      avisoOrganograma.value = { tipo: 'erro', texto: `${nomeDoChefe} está fora deste setor.` }
      return
    }
    corpo = { base, responsavel_chapa: chefe || '' }
    const verbo = origem.vagaIds.length === 1 ? 'fica' : 'ficam'
    mensagem = `${quantas} de ${origem.cargo} agora ${verbo}${chefe ? ` abaixo de ${nomeDoChefe}` : ''}${base ? ` em ${base}` : ''}.`
  }
  salvandoOrganograma.value = true
  avisoOrganograma.value = { tipo: '', texto: '' }
  try {
    await chamarApi(
      '/api/indiretos/vagas/posicao',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vaga_ids: origem.vagaIds, ...corpo })
      },
      'Não foi possível posicionar a vaga.'
    )
    avisoOrganograma.value = { tipo: 'ok', texto: mensagem }
    await carregar()
  } catch (e) {
    avisoOrganograma.value = { tipo: 'erro', texto: e.message }
  } finally {
    salvandoOrganograma.value = false
  }
}

// organograma: pessoa solta numa vaga vazia passa a ocupá-la
async function soltarNaVaga(origem, alvo) {
  if (origem.chapas) {
    avisoOrganograma.value = { tipo: 'erro', texto: 'Arraste uma pessoa por vez para a vaga.' }
    return
  }
  salvandoOrganograma.value = true
  avisoOrganograma.value = { tipo: '', texto: '' }
  try {
    await chamarApi(
      '/api/indiretos/vagas/ocupar',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vaga_id: alvo.vagaIds[0], chapa: origem.chapa })
      },
      'Não foi possível ocupar a vaga.'
    )
    avisoOrganograma.value = { tipo: 'ok', texto: `${origem.nome} agora ocupa a vaga de ${alvo.cargo}.` }
    await carregar()
  } catch (e) {
    avisoOrganograma.value = { tipo: 'erro', texto: e.message }
  } finally {
    salvandoOrganograma.value = false
  }
}

// ---------- vaga no diálogo de alocar

// vagas do setor escolhido que a pessoa pode ocupar: as vazias e a dela
const opcoesVagaDialogo = computed(() => {
  const lista = vagas.value
    .filter(v => v.setor === setorEscolhido.value)
    .filter(v => {
      const ocupante = ocupantePorVaga.value.get(v.id)
      return !ocupante || ocupante.chapa === alocacao.chapa
    })
  // várias vagas vazias da mesma função: basta uma opção por função
  const vistas = new Set()
  const opcoes = []
  for (const vaga of lista) {
    const dela = ocupantePorVaga.value.get(vaga.id)?.chapa === alocacao.chapa
    if (!dela && vistas.has(vaga.funcao)) continue
    if (!dela) vistas.add(vaga.funcao)
    const vazias = lista.filter(v => v.funcao === vaga.funcao && !ocupantePorVaga.value.has(v.id)).length
    opcoes.push({
      label: vaga.funcao,
      value: vaga.id,
      caption: dela ? 'vaga atual' : `${vazias} ${vazias === 1 ? 'vazia' : 'vazias'}`
    })
  }
  return [{ label: 'Sem vaga (extra)', value: null, caption: 'fica como extra no setor' }, ...opcoes]
})
const setorEscolhidoTemBid = computed(() => setoresComBid.value.has(setorEscolhido.value))

// trocou o setor (ou a pessoa): se a vaga escolhida não é do setor, sugere
// uma vaga vazia da mesma função da pessoa
watch(
  () => [setorEscolhido.value, alocacao.chapa],
  () => {
    if (!alocacao.aberto) return
    const atual = vagaPorId.value.get(alocacao.vagaId)
    if (atual && atual.setor === setorEscolhido.value) return
    const pessoa = pessoaAlocacao.value
    // continua no setor de hoje: fica como está (extra continua extra)
    if (pessoa?.alocacao && pessoa.alocacao.setor === setorEscolhido.value) {
      alocacao.vagaId = pessoa.alocacao.vaga_id || null
      return
    }
    const funcao = normalizarTexto(alocacao.funcao || (pessoa ? funcaoExibida(pessoa) : ''))
    const sugerida = opcoesVagaDialogo.value.find(
      o => o.value && normalizarTexto(o.label) === funcao && o.caption !== 'vaga atual'
    )
    alocacao.vagaId = sugerida ? sugerida.value : null
  }
)

// ============================================================
// FUNÇÃO NA PÁGINA (só a mostrada aqui; o cadastro não muda)
// ============================================================

// A função escolhida na página, se houver; senão, a do cadastro
function funcaoExibida(pessoa) {
  return pessoa.alocacao?.funcao || pessoa.funcao || ''
}

const opcoesFuncao = ref([])

// Sugere enquanto digita: primeiro as funções que COMEÇAM com o texto, depois
// as que o contêm; a primeira já fica marcada, e Enter completa com ela.
function filtrarFuncoes(texto, atualizar) {
  atualizar(
    () => {
      const termo = normalizarTexto(texto)
      if (!termo) {
        opcoesFuncao.value = funcoes.value
        return
      }
      const comecam = []
      const contem = []
      for (const funcao of funcoes.value) {
        const nome = normalizarTexto(funcao)
        if (nome.startsWith(termo)) comecam.push(funcao)
        else if (nome.includes(termo)) contem.push(funcao)
      }
      opcoesFuncao.value = [...comecam, ...contem]
    },
    campo => {
      if (texto && campo.options.length) {
        campo.setOptionIndex(-1)
        campo.moveOptionSelection(1, true)
      }
    }
  )
}

// ============================================================
// TROCAR RESPONSÁVEL (pessoa ou grupo)
// ============================================================

const trocaResponsavel = reactive({
  aberto: false,
  pessoas: [],
  responsavelAtual: null,
  chapa: null
})

function abrirTrocaResponsavel(grupo) {
  termoResponsavel.value = ''
  Object.assign(trocaResponsavel, {
    aberto: true,
    // troca só quem responde DIRETO a ele: quem está abaixo de um
    // sub-responsável (ex.: equipe do Rikelme) continua com o seu chefe
    pessoas: grupo.chapa
      ? grupo.pessoas.filter(p => p.alocacao.responsavel_chapa === grupo.chapa)
      : grupo.pessoas,
    responsavelAtual: grupo.responsavel || null,
    chapa: grupo.responsavel?.chapa || null
  })
}

async function salvarResponsavel() {
  salvando.value = true
  erro.value = ''
  sucesso.value = ''
  try {
    const dados = await chamarApi(
      '/api/indiretos/responsavel',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chapas: trocaResponsavel.pessoas.map(p => p.chapa),
          responsavel_chapa: trocaResponsavel.chapa
        })
      },
      'Não foi possível trocar o responsável.'
    )
    const novo = responsavelPorChapa(trocaResponsavel.chapa)
    sucesso.value = `Responsável de ${dados.alteradas} ${dados.alteradas === 1 ? 'pessoa' : 'pessoas'} agora é ${novo?.nome || trocaResponsavel.chapa}.`
    trocaResponsavel.aberto = false
    await carregar()
  } catch (e) {
    erro.value = e.message
  } finally {
    salvando.value = false
  }
}

// ============================================================
// PLANILHA: baixar / analisar / aplicar
// ============================================================

const baixando = ref(false)
const planilha = reactive({
  aberto: false,
  arquivo: null,
  previa: null,
  analisando: false,
  aplicando: false
})

function abrirPlanilha() {
  Object.assign(planilha, { aberto: true, arquivo: null, previa: null })
}

function baixarPlanilha() {
  return baixarArquivo('/api/indiretos/planilha', 'alocacao-indiretos.xlsx')
}

async function baixarArquivo(endereco, nome) {
  baixando.value = true
  erro.value = ''
  try {
    const resposta = await fetch(endereco)
    if (!resposta.ok) {
      const dados = await resposta.json().catch(() => ({}))
      throw new Error(dados.erro || 'Erro ao gerar a planilha.')
    }
    const url = URL.createObjectURL(await resposta.blob())
    const link = document.createElement('a')
    link.href = url
    link.download = nome
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    erro.value = e.message || 'Erro ao gerar a planilha.'
  } finally {
    baixando.value = false
  }
}

function corpoArquivo() {
  const corpo = new FormData()
  corpo.append('arquivo', planilha.arquivo)
  return corpo
}

async function analisarPlanilha() {
  planilha.analisando = true
  erro.value = ''
  try {
    planilha.previa = await chamarApi(
      '/api/indiretos/planilha/previa',
      { method: 'POST', body: corpoArquivo() },
      'Erro ao analisar a planilha.'
    )
  } catch (e) {
    planilha.previa = null
    erro.value = e.message
    planilha.aberto = false
  } finally {
    planilha.analisando = false
  }
}

const mudancasPrevia = computed(() => {
  const p = planilha.previa
  if (!p) return []
  return [
    ...p.alocar.map(i => ({
      ...i, tipo: 'a', icone: 'person_add', cor: 'positive',
      texto: `alocar em ${i.setor} · ${i.base} · responsável ${i.responsavel_nome}`
    })),
    ...p.mover.map(i => ({
      ...i, tipo: 'm', icone: 'swap_horiz', cor: 'primary',
      texto: `de ${i.de} para ${i.setor} · ${i.base} · responsável ${i.responsavel_nome}`
    })),
    ...p.atualizar.map(i => ({
      ...i, tipo: 'u', icone: 'edit', cor: 'warning',
      texto: (i.mudancas || []).join(' · ')
    }))
  ]
})

const podeAplicar = computed(
  () =>
    Boolean(planilha.previa && !planilha.previa.erros.length) &&
    Boolean(mudancasPrevia.value.length || planilha.previa.vagas?.length)
)

async function aplicarPlanilha() {
  planilha.aplicando = true
  erro.value = ''
  sucesso.value = ''
  try {
    const r = await chamarApi(
      '/api/indiretos/planilha/aplicar',
      { method: 'POST', body: corpoArquivo() },
      'Erro ao aplicar a planilha.'
    )
    const bid = r.vagas?.length
      ? `; BID de ${r.vagas.length} ${r.vagas.length === 1 ? 'setor atualizado' : 'setores atualizados'}`
      : ''
    sucesso.value = `Planilha aplicada: ${r.alocados} alocados, ${r.movidos} movidos, ${r.atualizados} atualizados${bid}.`
    planilha.aberto = false
    await carregar()
  } catch (e) {
    erro.value = e.message
    planilha.aberto = false
  } finally {
    planilha.aplicando = false
  }
}

function textoPreviaVagas(item) {
  const partes = [
    item.antes === item.depois ? `${item.depois} vagas` : `vagas: ${item.antes} → ${item.depois}`,
    item.criadas ? `${item.criadas} ${item.criadas === 1 ? 'nova' : 'novas'}` : '',
    item.removidas ? `${item.removidas} ${item.removidas === 1 ? 'apagada' : 'apagadas'}` : '',
    `${item.ocupadas} ${item.ocupadas === 1 ? 'ocupada' : 'ocupadas'}`,
    item.vazias ? `${item.vazias} ${item.vazias === 1 ? 'vazia' : 'vazias'}` : '',
    item.extras ? `${item.extras} ${item.extras === 1 ? 'extra' : 'extras'}` : ''
  ]
  return partes.filter(Boolean).join(' · ')
}
</script>

<style scoped>
.aviso-previa {
  border: 1px dashed var(--linha-forte);
}

/* ---------- indicadores ---------- */
.indicador {
  border-radius: 14px;
  transition: transform 0.14s ease, box-shadow 0.14s ease, border-color 0.14s ease;
}

.indicador:hover {
  transform: translateY(-2px);
}

.indicador--ativo {
  border-color: var(--marca-clara);
  box-shadow: 0 0 0 2px var(--marca-clara), var(--sombra);
}

.indicador__icone {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--realce);
  color: var(--marca-texto);
}

.indicador--alocados .indicador__icone {
  background: var(--positivo-fundo);
  color: var(--positivo);
}

.indicador--semSetor .indicador__icone {
  background: var(--folguista-fundo);
  color: var(--folguista);
}

.indicador--afastados .indicador__icone {
  background: var(--afastado-fundo);
  color: var(--afastado);
}

.indicador__valor {
  font-family: var(--fonte-ui);
  font-size: 1.9rem;
  font-weight: 700;
  line-height: 1;
  color: var(--titulo);
  font-variant-numeric: tabular-nums;
}

.indicador__rotulo {
  font-family: var(--fonte-ui);
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--tinta-fraca);
}

/* ---------- cartão do setor ---------- */
.cartao-organograma {
  max-height: 92vh;
  display: flex;
  flex-direction: column;
}

.area-organograma {
  flex: 1;
  overflow: auto;
}

.org-legenda {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px 16px;
  padding: 6px 14px;
  border: 1px solid var(--linha);
  border-radius: 999px;
  background: var(--superficie);
  font-family: var(--fonte-ui);
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  color: var(--tinta);
}

.org-legenda__item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.org-legenda__cor {
  width: 14px;
  height: 14px;
  border-radius: 4px;
  border: 2px solid var(--sub-borda);
  background: var(--sub-fundo);
}

body.body--dark .org-legenda__cor {
  border-color: var(--sub-borda-escura);
  background: var(--sub-fundo-escuro);
}

.org-legenda__cor--geral {
  border-color: var(--marca);
  background: var(--superficie);
}

/* nível mais alto do organograma: clicar volta para a visão geral */
.org-navegacao {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: max-content;
  min-width: 100%;
}

.org-voltar {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border: 0;
  border-radius: 12px;
  background: var(--gradiente-marca);
  color: #fff;
  font-family: var(--fonte-ui);
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  white-space: nowrap;
  cursor: pointer;
  box-shadow: var(--sombra);
  transition: transform 0.14s ease, box-shadow 0.14s ease;
}

.org-voltar:hover {
  transform: translateY(-1px);
  box-shadow: var(--sombra-elevada);
}

.org-voltar__linha {
  width: 2px;
  height: 14px;
  background: #c9a7ae;
}

:global(.body--dark) .org-voltar__linha {
  background: #6e5a5e;
}

/* setor no topo e as bases como primeiro nível de galhos */
.org-raizes {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
  min-width: max-content;
  padding: 8px;
}

/* vários topos (responsáveis sem chefe comum no setor) lado a lado */
.org-topos {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: 40px;
}

/* exportação em várias imagens (só alguns galhos visíveis): sem a linha
   horizontal que ligaria galhos escondidos */
.org-raizes :deep(.org-quebra > .org-ramo)::after {
  display: none;
}

.dica-arraste {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  font-size: 0.8rem;
  color: var(--tinta-fraca);
}


.mural-setores {
  column-count: 1;
  column-gap: 16px;
}

@media (min-width: 1024px) {
  .mural-setores {
    column-count: 2;
  }
}

.mural-setores__item {
  break-inside: avoid;
  margin-bottom: 16px;
}

.cartao-setor {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.cartao-setor__faixa {
  height: 4px;
  background: linear-gradient(90deg, var(--marca) 0%, var(--marca-clara) 60%, transparent 100%);
}

.cartao-setor__nome {
  font-family: var(--fonte-ui);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--titulo);
}

.cartao-setor__contagem {
  text-align: center;
  min-width: 64px;
  padding: 6px 10px;
  border-radius: 12px;
  background: var(--superficie-2);
  border: 1px solid var(--linha);
}

.cartao-setor__numero {
  font-family: var(--fonte-ui);
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1;
  color: var(--marca-texto);
}

.cartao-setor__legenda {
  font-size: 0.7rem;
  color: var(--tinta-fraca);
}

.secoes-base {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 12px 4px;
}

.secao-base {
  border: 1px solid var(--linha);
  border-radius: 10px;
  overflow: hidden;
}

.secao-base__cabecalho {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: var(--superficie-2);
  border-bottom: 1px solid var(--linha);
}

.chip-base {
  background: var(--marca);
  color: #fff;
  font-family: var(--fonte-ui);
  font-weight: 700;
  letter-spacing: 0.04em;
}

.chip-base :deep(.q-icon) {
  color: #fff;
}

.secao-base__cabecalho--sub {
  padding-left: 18px;
  border-top: 1px solid var(--linha);
}

.secao-chapa {
  min-width: 64px;
}

.chapa-pessoa {
  font-family: var(--fonte-ui);
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--marca-texto);
  font-variant-numeric: tabular-nums;
}

.funcao-pessoa {
  max-width: 260px;
  margin-right: 4px;
  padding: 2px 8px;
  border-radius: 6px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  background: var(--realce);
  font-family: var(--fonte-ui);
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--marca-texto);
  text-transform: uppercase;
}

.lista-previa {
  max-height: 280px;
  overflow-y: auto;
}

.responsavel-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border: 1px solid var(--linha);
  border-radius: 999px;
  background: var(--superficie);
  color: var(--tinta);
  font: inherit;
  cursor: pointer;
  transition: border-color 0.14s ease, box-shadow 0.14s ease;
}

.responsavel-chip:not(:disabled):hover,
.responsavel-chip:not(:disabled):focus-visible {
  border-color: var(--linha-forte);
  box-shadow: 0 0 0 3px rgba(113, 20, 36, 0.1);
  outline: none;
}

/* só consulta (quem não é Administrador): o chip é informativo */
.responsavel-chip:disabled {
  cursor: default;
  color: var(--tinta);
}

.responsavel-chip__texto {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
  text-align: left;
  font-size: 0.95rem;
}

/* nomes um pouco menores que o padrão da lista, para harmonizar com as etiquetas */
/* nomes nos cartões de setor; a lista "Sem setor" fica mais compacta */
.lista-pessoas .text-weight-medium {
  font-size: 1.1rem;
}

.lista-sem-setor .text-weight-medium {
  font-size: 0.82rem;
}

/* "Sem setor" estreita em telas largas: o espaço vai para os setores */
@media (min-width: 1440px) {
  .coluna-setores {
    width: 80%;
  }

  .coluna-sem-setor {
    width: 20%;
  }
}

.responsavel-chip__texto small {
  color: var(--tinta-fraca);
  font-size: 0.76rem;
}

.responsavel-chip__editar {
  color: var(--tinta-fraca);
}

.avatar-responsavel {
  background: var(--marca);
  color: #fff;
  font-family: var(--fonte-ui);
  font-weight: 700;
  font-size: 0.7rem;
}

.pessoa-fixa {
  display: flex;
  align-items: center;
  padding: 8px 10px;
  border-radius: 10px;
  background: var(--superficie-2);
  border: 1px solid var(--linha);
}

.texto-medio {
  font-size: 1.05rem;
}

.tabela-modelo thead tr {
  background: var(--gradiente-marca);
}

.tabela-modelo th {
  background: transparent;
  color: #fff;
  font-family: var(--fonte-ui);
  font-weight: 600;
  font-size: 0.72rem;
  letter-spacing: 0.06em;
}

.secao-base__responsavel {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--tinta);
}

.secao-base__responsavel .q-icon {
  color: var(--marca-texto);
}

.sem-responsavel {
  color: var(--tinta-fraca);
  font-style: italic;
}

.secao-base__contagem {
  font-family: var(--fonte-ui);
  font-weight: 700;
  color: var(--marca-texto);
  font-variant-numeric: tabular-nums;
}

.responsavel {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 10px;
  background: var(--superficie-2);
  color: var(--tinta);
}

.responsavel .q-icon {
  color: var(--marca-texto);
}

.responsavel__rotulo {
  color: var(--tinta-fraca);
}

.lista-pessoas {
  flex: 1;
}

.avatar-pessoa {
  background: var(--realce);
  color: var(--marca-texto);
  font-family: var(--fonte-ui);
  font-weight: 700;
  font-size: 0.8rem;
}

.linha-afastado {
  background: var(--afastado-fundo);
}

/* ---------- faixa de indicadores (item 4) ---------- */
.faixa-indicadores {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px 18px;
  padding: 10px 16px;
  border: 1px solid var(--linha);
  border-radius: var(--raio);
  background: var(--superficie);
}

.faixa-indicadores__item {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  padding: 2px 0;
  border: 0;
  border-bottom: 2px solid transparent;
  background: none;
  font: inherit;
  color: var(--tinta);
  cursor: pointer;
}

.faixa-indicadores__valor {
  font-size: 1.15rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.faixa-indicadores__rotulo {
  font-size: 0.85rem;
  color: var(--tinta-fraca);
}

.faixa-indicadores__item:hover .faixa-indicadores__rotulo {
  color: var(--tinta);
}

.faixa-indicadores__item--ativo {
  border-bottom-color: var(--marca-clara);
}

.faixa-indicadores__item--vagasVazias .faixa-indicadores__valor {
  color: var(--vaga-vazia);
}

.faixa-indicadores__item--extras .faixa-indicadores__valor {
  color: var(--folguista);
}

/* ---------- lista do cartão do setor: limpa, sem pílulas ---------- */
.linha-bid {
  min-height: 38px;
  padding: 2px 10px 2px 13px;
  border-left: 3px solid transparent;
  transition: background-color 0.12s ease;
}

.linha-bid + .linha-bid {
  border-top: 1px solid var(--linha);
}

.linha-bid:hover {
  background: color-mix(in srgb, var(--marca-clara) 6%, transparent);
}

.lista-bid .secao-chapa {
  min-width: 52px;
  padding-right: 6px;
}

.lista-bid .chapa-pessoa {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--marca-texto);
}

.lista-bid .bid-pessoa {
  color: var(--marca-texto);
  font-weight: 700;
  opacity: 0.85;
}

/* base: cor própria de cada base (ver corDaBase) */
.lista-bid .base-pessoa {
  min-width: 52px;
  margin-right: 10px;
  border: 1px solid color-mix(in srgb, var(--cor-base, var(--tinta-fraca)) 45%, transparent);
  background: color-mix(in srgb, var(--cor-base, var(--tinta-fraca)) 13%, transparent);
  color: var(--cor-base, var(--tinta-fraca));
  font-weight: 700;
}

.lista-bid .base-pessoa--vazia {
  border-color: transparent;
}

.nome-pessoa {
  font-weight: 600;
  color: var(--titulo);
}

.funcao-real {
  max-width: 220px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 0.74rem;
  color: var(--tinta-fraca);
}

.marca-extra,
.marca-afastado {
  margin-right: 8px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.marca-extra {
  color: var(--folguista);
}

.marca-afastado {
  color: var(--afastado);
}

.linha-bid__direita {
  gap: 4px;
}

/* editar só aparece ao passar o mouse (no toque, sempre) */
.linha-bid__editar {
  opacity: 0;
  transition: opacity 0.12s ease;
}

.linha-bid:hover .linha-bid__editar,
.linha-bid__editar:focus-visible {
  opacity: 1;
}

@media (hover: none) {
  .linha-bid__editar {
    opacity: 1;
  }
}

/* vaga vazia (azul) e extra (laranja): fundo suave e filete à esquerda */
.lista-bid .linha-vaga-vazia {
  border-left-color: var(--vaga-vazia);
}

.lista-bid .linha-extra {
  border-left-color: var(--folguista);
}

.texto-extra {
  font-weight: 600;
  color: var(--folguista);
}

.texto-secundario {
  font-weight: 400;
  color: var(--tinta-fraca);
}

.texto-afastado {
  font-weight: 400;
  color: var(--afastado);
}

.acao-texto {
  padding: 2px 4px;
  border: 0;
  background: none;
  font: inherit;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--marca-texto);
  cursor: pointer;
}

.acao-texto:hover {
  text-decoration: underline;
}

/* ---------- vagas do BID ---------- */
.indicador--vagasVazias .indicador__icone {
  background: var(--vaga-vazia-fundo);
  color: var(--vaga-vazia);
}

.indicador--extras .indicador__icone {
  background: var(--folguista-fundo);
  color: var(--folguista);
}

.resumo-vagas {
  display: inline-block;
  margin-top: 2px;
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  font-size: 0.75rem;
  color: var(--tinta-fraca);
  white-space: nowrap;
  cursor: pointer;
}

.resumo-vagas:not(:disabled):hover {
  color: var(--marca-texto);
  text-decoration: underline;
}

.resumo-vagas:disabled {
  cursor: default;
}

.resumo-vagas--sem-bid {
  border-style: dashed;
  background: transparent;
  color: var(--tinta-fraca);
  border-color: var(--linha-forte);
}

.chip-extra {
  background: var(--folguista-fundo);
  color: var(--folguista);
  font-weight: 600;
}

.vagas-dialogo {
  max-height: 62vh;
  overflow-y: auto;
}

.vagas-secao__titulo {
  margin-bottom: 6px;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--titulo);
}

.vagas-tabela__cabecalho,
.vagas-tabela__linha {
  display: flex;
  align-items: center;
  gap: 8px;
}

.vagas-tabela__cabecalho {
  padding: 0 2px 4px;
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--tinta-fraca);
  text-transform: uppercase;
}

.vagas-tabela__linha + .vagas-tabela__linha {
  margin-top: 6px;
}

.vagas-tabela__alca {
  width: 22px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--tinta-fraca);
  cursor: grab;
}

.vagas-tabela__alca:active {
  cursor: grabbing;
}

.vagas-tabela__linha--arrastando {
  opacity: 0.45;
}

/* onde a linha vai entrar */
.vagas-tabela__linha--alvo {
  box-shadow: 0 -2px 0 var(--marca-clara);
  border-radius: 4px;
}

.vagas-tabela__linha--apagar {
  opacity: 0.55;
  text-decoration: line-through;
}

.vagas-tabela__qtd {
  width: 84px;
  flex: none;
}

.vagas-tabela__ocupadas {
  width: 70px;
  flex: none;
  text-align: center;
  color: var(--tinta-fraca);
}

.vagas-tabela__acao {
  width: 32px;
  flex: none;
}

.tabela-ocupacao__cargo {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--titulo);
  white-space: nowrap;
}

.tabela-ocupacao__nome {
  min-width: 210px;
}

.tabela-ocupacao__funcao {
  white-space: normal;
  font-size: 0.75rem;
  color: var(--tinta-fraca);
}

/* cadeira vazia: tons de azul; extra: fundo laranja (claro e escuro pelos tokens) */
.linha-vaga-vazia,
.linha-vaga-vazia td {
  background: var(--vaga-vazia-fundo);
}

.linha-vaga-vazia :deep(.q-field__native),
.texto-vaga-vazia {
  color: var(--vaga-vazia);
  font-style: italic;
}

.linha-extra,
.linha-extra td {
  background: var(--folguista-fundo);
}

.chip-vaga-vazia {
  background: var(--vaga-vazia);
  color: #fff;
  font-weight: 600;
}

:global(.body--dark) .chip-vaga-vazia {
  color: #10202f;
}

.chapa-pessoa--vazia {
  color: var(--vaga-vazia);
}

/* base: só uma informação da linha (antes agrupava as pessoas) */
.base-pessoa {
  display: inline-block;
  flex: none;
  min-width: 58px;
  margin-right: 8px;
  padding: 0 6px;
  text-align: center;
  white-space: nowrap;
  border-radius: 999px;
  background: var(--realce);
  color: var(--marca-texto);
  font-size: 0.66rem;
  font-weight: 700;
}

.base-pessoa--vazia {
  background: transparent;
  color: var(--tinta-fraca);
}

.nome-pessoa {
  min-width: 0;
}

/* coluna do BID no cartão: o cargo previsto da vaga (vazio = extra) */
.secao-bid {
  width: 116px;
  min-width: 116px;
  padding-right: 6px;
  align-items: flex-start;
}

/* até duas linhas: o nome da pessoa fica com o espaço maior */
.bid-pessoa {
  display: -webkit-box;
  width: 100%;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.15;
  white-space: normal;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--vaga-vazia);
}

.tabela-ocupacao__grupos th {
  font-weight: 800;
  letter-spacing: 0.08em;
}

.tabela-ocupacao__grupo-bid {
  background: var(--vaga-vazia-fundo);
  color: var(--vaga-vazia);
}

.tabela-ocupacao__grupo-real {
  background: var(--realce);
  color: var(--marca-texto);
}

/* ---------- sem setor ---------- */
.cartao-sem-setor {
  position: sticky;
  top: 74px;
}

.lista-sem-setor {
  max-height: 70vh;
  overflow-y: auto;
}

.estado-vazio {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 40px 0;
  color: var(--tinta-fraca);
}

@media (prefers-reduced-motion: reduce) {
  .indicador {
    transition: none;
  }

  .indicador:hover {
    transform: none;
  }
}
</style>
