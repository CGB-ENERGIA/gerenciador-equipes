<template>
  <q-layout view="lHh Lpr lFf">
    <MarcaDaguaFundo />

    <CabecalhoApp
      titulo="Cadastro de Vagas"
      :carregando="carregando"
      @atualizar="carregarEquipes"
    />

    <q-page-container>
      <q-page class="q-pa-md">
        <div class="q-mb-md">
          <div class="text-h5"> Cadastro de Vagas </div>

          <div class="text-subtitle2 text-grey-7">
            Equipes, quantas vagas de cada função elas têm e quem responde por cada tipo de equipe
          </div>
        </div>

        <q-banner v-if="erro" class="bg-red-1 text-negative q-mb-md" rounded>
          {{ erro }}
        </q-banner>

        <q-banner
          v-if="sucesso"
          class="bg-green-1 text-positive q-mb-md"
          rounded
        >
          {{ sucesso }}
        </q-banner>

        <div class="row q-col-gutter-md items-start">
          <!-- ================================================== -->
          <!-- LISTA DE EQUIPES -->
          <!-- ================================================== -->

          <div class="col-12 col-md-5">
            <q-card bordered>
              <q-card-section class="q-gutter-y-sm">
                <div class="row items-center q-gutter-sm no-wrap">
                  <q-input
                    v-model="filtroEquipe"
                    outlined
                    dense
                    clearable
                    class="col"
                    placeholder="Buscar prefixo ou base"
                  >
                    <template #prepend>
                      <q-icon name="search" />
                    </template>
                  </q-input>

                  <q-btn-dropdown
                    outline
                    dense
                    no-caps
                    color="primary"
                    icon="table_view"
                    label="Planilha"
                  >
                    <q-list dense>
                      <q-item v-close-popup clickable :disable="baixandoPlanilha" @click="baixarPlanilha">
                        <q-item-section avatar><q-icon name="download" /></q-item-section>
                        <q-item-section>
                          <q-item-label>Baixar planilha</q-item-label>
                          <q-item-label caption>Equipes de hoje, com a quantidade de cada função</q-item-label>
                        </q-item-section>
                      </q-item>
                      <q-item v-close-popup clickable @click="dialogEnvioPlanilha = true">
                        <q-item-section avatar><q-icon name="upload_file" /></q-item-section>
                        <q-item-section>
                          <q-item-label>Enviar planilha preenchida</q-item-label>
                          <q-item-label caption>Cria, edita ou exclui várias equipes de uma vez</q-item-label>
                        </q-item-section>
                      </q-item>
                    </q-list>
                  </q-btn-dropdown>

                  <q-btn
                    unelevated
                    dense
                    no-caps
                    color="primary"
                    icon="add"
                    label="Nova equipe"
                    class="q-px-sm"
                    @click="iniciarNovaEquipe"
                  />
                </div>

                <div class="row q-col-gutter-sm">
                  <div class="col-12 col-sm-4">
                    <q-select
                      :model-value="baseFiltro"
                      outlined
                      dense
                      clearable
                      multiple
                      use-chips
                      emit-value
                      map-options
                      label="Base"
                      :options="opcoesBaseFiltro"
                      @update:model-value="atualizarSelecaoBaseFiltro"
                    />
                  </div>
                  <div class="col-6 col-sm-4">
                    <q-select
                      v-model="tipoFiltro"
                      outlined
                      dense
                      emit-value
                      map-options
                      label="Tipo de equipe"
                      :options="opcoesTipos"
                    />
                  </div>
                  <div class="col-6 col-sm-4">
                    <q-select
                      v-model="setorFiltro"
                      outlined
                      dense
                      emit-value
                      map-options
                      label="Setor"
                      :options="opcoesSetores"
                    />
                  </div>
                  <div class="col-12 col-sm-6">
                    <SelectFiltroMultiplo
                      :model-value="coordenadorFiltro"
                      :options="opcoesCoordenadores"
                      icon="badge"
                      label="Coordenador"
                      @update:model-value="selecao => (coordenadorFiltro = proximaSelecaoMultipla(coordenadorFiltro, selecao, RESPONSAVEL_TODOS))"
                    />
                  </div>
                  <div class="col-12 col-sm-6">
                    <SelectFiltroMultiplo
                      :model-value="supervisorFiltro"
                      :options="opcoesSupervisores"
                      icon="engineering"
                      label="Supervisor"
                      @update:model-value="selecao => (supervisorFiltro = proximaSelecaoMultipla(supervisorFiltro, selecao, RESPONSAVEL_TODOS))"
                    />
                  </div>
                </div>
              </q-card-section>

              <q-separator />

              <div v-if="selecionadas.length" class="barra-selecao row items-center no-wrap q-px-md q-py-xs">
                <span class="text-weight-medium">{{ selecionadas.length }} selecionada(s)</span>
                <q-space />
                <q-btn
                  flat
                  dense
                  no-caps
                  color="primary"
                  icon="edit"
                  label="Editar setor e responsáveis"
                  @click="abrirEdicaoSelecionadas"
                />
                <q-btn flat dense round icon="close" aria-label="Limpar seleção" @click="selecionadas = []" />
              </div>

              <div class="row items-center no-wrap q-px-sm q-py-xs text-caption text-grey-7">
                <q-checkbox
                  dense
                  size="sm"
                  :model-value="estadoMarcarTodas"
                  aria-label="Selecionar todas as equipes da lista"
                  @update:model-value="marcarTodasFiltradas"
                />
                <span class="q-ml-sm">
                  {{ equipesFiltradas.length }} equipe(s)
                  <template v-if="equipesComVagaLivre">
                    · <span class="text-negative">{{ equipesComVagaLivre }} com vaga livre</span>
                  </template>
                </span>
              </div>

              <q-separator />

              <div v-if="carregando && primeiraCarga" class="row justify-center q-pa-xl">
                <q-spinner color="primary" size="40px" />
              </div>

              <div v-else-if="!equipesFiltradas.length" class="text-grey-7 q-pa-lg text-center">
                Nenhuma equipe encontrada com esses filtros.
              </div>

              <q-virtual-scroll
                v-else
                class="lista-equipes"
                :items="equipesFiltradas"
                separator
                v-slot="{ item: equipe }"
              >
                <q-item
                  :key="equipe.id"
                  clickable
                  :active="painel.equipeId === equipe.id"
                  active-class="item-ativo"
                  @click="abrirEquipe(equipe)"
                >
                  <q-item-section side class="q-pr-sm">
                    <q-checkbox
                      dense
                      size="sm"
                      :model-value="selecionadas.includes(equipe.id)"
                      :aria-label="`Selecionar ${equipe.prefixo}`"
                      @click.stop
                      @update:model-value="alternarSelecao(equipe.id)"
                    />
                  </q-item-section>

                  <q-item-section>
                    <q-item-label class="text-weight-medium">{{ equipe.prefixo || 'Equipe' }}</q-item-label>
                    <q-item-label caption>
                      {{ equipe.base }}<template v-if="(equipe.setores || []).length"> · {{ equipe.setores.join(', ') }}</template>
                    </q-item-label>
                    <q-item-label caption class="ellipsis">{{ (equipe.tipos || []).join(', ') }}</q-item-label>
                  </q-item-section>

                  <q-item-section side top class="text-right">
                    <span
                      class="contagem-vagas"
                      :class="contagemDaEquipe(equipe).livres ? 'text-negative' : 'text-grey-9'"
                    >
                      {{ contagemDaEquipe(equipe).ocupadas }} de {{ contagemDaEquipe(equipe).total }}
                    </span>
                    <q-item-label caption>ocupadas</q-item-label>
                  </q-item-section>
                </q-item>
              </q-virtual-scroll>
            </q-card>
          </div>

          <!-- ================================================== -->
          <!-- PAINEL DA EQUIPE -->
          <!-- ================================================== -->

          <div class="col-12 col-md-7">
            <q-card bordered class="painel-equipe">
              <!-- nada aberto -->
              <q-card-section v-if="!painel.modo" class="column items-center text-center q-pa-xl text-grey-7">
                <q-icon name="groups" size="48px" color="grey-5" />
                <div class="q-mt-sm">Escolha uma equipe na lista para ver e mudar as vagas dela.</div>
                <q-btn
                  outline
                  no-caps
                  color="primary"
                  icon="add"
                  label="Nova equipe"
                  class="q-mt-md"
                  @click="iniciarNovaEquipe"
                />
              </q-card-section>

              <!-- nova equipe, passo 1: base e prefixo -->
              <template v-else-if="painel.modo === 'nova' && painel.passo === 1">
                <q-card-section>
                  <div class="text-overline text-grey-7">Nova equipe · passo 1 de 2</div>
                  <div class="text-h6">Identificação</div>
                  <div class="text-caption text-grey-7">
                    A base e o prefixo identificam a equipe. No próximo passo, você define as vagas e os responsáveis.
                  </div>
                </q-card-section>

                <q-card-section class="q-gutter-md">
                  <q-select
                    v-model="painel.base"
                    outlined
                    dense
                    use-input
                    fill-input
                    hide-selected
                    input-debounce="0"
                    new-value-mode="add-unique"
                    label="Base"
                    hint="Escolha uma base existente ou digite uma nova"
                    :error="Boolean(erroBase) && painelTocado"
                    :error-message="erroBase"
                    :options="basesFiltradas"
                    @filter="filtrarBases"
                    @input-value="valor => (painel.base = valor)"
                  />

                  <q-input
                    v-model="painel.prefixo"
                    outlined
                    dense
                    label="Prefixo"
                    hint="Ex.: MA-BCB-O007M ou FOLGUISTA"
                    :error="Boolean(erroPrefixo) && painelTocado"
                    :error-message="erroPrefixo"
                    @keyup.enter="avancarParaVagas"
                  />
                </q-card-section>

                <q-separator />

                <q-card-actions align="right">
                  <q-btn flat no-caps color="grey-8" label="Cancelar" @click="fecharPainel" />
                  <q-btn
                    unelevated
                    no-caps
                    color="primary"
                    icon-right="arrow_forward"
                    label="Continuar"
                    @click="avancarParaVagas"
                  />
                </q-card-actions>
              </template>

              <!-- nova equipe (passo 2) ou equipe existente -->
              <template v-else>
                <q-card-section class="q-pb-sm">
                  <div v-if="painel.modo === 'nova'" class="row items-start no-wrap">
                    <div class="col">
                      <div class="text-overline text-grey-7">Nova equipe · passo 2 de 2</div>
                      <div class="text-h6">{{ painel.prefixo }}</div>
                      <div class="text-caption text-grey-7">Base {{ painel.base }}</div>
                    </div>
                    <q-btn flat dense no-caps color="primary" icon="arrow_back" label="Voltar" @click="painel.passo = 1" />
                  </div>

                  <template v-else>
                    <div class="row q-col-gutter-sm">
                      <div class="col-12 col-sm-5">
                        <q-select
                          v-model="painel.base"
                          outlined
                          dense
                          use-input
                          fill-input
                          hide-selected
                          input-debounce="0"
                          new-value-mode="add-unique"
                          label="Base"
                          :options="basesFiltradas"
                          @filter="filtrarBases"
                          @input-value="valor => (painel.base = valor)"
                        />
                      </div>
                      <div class="col-12 col-sm-7">
                        <q-input v-model="painel.prefixo" outlined dense label="Prefixo" />
                      </div>
                    </div>
                    <div class="text-caption text-grey-7 q-mt-sm">
                      {{ resumoPainel.ocupadas }} de {{ resumoPainel.total }} vagas ocupadas
                      <template v-if="painel.extras">
                        · {{ painel.extras }} Folguista Extra, gerido no Banco de Dados
                      </template>
                    </div>
                  </template>
                </q-card-section>

                <q-card-section class="q-pt-none q-gutter-y-md">
                  <div class="text-subtitle2">Vagas por tipo de equipe</div>

                  <div
                    v-for="(disciplina, indice) in painel.disciplinas"
                    :key="disciplina.chave"
                    class="bloco-disciplina"
                  >
                    <div class="row items-center no-wrap q-gutter-sm">
                      <q-select
                        v-model="disciplina.tipo"
                        outlined
                        dense
                        use-input
                        fill-input
                        hide-selected
                        input-debounce="0"
                        new-value-mode="add-unique"
                        label="Tipo de equipe"
                        class="col"
                        :options="estruturasFiltradas"
                        @filter="filtrarEstruturas"
                        @input-value="valor => (disciplina.tipo = (valor || '').toUpperCase())"
                      />
                      <q-btn
                        flat
                        dense
                        round
                        color="grey-7"
                        icon="delete_outline"
                        :aria-label="`Tirar o tipo ${disciplina.tipo || ''}`"
                        @click="removerDisciplina(indice)"
                      >
                        <q-tooltip>Tirar este tipo de equipe e as vagas dele</q-tooltip>
                      </q-btn>
                    </div>

                    <div class="row q-col-gutter-sm q-mt-xs">
                      <div class="col-12 col-sm-4">
                        <q-select
                          v-model="disciplina.setor"
                          outlined
                          dense
                          clearable
                          label="Setor"
                          :options="setoresNegocio"
                        />
                      </div>
                      <div class="col-12 col-sm-4">
                        <q-select
                          v-model="disciplina.supervisor"
                          outlined
                          dense
                          clearable
                          use-input
                          fill-input
                          hide-selected
                          input-debounce="0"
                          label="Supervisor"
                          :options="contasFiltradas"
                          :hint="semConta('SUPERVISOR', disciplina.supervisor) ? 'Nome antigo, sem conta no sistema: escolha a conta' : ''"
                          @filter="(termo, atualizar) => filtrarContas('SUPERVISOR', termo, atualizar)"
                        />
                      </div>
                      <div class="col-12 col-sm-4">
                        <q-select
                          v-model="disciplina.coordenador"
                          outlined
                          dense
                          clearable
                          use-input
                          fill-input
                          hide-selected
                          input-debounce="0"
                          label="Coordenador"
                          :options="contasFiltradas"
                          :hint="semConta('COORDENADOR', disciplina.coordenador) ? 'Nome antigo, sem conta no sistema: escolha a conta' : ''"
                          @filter="(termo, atualizar) => filtrarContas('COORDENADOR', termo, atualizar)"
                        />
                      </div>
                    </div>

                    <div class="q-mt-sm">
                      <div
                        v-for="(linha, i) in disciplina.funcoes"
                        :key="linha.chave"
                        class="linha-funcao row items-center no-wrap q-gutter-sm"
                      >
                        <q-select
                          v-model="linha.funcao"
                          outlined
                          dense
                          use-input
                          fill-input
                          hide-selected
                          input-debounce="0"
                          new-value-mode="add-unique"
                          label="Função"
                          class="col"
                          :options="funcoesFiltradas"
                          @filter="filtrarFuncoes"
                          @input-value="valor => (linha.funcao = (valor || '').toUpperCase())"
                        />

                        <div class="contador row items-center no-wrap">
                          <q-btn
                            flat
                            dense
                            round
                            icon="remove"
                            :disable="!linha.quantidade"
                            :aria-label="`Uma vaga a menos de ${linha.funcao || 'função'}`"
                            @click="linha.quantidade = Math.max(0, (linha.quantidade || 0) - 1)"
                          />
                          <q-input
                            v-model.number="linha.quantidade"
                            dense
                            outlined
                            type="number"
                            min="0"
                            input-class="text-center"
                            class="campo-quantidade"
                            :aria-label="`Vagas de ${linha.funcao || 'função'}`"
                          />
                          <q-btn
                            flat
                            dense
                            round
                            icon="add"
                            :aria-label="`Uma vaga a mais de ${linha.funcao || 'função'}`"
                            @click="linha.quantidade = (linha.quantidade || 0) + 1"
                          />
                        </div>

                        <div class="info-ocupadas text-caption" :class="(linha.quantidade || 0) < linha.ocupadas ? 'text-negative' : 'text-grey-7'">
                          <template v-if="(linha.quantidade || 0) < linha.ocupadas">
                            tira {{ linha.ocupadas - (linha.quantidade || 0) }} pessoa(s)
                          </template>
                          <template v-else-if="linha.ocupadas">
                            {{ linha.ocupadas }} ocupada(s)
                          </template>
                          <template v-else>livre</template>
                        </div>

                        <q-btn
                          flat
                          dense
                          round
                          size="sm"
                          color="grey-7"
                          icon="close"
                          :aria-label="`Tirar a função ${linha.funcao || ''}`"
                          @click="removerFuncao(disciplina, i)"
                        />
                      </div>

                      <q-btn
                        flat
                        dense
                        no-caps
                        color="primary"
                        icon="add"
                        label="Adicionar função"
                        class="q-mt-xs"
                        @click="adicionarFuncao(disciplina)"
                      />
                    </div>
                  </div>

                  <q-btn
                    outline
                    dense
                    no-caps
                    color="primary"
                    icon="add"
                    label="Adicionar outro tipo de equipe"
                    @click="adicionarDisciplina"
                  />

                  <div v-if="problemaVagas && painelTocado" class="text-negative text-caption">
                    {{ problemaVagas }}
                  </div>
                </q-card-section>

                <q-separator />

                <q-card-actions class="q-px-md">
                  <q-btn
                    v-if="painel.modo === 'editar'"
                    flat
                    dense
                    no-caps
                    color="negative"
                    icon="delete"
                    label="Excluir equipe"
                    :disable="resumoPainel.ocupadas > 0"
                    @click="removerEquipeAberta"
                  >
                    <q-tooltip v-if="resumoPainel.ocupadas > 0">
                      Tire as pessoas da equipe no Banco de Dados antes de excluir
                    </q-tooltip>
                  </q-btn>
                  <q-space />
                  <q-btn flat no-caps color="grey-8" label="Cancelar" @click="fecharPainel" />
                  <q-btn
                    unelevated
                    no-caps
                    color="primary"
                    :label="painel.modo === 'nova' ? 'Criar equipe' : 'Salvar'"
                    :loading="salvandoPainel"
                    @click="salvarPainel"
                  />
                </q-card-actions>
              </template>
            </q-card>
          </div>
        </div>
      </q-page>
    </q-page-container>

    <!-- ==================================================== -->
    <!-- EDITAR SETOR E RESPONSÁVEIS DAS SELECIONADAS -->
    <!-- ==================================================== -->

    <q-dialog v-model="dialogSelecionadas">
      <q-card style="width: 460px; max-width: 92vw">
        <q-card-section>
          <div class="text-h6">Setor e responsáveis</div>
          <div class="text-caption text-grey-7">
            Vale para todos os tipos de equipe das {{ selecionadas.length }} equipe(s) selecionada(s).
            Campo em branco não muda nada.
          </div>
        </q-card-section>

        <q-card-section class="q-gutter-md q-pt-none">
          <q-select v-model="massa.setor" outlined dense clearable label="Setor" :options="setoresNegocio" />
          <q-select
            v-model="massa.supervisor"
            outlined
            dense
            clearable
            use-input
            fill-input
            hide-selected
            input-debounce="0"
            label="Supervisor"
            :options="contasFiltradas"
            :hint="semConta('SUPERVISOR', massa.supervisor) ? 'Nome antigo, sem conta no sistema: escolha a conta' : ''"
            @filter="(termo, atualizar) => filtrarContas('SUPERVISOR', termo, atualizar)"
          />
          <q-select
            v-model="massa.coordenador"
            outlined
            dense
            clearable
            use-input
            fill-input
            hide-selected
            input-debounce="0"
            label="Coordenador"
            :options="contasFiltradas"
            :hint="semConta('COORDENADOR', massa.coordenador) ? 'Nome antigo, sem conta no sistema: escolha a conta' : ''"
            @filter="(termo, atualizar) => filtrarContas('COORDENADOR', termo, atualizar)"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn v-close-popup flat no-caps color="grey-8" label="Cancelar" />
          <q-btn
            unelevated
            no-caps
            color="primary"
            label="Aplicar"
            :loading="salvandoMassa"
            @click="aplicarEdicaoSelecionadas"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ==================================================== -->
    <!-- ENVIAR PLANILHA -->
    <!-- ==================================================== -->

    <q-dialog v-model="dialogEnvioPlanilha">
      <q-card style="width: 460px; max-width: 92vw">
        <q-card-section>
          <div class="text-h6">Enviar planilha preenchida</div>
          <div class="text-caption text-grey-7">
            Use a planilha baixada aqui. Na coluna AÇÃO, escreva <strong>criar</strong>,
            <strong>editar</strong> ou <strong>excluir</strong>; linha sem ação é ignorada.
            Nada é gravado antes de você conferir.
          </div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <q-file
            v-model="arquivoPlanilha"
            outlined
            dense
            clearable
            accept=".xlsx"
            label="Planilha (.xlsx)"
          >
            <template #prepend>
              <q-icon name="attach_file" />
            </template>
          </q-file>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn v-close-popup flat no-caps color="grey-8" label="Cancelar" />
          <q-btn
            unelevated
            no-caps
            color="primary"
            icon="fact_check"
            label="Conferir mudanças"
            :disable="!arquivoPlanilha"
            :loading="analisandoPlanilha"
            @click="analisarPlanilha"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ==================================================== -->
    <!-- PRÉVIA DA PLANILHA -->
    <!-- ==================================================== -->

    <q-dialog v-model="dialogPlanilha">
      <q-card style="min-width: 560px; max-width: 90vw">
        <q-card-section>
          <div class="text-h6"> Conferir mudanças </div>
          <div class="text-caption text-grey-7">
            Nada foi gravado ainda. Confira e confirme.
          </div>
        </q-card-section>

        <q-separator />

        <q-card-section style="max-height: 60vh" class="scroll">
          <div v-if="planoPlanilha" class="q-gutter-md">
            <div class="row q-gutter-sm">
              <q-chip
                :color="planoPlanilha.criar.length ? 'positive' : 'grey-5'"
                text-color="white"
              >
                {{ planoPlanilha.criar.length }} a criar
              </q-chip>
              <q-chip
                :color="planoPlanilha.editar.length ? 'primary' : 'grey-5'"
                text-color="white"
              >
                {{ planoPlanilha.editar.length }} a editar
              </q-chip>
              <q-chip
                :color="planoPlanilha.excluir.length ? 'negative' : 'grey-5'"
                text-color="white"
              >
                {{ planoPlanilha.excluir.length }} a excluir
              </q-chip>
              <q-chip
                :color="planoPlanilha.erros.length ? 'negative' : 'grey-5'"
                text-color="white"
              >
                {{ planoPlanilha.erros.length }} com erro
              </q-chip>
              <q-chip color="grey-6" text-color="white">
                {{ planoPlanilha.ignoradas }} sem alteração
              </q-chip>
            </div>

            <q-banner
              v-if="planoPlanilha.erros.length"
              class="bg-red-1 text-negative"
              rounded
            >
              Corrija as linhas com erro antes de aplicar. Nada será gravado
              enquanto houver erro.
            </q-banner>

            <div v-if="planoPlanilha.erros.length">
              <div class="text-subtitle2 text-negative q-mb-xs"> Erros </div>
              <q-markup-table flat dense bordered separator="horizontal" class="tabela-detalhe">
                <thead>
                  <tr>
                    <th class="text-left col-ordenavel" @click="ordenarErrosPlanilha('linha')">
                      Linha
                      <q-icon
                        v-if="ordenacaoErrosPlanilha.coluna === 'linha'"
                        :name="ordenacaoErrosPlanilha.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                        size="14px"
                        class="q-ml-xs"
                      />
                    </th>
                    <th class="text-left col-ordenavel" @click="ordenarErrosPlanilha('equipe')">
                      Equipe
                      <q-icon
                        v-if="ordenacaoErrosPlanilha.coluna === 'equipe'"
                        :name="ordenacaoErrosPlanilha.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                        size="14px"
                        class="q-ml-xs"
                      />
                    </th>
                    <th class="text-left col-ordenavel" @click="ordenarErrosPlanilha('erro')">
                      Erro
                      <q-icon
                        v-if="ordenacaoErrosPlanilha.coluna === 'erro'"
                        :name="ordenacaoErrosPlanilha.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                        size="14px"
                        class="q-ml-xs"
                      />
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="e in errosPlanilhaOrdenados" :key="'e' + e.linha">
                    <td>{{ e.linha }}</td>
                    <td>{{ e.equipe }}</td>
                    <td class="text-negative">{{ e.erro }}</td>
                  </tr>
                </tbody>
              </q-markup-table>
            </div>

            <div v-if="planoPlanilha.criar.length">
              <div class="text-subtitle2 q-mb-xs"> Criar </div>
              <q-markup-table flat dense bordered separator="horizontal" class="tabela-detalhe">
                <thead>
                  <tr>
                    <th class="text-left col-ordenavel" @click="ordenarCriarPlanilha('linha')">
                      Linha
                      <q-icon
                        v-if="ordenacaoCriarPlanilha.coluna === 'linha'"
                        :name="ordenacaoCriarPlanilha.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                        size="14px"
                        class="q-ml-xs"
                      />
                    </th>
                    <th class="text-left col-ordenavel" @click="ordenarCriarPlanilha('equipe')">
                      Equipe
                      <q-icon
                        v-if="ordenacaoCriarPlanilha.coluna === 'equipe'"
                        :name="ordenacaoCriarPlanilha.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                        size="14px"
                        class="q-ml-xs"
                      />
                    </th>
                    <th class="text-left col-ordenavel" @click="ordenarCriarPlanilha('total')">
                      Vagas
                      <q-icon
                        v-if="ordenacaoCriarPlanilha.coluna === 'total'"
                        :name="ordenacaoCriarPlanilha.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                        size="14px"
                        class="q-ml-xs"
                      />
                    </th>
                    <th class="text-left">Detalhe</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="i in criarPlanilhaOrdenados" :key="'c' + i.linha">
                    <td>{{ i.linha }}</td>
                    <td>
                      {{ i.equipe }}
                      <q-badge
                        v-if="i.era_edicao"
                        color="orange"
                        text-color="white"
                        class="q-ml-sm"
                      >
                        equipe nova
                      </q-badge>
                      <div v-if="i.era_edicao" class="text-caption text-orange-9">
                        Estava como "editar", mas essa equipe ainda não existe.
                      </div>
                    </td>
                    <td>{{ i.total }}</td>
                    <td>
                      {{
                        Object.entries(i.vagas)
                          .map(([f, q]) => q + ' ' + f)
                          .join(', ')
                      }}
                    </td>
                  </tr>
                </tbody>
              </q-markup-table>
            </div>

            <div v-if="planoPlanilha.editar.length">
              <div class="text-subtitle2 q-mb-xs"> Editar </div>
              <q-markup-table flat dense bordered separator="horizontal" class="tabela-detalhe">
                <thead>
                  <tr>
                    <th class="text-left col-ordenavel" @click="ordenarEditarPlanilha('linha')">
                      Linha
                      <q-icon
                        v-if="ordenacaoEditarPlanilha.coluna === 'linha'"
                        :name="ordenacaoEditarPlanilha.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                        size="14px"
                        class="q-ml-xs"
                      />
                    </th>
                    <th class="text-left col-ordenavel" @click="ordenarEditarPlanilha('equipe')">
                      Equipe
                      <q-icon
                        v-if="ordenacaoEditarPlanilha.coluna === 'equipe'"
                        :name="ordenacaoEditarPlanilha.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                        size="14px"
                        class="q-ml-xs"
                      />
                    </th>
                    <th class="text-left">Resumo</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="i in editarPlanilhaOrdenados" :key="'ed' + i.linha">
                    <td>{{ i.linha }}</td>
                    <td>{{ i.equipe }}</td>
                    <td>{{ i.resumo }}</td>
                  </tr>
                </tbody>
              </q-markup-table>
            </div>

            <div v-if="planoPlanilha.excluir.length">
              <div class="text-subtitle2 text-negative q-mb-xs"> Excluir </div>
              <q-markup-table flat dense bordered separator="horizontal" class="tabela-detalhe">
                <thead>
                  <tr>
                    <th class="text-left col-ordenavel" @click="ordenarExcluirPlanilha('linha')">
                      Linha
                      <q-icon
                        v-if="ordenacaoExcluirPlanilha.coluna === 'linha'"
                        :name="ordenacaoExcluirPlanilha.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                        size="14px"
                        class="q-ml-xs"
                      />
                    </th>
                    <th class="text-left col-ordenavel" @click="ordenarExcluirPlanilha('equipe')">
                      Equipe
                      <q-icon
                        v-if="ordenacaoExcluirPlanilha.coluna === 'equipe'"
                        :name="ordenacaoExcluirPlanilha.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                        size="14px"
                        class="q-ml-xs"
                      />
                    </th>
                    <th class="text-left col-ordenavel" @click="ordenarExcluirPlanilha('vagas')">
                      Vagas perdidas
                      <q-icon
                        v-if="ordenacaoExcluirPlanilha.coluna === 'vagas'"
                        :name="ordenacaoExcluirPlanilha.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                        size="14px"
                        class="q-ml-xs"
                      />
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="i in excluirPlanilhaOrdenados" :key="'x' + i.linha">
                    <td>{{ i.linha }}</td>
                    <td>{{ i.equipe }}</td>
                    <td>{{ i.vagas }}</td>
                  </tr>
                </tbody>
              </q-markup-table>
            </div>
          </div>
        </q-card-section>

        <q-separator />

        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Cancelar" color="grey-7" />

          <q-btn
            color="primary"
            label="Aplicar"
            :disable="!podeAplicarPlanilha"
            :loading="aplicandoPlanilha"
            @click="aplicarPlanilha"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-layout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'

import CabecalhoApp from '../components/CabecalhoApp.vue'
import MarcaDaguaFundo from '../components/MarcaDaguaFundo.vue'
import SelectFiltroMultiplo from '../components/SelectFiltroMultiplo.vue'
import { PODE_GERENCIAR_VAGAS } from '../composables/useSessao'
import { useConfirmacao } from '../composables/useConfirmacao'
import { criarOrdenacaoTabela, ordenarLista } from '../utils/ordenacaoTabela'
import {
  equipeCombinaComResponsavel,
  equipeCombinaComSetor,
  equipeCombinaComTipo,
  equipeNaSelecaoDeBases,
  FUNCOES_SISTEMA,
  OPCAO_TODAS_BASES,
  opcoesResponsavelFiltro,
  opcoesSetorFiltro,
  opcoesTipoFiltro,
  proximaSelecaoBases,
  proximaSelecaoMultipla,
  RESPONSAVEL_TODOS,
  SETOR_TODOS,
  TIPO_TODOS
} from '../utils/equipes'

definePage({ meta: { permissao: PODE_GERENCIAR_VAGAS } })

const { confirmar } = useConfirmacao()

// ============================================================
// ESTADO
// ============================================================

const equipes = ref([])

const carregando = ref(false)
// Spinner que ocupa a lista só na primeira abertura: numa recarga (depois de
// salvar, aplicar planilha...) o conteúdo fica no lugar e o ícone de
// atualizar do cabeçalho é que gira.
const primeiraCarga = ref(true)

const erro = ref('')
const sucesso = ref('')

const filtroEquipe = ref('')
const baseFiltro = ref([])
const tipoFiltro = ref(TIPO_TODOS)
const setorFiltro = ref(SETOR_TODOS)
const coordenadorFiltro = ref([RESPONSAVEL_TODOS])
const supervisorFiltro = ref([RESPONSAVEL_TODOS])

const setoresNegocio = ref([])

const arquivoPlanilha = ref(null)
const planoPlanilha = ref(null)
const dialogPlanilha = ref(false)
const dialogEnvioPlanilha = ref(false)
const baixandoPlanilha = ref(false)
const analisandoPlanilha = ref(false)
const aplicandoPlanilha = ref(false)

// ------------------------------------------------------------
// Ordenação das tabelas de "Conferir mudanças" (clique no cabeçalho)
// ------------------------------------------------------------

const {
  estado: ordenacaoErrosPlanilha,
  ordenarPor: ordenarErrosPlanilha,
  resetar: resetarOrdenacaoErrosPlanilha
} = criarOrdenacaoTabela()

const {
  estado: ordenacaoCriarPlanilha,
  ordenarPor: ordenarCriarPlanilha,
  resetar: resetarOrdenacaoCriarPlanilha
} = criarOrdenacaoTabela()

const {
  estado: ordenacaoEditarPlanilha,
  ordenarPor: ordenarEditarPlanilha,
  resetar: resetarOrdenacaoEditarPlanilha
} = criarOrdenacaoTabela()

const {
  estado: ordenacaoExcluirPlanilha,
  ordenarPor: ordenarExcluirPlanilha,
  resetar: resetarOrdenacaoExcluirPlanilha
} = criarOrdenacaoTabela()

function resetarOrdenacaoPlanilha() {
  resetarOrdenacaoErrosPlanilha()
  resetarOrdenacaoCriarPlanilha()
  resetarOrdenacaoEditarPlanilha()
  resetarOrdenacaoExcluirPlanilha()
}

const errosPlanilhaOrdenados = computed(() => {
  const extratores = { linha: e => e.linha, equipe: e => e.equipe, erro: e => e.erro }
  const extrair = extratores[ordenacaoErrosPlanilha.coluna]
  const lista = planoPlanilha.value?.erros || []
  return extrair ? ordenarLista(lista, extrair, ordenacaoErrosPlanilha) : lista
})

const criarPlanilhaOrdenados = computed(() => {
  const extratores = { linha: i => i.linha, equipe: i => i.equipe, total: i => i.total }
  const extrair = extratores[ordenacaoCriarPlanilha.coluna]
  const lista = planoPlanilha.value?.criar || []
  return extrair ? ordenarLista(lista, extrair, ordenacaoCriarPlanilha) : lista
})

const editarPlanilhaOrdenados = computed(() => {
  const extratores = { linha: i => i.linha, equipe: i => i.equipe }
  const extrair = extratores[ordenacaoEditarPlanilha.coluna]
  const lista = planoPlanilha.value?.editar || []
  return extrair ? ordenarLista(lista, extrair, ordenacaoEditarPlanilha) : lista
})

const excluirPlanilhaOrdenados = computed(() => {
  const extratores = { linha: i => i.linha, equipe: i => i.equipe, vagas: i => i.vagas }
  const extrair = extratores[ordenacaoExcluirPlanilha.coluna]
  const lista = planoPlanilha.value?.excluir || []
  return extrair ? ordenarLista(lista, extrair, ordenacaoExcluirPlanilha) : lista
})

const podeAplicarPlanilha = computed(() => {
  const plano = planoPlanilha.value
  if (!plano || plano.erros.length) {
    return false
  }
  return Boolean(plano.criar.length || plano.editar.length || plano.excluir.length)
})

// ============================================================
// LISTA
// ============================================================

const bases = computed(() =>
  [...new Set(equipes.value.map(equipe => equipe.base).filter(Boolean))].sort()
)

const opcoesBaseFiltro = computed(() => [
  { label: 'Todas as bases', value: OPCAO_TODAS_BASES },
  ...bases.value.map(base => ({ label: base, value: base }))
])

function atualizarSelecaoBaseFiltro(selecao) {
  baseFiltro.value = proximaSelecaoBases(baseFiltro.value, selecao)
}

const opcoesTipos = computed(() => opcoesTipoFiltro(equipes.value))
const opcoesSetores = computed(() => opcoesSetorFiltro(equipes.value))
const opcoesCoordenadores = computed(() =>
  opcoesResponsavelFiltro(equipes.value, 'coordenador', 'Todos os coordenadores')
)
const opcoesSupervisores = computed(() =>
  opcoesResponsavelFiltro(equipes.value, 'supervisor', 'Todos os supervisores')
)

const equipesFiltradas = computed(() => {
  const termo = (filtroEquipe.value || '').trim().toLowerCase()

  return equipes.value.filter(
    equipe =>
      equipeNaSelecaoDeBases(equipe, baseFiltro.value || []) &&
      equipeCombinaComTipo(equipe, tipoFiltro.value) &&
      equipeCombinaComSetor(equipe, setorFiltro.value) &&
      equipeCombinaComResponsavel(equipe, 'coordenador', coordenadorFiltro.value) &&
      equipeCombinaComResponsavel(equipe, 'supervisor', supervisorFiltro.value) &&
      (!termo || `${equipe.prefixo} ${equipe.base}`.toLowerCase().includes(termo))
  )
})

// vagas padrão: o Folguista Extra fica fora da conta (é gerido no Banco de Dados)
function vagasPadrao(equipe) {
  return (equipe?.vagas || []).filter(vaga => !vaga.eh_extra)
}

function contagemDaEquipe(equipe) {
  const vagas = vagasPadrao(equipe)
  const ocupadas = vagas.filter(vaga => vaga.ocupada).length
  return { total: vagas.length, ocupadas, livres: vagas.length - ocupadas }
}

const equipesComVagaLivre = computed(
  () => equipesFiltradas.value.filter(equipe => contagemDaEquipe(equipe).livres).length
)

// ------------------------------------------------------------
// Seleção para editar várias de uma vez
// ------------------------------------------------------------

const selecionadas = ref([])

function alternarSelecao(id) {
  selecionadas.value = selecionadas.value.includes(id)
    ? selecionadas.value.filter(item => item !== id)
    : [...selecionadas.value, id]
}

const estadoMarcarTodas = computed(() => {
  const ids = equipesFiltradas.value.map(equipe => equipe.id)
  const marcadas = ids.filter(id => selecionadas.value.includes(id)).length
  if (!marcadas) {
    return false
  }
  return marcadas === ids.length ? true : null
})

function marcarTodasFiltradas(marcar) {
  const ids = equipesFiltradas.value.map(equipe => equipe.id)
  selecionadas.value = marcar
    ? [...new Set([...selecionadas.value, ...ids])]
    : selecionadas.value.filter(id => !ids.includes(id))
}

// ============================================================
// OPÇÕES DOS CAMPOS (com busca e texto novo)
// ============================================================

const basesFiltradas = ref([])
const estruturasFiltradas = ref([])
const funcoesFiltradas = ref([])
const contasFiltradas = ref([])

// contas que podem ser supervisor ou coordenador de vaga: o nome escolhido
// aqui é o da conta, e o servidor liga a vaga a ela
// (ver database/responsaveis_vaga.py)
const contasResponsaveis = ref([])

// o coordenador da vaga pode ser um Gerente (equipe que responde direto a ele)
const NIVEIS_ACEITOS = { SUPERVISOR: ['SUPERVISOR'], COORDENADOR: ['COORDENADOR', 'GERENTE'] }

function nomesDasContas(campo) {
  return contasResponsaveis.value
    .filter(conta => NIVEIS_ACEITOS[campo].includes(conta.nivel) && conta.ativo)
    .map(conta => conta.nome)
}

function semConta(campo, nome) {
  const procurado = (nome || '').trim().toUpperCase()
  return Boolean(procurado) &&
    !contasResponsaveis.value.some(
      conta =>
        NIVEIS_ACEITOS[campo].includes(conta.nivel) &&
        (conta.nome || '').trim().toUpperCase() === procurado
    )
}

const estruturasDisponiveis = computed(() => {
  const valores = new Set()
  equipes.value.forEach(equipe => (equipe.tipos || []).forEach(tipo => tipo && valores.add(tipo)))
  return valores.size ? [...valores].sort() : ['CONSTRUÇÃO']
})

const funcoesDisponiveis = computed(() => {
  const valores = new Set(FUNCOES_SISTEMA)
  equipes.value.forEach(equipe =>
    (equipe.vagas || []).forEach(vaga => vaga.funcao_er && valores.add(vaga.funcao_er))
  )
  return [...valores].sort()
})

function filtrarLista(lista, termo) {
  const busca = (termo || '').toLowerCase()
  return busca ? lista.filter(item => item.toLowerCase().includes(busca)) : lista
}

function filtrarBases(termo, atualizar) {
  atualizar(() => (basesFiltradas.value = filtrarLista(bases.value, termo)))
}

function filtrarEstruturas(termo, atualizar) {
  atualizar(() => (estruturasFiltradas.value = filtrarLista(estruturasDisponiveis.value, termo)))
}

function filtrarFuncoes(termo, atualizar) {
  atualizar(() => (funcoesFiltradas.value = filtrarLista(funcoesDisponiveis.value, termo)))
}

function filtrarContas(campo, termo, atualizar) {
  atualizar(() => (contasFiltradas.value = filtrarLista(nomesDasContas(campo), termo)))
}

async function carregarContasResponsaveis() {
  try {
    const resposta = await fetch('/api/responsaveis-vaga')
    const dados = await resposta.json()
    contasResponsaveis.value = Array.isArray(dados) ? dados : []
  } catch (e) {
    console.error(e)
  }
}

// ============================================================
// PAINEL DA EQUIPE
// ============================================================
//
// Uma equipe é organizada por disciplina (tipo de equipe): setor, supervisor
// e coordenador valem para a disciplina inteira, e cada função tem uma
// quantidade de vagas. É o mesmo formato que o servidor recebe em
// PUT /api/equipes/<id> (ver responsaveis_por_tipo em app.py).

let proximaChave = 0
const chave = () => ++proximaChave

const painel = reactive({
  modo: null, // null | 'nova' | 'editar'
  passo: 1, // só na nova: 1 = base e prefixo, 2 = vagas
  equipeId: null,
  base: '',
  prefixo: '',
  extras: 0,
  disciplinas: [],
  // funções que existiam e saíram do painel: vão com quantidade 0, senão o
  // servidor não sabe que deve tirar essas vagas
  removidas: []
})

const painelTocado = ref(false)
const salvandoPainel = ref(false)
let retratoPainel = ''

function novaLinhaFuncao(funcao = null, quantidade = 1, ocupadas = 0) {
  return { chave: chave(), funcao, quantidade, ocupadas, original: funcao ? quantidade : 0 }
}

function novaDisciplina(tipo = 'CONSTRUÇÃO') {
  return {
    chave: chave(),
    tipo,
    tipoOriginal: null,
    setor: null,
    supervisor: '',
    coordenador: '',
    funcoes: [novaLinhaFuncao()]
  }
}

function disciplinasDaEquipe(equipe) {
  const porTipo = new Map()
  for (const vaga of vagasPadrao(equipe)) {
    if (!porTipo.has(vaga.tipo)) {
      porTipo.set(vaga.tipo, {
        chave: chave(),
        tipo: vaga.tipo,
        tipoOriginal: vaga.tipo,
        setor: vaga.setor || null,
        supervisor: vaga.supervisor || '',
        coordenador: vaga.coordenador || '',
        porFuncao: new Map()
      })
    }
    const funcoes = porTipo.get(vaga.tipo).porFuncao
    const atual = funcoes.get(vaga.funcao_er) || { quantidade: 0, ocupadas: 0 }
    atual.quantidade += 1
    atual.ocupadas += vaga.ocupada ? 1 : 0
    funcoes.set(vaga.funcao_er, atual)
  }

  return [...porTipo.values()].map(({ porFuncao, ...disciplina }) => ({
    ...disciplina,
    funcoes: [...porFuncao.entries()].map(([funcao, { quantidade, ocupadas }]) =>
      novaLinhaFuncao(funcao, quantidade, ocupadas)
    )
  }))
}

function retratoAtual() {
  return JSON.stringify([painel.base, painel.prefixo, painel.disciplinas, painel.removidas])
}

const painelAlterado = computed(() => Boolean(painel.modo) && retratoAtual() !== retratoPainel)

async function podeTrocarDePainel() {
  if (!painelAlterado.value) {
    return true
  }
  return confirmar('Há mudanças não salvas nesta equipe. Descartar?', {
    titulo: 'Descartar mudanças',
    textoConfirmar: 'Descartar'
  })
}

function preencherPainel(modo, dados) {
  Object.assign(painel, {
    modo,
    passo: dados.passo || 1,
    equipeId: dados.equipeId ?? null,
    base: dados.base || '',
    prefixo: dados.prefixo || '',
    extras: dados.extras || 0,
    disciplinas: dados.disciplinas || [],
    removidas: []
  })
  painelTocado.value = false
  retratoPainel = retratoAtual()
}

async function abrirEquipe(equipe) {
  if (painel.equipeId === equipe.id && painel.modo === 'editar') {
    return
  }
  if (!(await podeTrocarDePainel())) {
    return
  }
  preencherPainel('editar', {
    equipeId: equipe.id,
    base: equipe.base,
    prefixo: equipe.prefixo,
    extras: (equipe.vagas || []).length - vagasPadrao(equipe).length,
    disciplinas: disciplinasDaEquipe(equipe)
  })
}

async function iniciarNovaEquipe() {
  if (!(await podeTrocarDePainel())) {
    return
  }
  preencherPainel('nova', { passo: 1 })
}

async function fecharPainel() {
  if (!(await podeTrocarDePainel())) {
    return
  }
  preencherPainel(null, {})
}

const resumoPainel = computed(() => {
  let total = 0
  let ocupadas = 0
  for (const disciplina of painel.disciplinas) {
    for (const linha of disciplina.funcoes) {
      total += Number(linha.original || 0)
      ocupadas += linha.ocupadas
    }
  }
  return { total, ocupadas }
})

// ------------------------------------------------------------
// Passo 1 da nova equipe
// ------------------------------------------------------------

const erroBase = computed(() => ((painel.base || '').trim() ? '' : 'Informe a base.'))

const erroPrefixo = computed(() => {
  const base = (painel.base || '').trim().toUpperCase()
  const prefixo = (painel.prefixo || '').trim()
  if (!prefixo) {
    return 'Informe o prefixo.'
  }
  const repetida = equipes.value.some(
    equipe =>
      equipe.id !== painel.equipeId &&
      (equipe.base || '').toUpperCase() === base &&
      (equipe.prefixo || '').trim().toUpperCase() === prefixo.toUpperCase()
  )
  return repetida ? `Já existe a equipe ${prefixo} na base ${base}.` : ''
})

const problemaIdentificacao = computed(() => erroBase.value || erroPrefixo.value)

function avancarParaVagas() {
  painelTocado.value = true
  if (problemaIdentificacao.value) {
    return
  }
  painel.base = painel.base.trim().toUpperCase()
  painel.prefixo = painel.prefixo.trim()
  if (!painel.disciplinas.length) {
    // a disciplina mais comum; o tipo pode ser trocado no próprio bloco
    painel.disciplinas = [novaDisciplina('CONSTRUÇÃO')]
  }
  painel.passo = 2
  painelTocado.value = false
}

// ------------------------------------------------------------
// Disciplinas e funções
// ------------------------------------------------------------

function adicionarDisciplina() {
  const usados = new Set(painel.disciplinas.map(d => (d.tipo || '').toUpperCase()))
  const livre = estruturasDisponiveis.value.find(tipo => !usados.has(tipo)) || ''
  painel.disciplinas.push(novaDisciplina(livre))
}

function guardarRemovida(disciplina, linha) {
  if (linha.original && disciplina.tipoOriginal && linha.funcao) {
    painel.removidas.push({
      tipo: disciplina.tipoOriginal,
      funcao: linha.funcao,
      ocupadas: linha.ocupadas
    })
  }
}

async function removerDisciplina(indice) {
  const disciplina = painel.disciplinas[indice]
  const ocupadas = disciplina.funcoes.reduce((soma, linha) => soma + linha.ocupadas, 0)
  if (
    ocupadas &&
    !(await confirmar(
      `O tipo ${disciplina.tipo} tem ${ocupadas} pessoa(s) alocada(s) nesta equipe. ` +
        'Ao salvar, elas saem das vagas. Tirar este tipo?',
      { titulo: 'Tirar tipo de equipe', textoConfirmar: 'Tirar' }
    ))
  ) {
    return
  }
  disciplina.funcoes.forEach(linha => guardarRemovida(disciplina, linha))
  painel.disciplinas.splice(indice, 1)
}

function adicionarFuncao(disciplina) {
  disciplina.funcoes.push(novaLinhaFuncao())
}

function removerFuncao(disciplina, indice) {
  guardarRemovida(disciplina, disciplina.funcoes[indice])
  disciplina.funcoes.splice(indice, 1)
}

const problemaVagas = computed(() => {
  if (!painel.disciplinas.length) {
    return 'Adicione ao menos um tipo de equipe.'
  }
  const tipos = new Set()
  for (const disciplina of painel.disciplinas) {
    const tipo = (disciplina.tipo || '').trim().toUpperCase()
    if (!tipo) {
      return 'Escolha o tipo de equipe de cada bloco.'
    }
    if (tipos.has(tipo)) {
      return `O tipo ${tipo} aparece duas vezes. Junte as funções num bloco só.`
    }
    tipos.add(tipo)
    const funcoes = new Set()
    for (const linha of disciplina.funcoes) {
      const funcao = (linha.funcao || '').trim().toUpperCase()
      if (!funcao) {
        return `Escolha a função de cada linha em ${tipo}.`
      }
      if (funcoes.has(funcao)) {
        return `A função ${funcao} aparece duas vezes em ${tipo}.`
      }
      funcoes.add(funcao)
      if (!Number.isInteger(Number(linha.quantidade)) || Number(linha.quantidade) < 0) {
        return `A quantidade de ${funcao} em ${tipo} precisa ser um número inteiro.`
      }
    }
  }
  const total = painel.disciplinas.reduce(
    (soma, d) => soma + d.funcoes.reduce((s, l) => s + Number(l.quantidade || 0), 0),
    0
  )
  return total ? '' : 'A equipe precisa de ao menos uma vaga.'
})

// linhas que o servidor recebe: as do painel e, com quantidade 0, as que saíram
function vagasParaEnviar() {
  const linhas = []
  const vistos = new Set()
  for (const disciplina of painel.disciplinas) {
    const tipo = disciplina.tipo.trim().toUpperCase()
    const responsaveis = {
      setor: disciplina.setor || '',
      supervisor: (disciplina.supervisor || '').trim(),
      coordenador: (disciplina.coordenador || '').trim()
    }
    for (const linha of disciplina.funcoes) {
      const funcao = linha.funcao.trim().toUpperCase()
      vistos.add(`${tipo}|${funcao}`)
      linhas.push({ tipo, funcao, quantidade: Number(linha.quantidade || 0), ...responsaveis })
    }
    // trocou o tipo da disciplina: zera as vagas do tipo antigo
    if (disciplina.tipoOriginal && disciplina.tipoOriginal !== tipo) {
      for (const linha of disciplina.funcoes) {
        if (linha.original) {
          painel.removidas.push({
            tipo: disciplina.tipoOriginal,
            funcao: linha.funcao,
            ocupadas: linha.ocupadas,
            retipo: true
          })
        }
      }
    }
  }
  for (const removida of painel.removidas) {
    const chaveLinha = `${removida.tipo}|${removida.funcao}`
    if (!vistos.has(chaveLinha)) {
      vistos.add(chaveLinha)
      linhas.push({ tipo: removida.tipo, funcao: removida.funcao, quantidade: 0, retipo: Boolean(removida.retipo) })
    }
  }
  return linhas
}

// vagas ocupadas que a nova quantidade não comporta: o servidor só tira
// pessoas de vaga com confirmação explícita (confirmar_remocoes)
function vagasOcupadasARemover(equipe, linhas) {
  const porChave = new Map()
  for (const vaga of vagasPadrao(equipe)) {
    const chaveVaga = `${vaga.tipo}|${vaga.funcao_er}`
    if (!porChave.has(chaveVaga)) {
      porChave.set(chaveVaga, [])
    }
    porChave.get(chaveVaga).push(vaga)
  }
  const remover = []
  for (const linha of linhas) {
    // tipo trocado: o servidor reclassifica as vagas e as pessoas ficam
    if (linha.retipo) {
      continue
    }
    const vagas = porChave.get(`${linha.tipo}|${linha.funcao}`) || []
    const livres = vagas.filter(vaga => !vaga.ocupada).length
    const reducao = vagas.length - linha.quantidade
    if (reducao > livres) {
      remover.push(...vagas.filter(vaga => vaga.ocupada).slice(0, reducao - livres))
    }
  }
  return remover
}

async function enviarEquipe(equipeId, linhas, confirmarRemocoes) {
  const resposta = await fetch(`/api/equipes/${equipeId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      base: painel.base.trim().toUpperCase(),
      prefixo: painel.prefixo.trim(),
      vagas: linhas,
      confirmar_remocoes: confirmarRemocoes
    })
  })
  const dados = await resposta.json()
  if (!resposta.ok || dados.erro) {
    const detalhe = (dados.erros || []).map(e => e.erro).join(' ')
    throw new Error([dados.erro || 'Não foi possível salvar a equipe.', detalhe].filter(Boolean).join(' '))
  }
  return dados
}

async function salvarPainel() {
  painelTocado.value = true
  erro.value = ''
  sucesso.value = ''
  if (problemaIdentificacao.value || problemaVagas.value) {
    return
  }

  const removidasAntes = painel.removidas.length
  const linhas = vagasParaEnviar()
  painel.removidas.splice(removidasAntes)

  let confirmarRemocoes = []
  if (painel.modo === 'editar') {
    const equipe = equipes.value.find(item => item.id === painel.equipeId)
    const remover = vagasOcupadasARemover(equipe, linhas)
    if (remover.length) {
      const nomes = remover.map(v => `${v.colaborador?.nome || v.colaborador?.chapa} (${v.funcao_er})`).join(', ')
      if (
        !(await confirmar(
          `Com as quantidades novas, ${remover.length} pessoa(s) saem das vagas: ${nomes}. Confirma?`,
          { titulo: 'Tirar pessoas das vagas', textoConfirmar: 'Salvar mesmo assim' }
        ))
      ) {
        return
      }
      confirmarRemocoes = remover.map(v => v.id)
    }
  }

  salvandoPainel.value = true
  let equipeId = painel.equipeId
  try {
    if (painel.modo === 'nova') {
      const resposta = await fetch('/api/equipes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ base: painel.base.trim().toUpperCase(), prefixo: painel.prefixo.trim() })
      })
      const dados = await resposta.json()
      if (!resposta.ok || dados.erro) {
        throw new Error(dados.erro || 'Não foi possível criar a equipe.')
      }
      equipeId = dados.equipe.id
      // a partir daqui a equipe existe: se as vagas falharem, ela abre para editar
      painel.modo = 'editar'
      painel.equipeId = equipeId
    }

    const dados = await enviarEquipe(equipeId, linhas, confirmarRemocoes)
    sucesso.value = `Equipe ${dados.equipe.prefixo} salva.`
    await carregarEquipes()
    const atualizada = equipes.value.find(item => item.id === equipeId)
    if (atualizada) {
      retratoPainel = ''
      painel.equipeId = null
      await abrirEquipe(atualizada)
    }
  } catch (e) {
    erro.value = e.message || 'Não foi possível salvar a equipe.'
    if (painel.modo === 'editar' && equipeId) {
      await carregarEquipes()
    }
  } finally {
    salvandoPainel.value = false
  }
}

async function removerEquipeAberta() {
  const prefixo = painel.prefixo
  if (
    !(await confirmar(`Excluir a equipe ${prefixo} e todas as vagas dela?`, {
      titulo: 'Excluir equipe',
      textoConfirmar: 'Excluir'
    }))
  ) {
    return
  }

  erro.value = ''
  sucesso.value = ''

  try {
    const resposta = await fetch(`/api/equipes/${painel.equipeId}`, { method: 'DELETE' })
    const dados = await resposta.json()
    if (!resposta.ok || dados.erro) {
      throw new Error(dados.erro || 'Não foi possível excluir a equipe.')
    }
    selecionadas.value = selecionadas.value.filter(id => id !== painel.equipeId)
    preencherPainel(null, {})
    sucesso.value = `Equipe ${prefixo} excluída.`
    await carregarEquipes()
  } catch (e) {
    erro.value = e.message || 'Não foi possível excluir a equipe.'
  }
}

// ============================================================
// SETOR E RESPONSÁVEIS DE VÁRIAS EQUIPES
// ============================================================

const dialogSelecionadas = ref(false)
const salvandoMassa = ref(false)
const massa = reactive({ setor: null, supervisor: '', coordenador: '' })

function abrirEdicaoSelecionadas() {
  Object.assign(massa, { setor: null, supervisor: '', coordenador: '' })
  dialogSelecionadas.value = true
}

async function aplicarEdicaoSelecionadas() {
  const novo = {
    setor: massa.setor || '',
    supervisor: (massa.supervisor || '').trim(),
    coordenador: (massa.coordenador || '').trim()
  }
  if (!novo.setor && !novo.supervisor && !novo.coordenador) {
    dialogSelecionadas.value = false
    return
  }

  // cada disciplina mantém o que tinha nos campos deixados em branco
  const equipesPayload = equipes.value
    .filter(equipe => selecionadas.value.includes(equipe.id))
    .map(equipe => ({
      equipe_id: equipe.id,
      base: equipe.base,
      prefixo: equipe.prefixo,
      vagas: disciplinasDaEquipe(equipe).flatMap(disciplina =>
        disciplina.funcoes.map(linha => ({
          tipo: disciplina.tipo,
          funcao: linha.funcao,
          quantidade: linha.quantidade,
          setor: novo.setor || disciplina.setor || '',
          supervisor: novo.supervisor || disciplina.supervisor,
          coordenador: novo.coordenador || disciplina.coordenador
        }))
      ),
      confirmar_remocoes: []
    }))
    .filter(item => item.vagas.length)

  erro.value = ''
  sucesso.value = ''
  salvandoMassa.value = true
  try {
    const resposta = await fetch('/api/equipes/edicao-massa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ equipes: equipesPayload })
    })
    const dados = await resposta.json()
    if (!resposta.ok || dados.erro) {
      const detalhe = (dados.erros || []).map(e => `${e.equipe}: ${e.erro}`).join(' | ')
      throw new Error([dados.erro || 'Não foi possível aplicar.', detalhe].filter(Boolean).join(' '))
    }
    sucesso.value = `${dados.equipes_editadas} equipe(s) atualizada(s).`
    dialogSelecionadas.value = false
    selecionadas.value = []
    await carregarEquipes()
    const aberta = equipes.value.find(item => item.id === painel.equipeId)
    if (aberta && painel.modo === 'editar' && !painelAlterado.value) {
      painel.equipeId = null
      await abrirEquipe(aberta)
    }
  } catch (e) {
    erro.value = e.message || 'Não foi possível aplicar.'
  } finally {
    salvandoMassa.value = false
  }
}

// ============================================================
// CARREGAR E PLANILHA
// ============================================================

// carregarEquipes é chamada depois de cada criação/edição; se duas chamadas
// se cruzam, só a última disparada grava na tela.
let sequenciaEquipes = 0

async function carregarEquipes() {
  const minhaSequencia = ++sequenciaEquipes
  carregando.value = true

  try {
    const resposta = await fetch('/api/equipes')
    const dados = await resposta.json()
    if (!resposta.ok || dados.erro) {
      throw new Error(dados.erro || 'Erro ao carregar as equipes.')
    }
    if (minhaSequencia === sequenciaEquipes) {
      equipes.value = dados
      const existentes = new Set(dados.map(equipe => equipe.id))
      selecionadas.value = selecionadas.value.filter(id => existentes.has(id))
    }
  } catch (e) {
    if (minhaSequencia === sequenciaEquipes) {
      erro.value = e.message || 'Erro ao carregar as equipes.'
    }
  } finally {
    if (minhaSequencia === sequenciaEquipes) {
      carregando.value = false
      primeiraCarga.value = false
    }
  }
}

async function baixarPlanilha() {
  erro.value = ''
  baixandoPlanilha.value = true

  try {
    const resposta = await fetch('/api/equipes/planilha')
    if (!resposta.ok) {
      const dados = await resposta.json().catch(() => ({}))
      throw new Error(dados.erro || 'Erro ao gerar a planilha.')
    }
    const blob = await resposta.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'equipes.xlsx'
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    erro.value = e.message || 'Erro ao gerar a planilha.'
  } finally {
    baixandoPlanilha.value = false
  }
}

async function enviarPlanilha(rota) {
  const corpo = new FormData()
  corpo.append('arquivo', arquivoPlanilha.value)
  const resposta = await fetch(rota, { method: 'POST', body: corpo })
  const dados = await resposta.json()
  return { ok: resposta.ok, dados }
}

async function analisarPlanilha() {
  if (!arquivoPlanilha.value) {
    return
  }

  erro.value = ''
  sucesso.value = ''
  analisandoPlanilha.value = true

  try {
    const { ok, dados } = await enviarPlanilha('/api/equipes/planilha/previa')
    if (!ok || dados.erro) {
      throw new Error(dados.erro || 'Erro ao analisar a planilha.')
    }
    planoPlanilha.value = dados
    resetarOrdenacaoPlanilha()
    dialogEnvioPlanilha.value = false
    dialogPlanilha.value = true
  } catch (e) {
    erro.value = e.message || 'Erro ao analisar a planilha.'
    dialogEnvioPlanilha.value = false
  } finally {
    analisandoPlanilha.value = false
  }
}

async function aplicarPlanilha() {
  erro.value = ''
  sucesso.value = ''
  aplicandoPlanilha.value = true

  try {
    const { ok, dados } = await enviarPlanilha('/api/equipes/planilha/aplicar')
    if (!ok || dados.erro) {
      throw new Error(dados.erro || 'Erro ao aplicar a planilha.')
    }
    sucesso.value =
      `Planilha aplicada: ${dados.criadas} equipe(s) criada(s), ` +
      `${dados.editadas} editada(s), ${dados.excluidas} excluída(s).`
    dialogPlanilha.value = false
    planoPlanilha.value = null
    arquivoPlanilha.value = null
    preencherPainel(null, {})
    await carregarEquipes()
  } catch (e) {
    erro.value = e.message || 'Erro ao aplicar a planilha.'
  } finally {
    aplicandoPlanilha.value = false
  }
}

async function carregarSetoresNegocio() {
  try {
    const resposta = await fetch('/api/sessao')
    const dados = await resposta.json()
    setoresNegocio.value = dados.setores_negocio || []
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  carregarSetoresNegocio()
  carregarContasResponsaveis()
  carregarEquipes()
})
</script>

<style scoped>
.lista-equipes {
  max-height: 68vh;
}

.item-ativo {
  background: var(--realce, rgba(122, 26, 44, 0.08));
  color: inherit;
}

.contagem-vagas {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.barra-selecao {
  border-bottom: 1px solid var(--q-primary);
}

@media (min-width: 1024px) {
  .painel-equipe {
    position: sticky;
    top: 70px;
  }
}

.bloco-disciplina {
  border: 1px solid var(--linha, rgba(0, 0, 0, 0.12));
  border-radius: 10px;
  padding: 12px;
}

.linha-funcao + .linha-funcao {
  margin-top: 6px;
}

.campo-quantidade {
  width: 58px;
}

.campo-quantidade :deep(input) {
  font-variant-numeric: tabular-nums;
}

.info-ocupadas {
  width: 96px;
  white-space: nowrap;
}

@media (max-width: 599px) {
  .linha-funcao {
    flex-wrap: wrap;
  }

  .info-ocupadas {
    width: auto;
  }
}

.tabela-detalhe :deep(th) {
  font-family: var(--fonte-ui);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-size: 0.7rem;
}

.tabela-detalhe :deep(td) {
  font-size: 0.8rem;
}

.tabela-detalhe :deep(th.col-ordenavel) {
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

.tabela-detalhe :deep(th.col-ordenavel:hover) {
  color: var(--q-primary);
}
</style>
