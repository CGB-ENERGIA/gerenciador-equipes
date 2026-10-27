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
              Controle nominal do pessoal indireto por setor, base e responsável
            </div>
          </div>

          <!-- um botão só: o diálogo baixa a planilha atual e recebe a preenchida -->
          <div v-if="podeEditar" class="col-auto">
            <q-btn
              class="btn-exportar"
              color="positive"
              text-color="white"
              no-caps
              icon="table_view"
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
            </div>
          </q-card-section>
        </q-card>

        <!-- ================================================== -->
        <!-- INDICADORES (nominais: pessoas, não vagas) -->
        <!-- ================================================== -->

        <div class="row q-col-gutter-md q-mb-md">
          <div
            v-for="indicador in indicadores"
            :key="indicador.chave"
            class="col-6 col-md"
          >
            <q-card
              class="indicador cursor-pointer"
              :class="[
                `indicador--${indicador.chave}`,
                { 'indicador--ativo': filtroStatus === indicador.chave }
              ]"
              @click="alternarStatus(indicador.chave)"
            >
              <q-card-section class="row items-center no-wrap">
                <div class="indicador__icone">
                  <q-icon :name="indicador.icone" size="22px" />
                </div>
                <div class="q-ml-md">
                  <div class="indicador__valor">{{ indicador.valor }}</div>
                  <div class="indicador__rotulo">{{ indicador.rotulo }}</div>
                </div>
              </q-card-section>
            </q-card>
          </div>
        </div>

        <!-- ================================================== -->
        <!-- CONTEÚDO -->
        <!-- ================================================== -->

        <div v-if="carregando && primeiraCarga" class="row justify-center q-pa-xl">
          <q-spinner color="primary" size="50px" />
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
                      </div>

                      <div class="col q-px-md">
                        <button
                          v-if="grupo.responsavelUnico"
                          type="button"
                          class="responsavel-chip"
                          :disabled="!podeEditar"
                          @click="abrirTrocaResponsavel(grupo.responsavelUnico)"
                        >
                          <span v-if="grupo.responsavelUnico.responsavel" class="responsavel-chip__texto">
                            <strong>{{ nomeCurto(grupo.responsavelUnico.responsavel.nome) }}</strong>
                            <small>
                              {{ grupo.responsavelUnico.responsavel.chapa }}
                              <template v-if="grupo.responsavelUnico.responsavel.funcao">
                                · {{ grupo.responsavelUnico.responsavel.funcao }}
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
                            Responsável pelo setor inteiro · clique para trocar
                          </q-tooltip>
                        </button>
                      </div>

                      <div class="cartao-setor__contagem">
                        <div class="cartao-setor__numero">{{ grupo.total }}</div>
                        <div class="cartao-setor__legenda">
                          {{ grupo.total === 1 ? 'pessoa' : 'pessoas' }}
                        </div>
                      </div>
                    </div>
                  </q-card-section>

                  <div class="secoes-base">
                    <div v-for="secao in grupo.bases" :key="secao.base" class="secao-base">
                      <!--
                        O responsável fica na mesma linha da base (ou no
                        cabeçalho do setor, quando é um só no setor todo). Se
                        a base tem mais de um, os demais abrem uma linha
                        própria (sem repetir a base) acima das suas pessoas.
                      -->
                      <div
                        v-for="(time, indice) in secao.responsaveis"
                        :key="time.chapa || 'sem'"
                        class="time-responsavel"
                      >
                        <div
                          class="secao-base__cabecalho"
                          :class="{ 'secao-base__cabecalho--sub': indice > 0 }"
                        >
                          <q-chip
                            v-if="indice === 0"
                            dense
                            class="chip-base q-ma-none"
                            icon="place"
                          >
                            {{ secao.base }}
                          </q-chip>
                          <button
                            v-if="!grupo.responsavelUnico"
                            type="button"
                            class="responsavel-chip"
                            :disabled="!podeEditar"
                            @click="abrirTrocaResponsavel(time)"
                          >
                            <span v-if="time.responsavel" class="responsavel-chip__texto">
                              <strong>{{ nomeCurto(time.responsavel.nome) }}</strong>
                              <small>
                                {{ time.responsavel.chapa }}
                                <template v-if="time.responsavel.funcao">
                                  · {{ time.responsavel.funcao }}
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
                              Responsável de {{ time.pessoas.length }}
                              {{ time.pessoas.length === 1 ? 'pessoa' : 'pessoas' }} · clique para trocar
                            </q-tooltip>
                          </button>
                          <q-space />
                          <span class="secao-base__contagem">{{ time.pessoas.length }}</span>
                        </div>

                        <q-list dense separator class="lista-pessoas">
                          <q-item
                            v-for="pessoa in time.pessoas"
                            :key="pessoa.chapa"
                            :class="{ 'linha-afastado': pessoa.afastado }"
                          >
                            <q-item-section avatar class="secao-chapa">
                              <span class="chapa-pessoa">{{ pessoa.chapa }}</span>
                            </q-item-section>

                            <q-item-section>
                              <q-item-label
                                v-caber-na-linha
                                class="text-weight-medium"
                                :title="pessoa.nome"
                              >
                                {{ pessoa.nome }}
                              </q-item-label>
                              <q-item-label v-if="pessoa.alocacao.observacao" caption>
                                <q-icon name="notes" size="12px" />
                                {{ pessoa.alocacao.observacao }}
                              </q-item-label>
                            </q-item-section>

                            <q-item-section side>
                              <div class="row items-center no-wrap">
                                <span
                                  class="funcao-pessoa"
                                  :title="
                                    pessoa.alocacao.funcao
                                      ? `${pessoa.alocacao.funcao} (no cadastro: ${pessoa.funcao || '—'})`
                                      : pessoa.funcao
                                  "
                                >
                                  {{ funcaoExibida(pessoa) }}
                                </span>
                                <q-chip
                                  v-if="pessoa.afastado"
                                  dense
                                  class="bg-afastado text-afastado"
                                  label="afastado"
                                />
                                <q-btn
                                  v-if="podeEditar"
                                  flat
                                  round
                                  dense
                                  icon="edit"
                                  size="sm"
                                  aria-label="Editar colaborador"
                                  @click="abrirAlocacao(pessoa)"
                                >
                                  <q-tooltip>Editar colaborador</q-tooltip>
                                </q-btn>
                              </div>
                            </q-item-section>
                          </q-item>
                        </q-list>
                      </div>
                    </div>
                  </div>

                  <q-card-actions v-if="podeEditar">
                    <q-btn
                      flat
                      no-caps
                      color="primary"
                      icon="person_add"
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
            <template #prepend><q-icon name="person" /></template>
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
                hint="Escolha ou digite um setor novo"
                :options="opcoesSetorDialogo"
                :readonly="alocacao.modo === 'setor'"
                @filter="filtrarSetores"
                @input-value="valor => (alocacao.setorDigitado = valor)"
              >
                <template #prepend><q-icon name="apartment" /></template>
              </q-select>
            </div>

            <div class="col-12 col-sm-5">
              <q-select
                v-model="alocacao.base"
                outlined
                dense
                label="Base *"
                :options="bases"
                hint="Independe do cadastro"
              >
                <template #prepend><q-icon name="place" /></template>
              </q-select>
            </div>
          </div>

          <q-select
            v-model="alocacao.responsavelChapa"
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
            <template #prepend><q-icon name="supervisor_account" /></template>
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
                ? `No cadastro: ${pessoaAlocacao.funcao || 'sem função'}. Trocar aqui não muda o cadastro.`
                : 'Vazio = a função do cadastro'
            "
            @filter="filtrarFuncoes"
          >
            <template #prepend><q-icon name="badge" /></template>
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
            <template #prepend><q-icon name="notes" /></template>
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
            icon="person_remove"
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
            <template #prepend><q-icon name="supervisor_account" /></template>
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
            Baixe a planilha atual para consultar ou exportar as alocações. Para
            alocar, mover ou trocar o responsável de vários indiretos de uma vez,
            preencha e envie de volta: uma linha por indireto, e quem não estiver
            na planilha continua onde está.
          </div>

          <q-markup-table flat bordered dense class="tabela-modelo">
            <thead>
              <tr>
                <th>SETOR</th>
                <th>BASE</th>
                <th>CHAPA RESPONSÁVEL</th>
                <th>CHAPA INDIRETO</th>
                <th>OBSERVAÇÃO</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>ALMOXARIFADO</td>
                <td>BCB</td>
                <td>19837</td>
                <td>12345</td>
                <td></td>
              </tr>
            </tbody>
          </q-markup-table>

          <div class="row q-col-gutter-sm items-center">
            <div class="col-12 col-sm-auto">
              <q-btn
                outline
                no-caps
                color="primary"
                icon="download"
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
                <template #prepend><q-icon name="attach_file" /></template>
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

            <div v-else class="text-caption">Nada muda com esta planilha.</div>
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
            icon="check"
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
import { computed, onMounted, reactive, ref, watch } from 'vue'

import CabecalhoApp from '../components/CabecalhoApp.vue'
import MarcaDaguaFundo from '../components/MarcaDaguaFundo.vue'
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
const funcoes = ref([])
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
    funcoes.value = dados.funcoes || []
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

function nomeCurto(nome) {
  return String(nome || '').trim().split(/\s+/).slice(0, 2).join(' ')
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
const filtroResponsaveis = ref([TODOS])
const busca = ref('')
const buscaSemSetor = ref('')

// o que está de fato escolhido (vazio = todos)
const escolhidos = selecao => (selecao.includes(TODOS) ? [] : selecao)
const basesAtivas = computed(() => escolhidos(filtroBases.value))
const setoresAtivos = computed(() => escolhidos(filtroSetores.value))
const responsaveisAtivos = computed(() => escolhidos(filtroResponsaveis.value))

function limparFiltros() {
  filtroBases.value = [TODOS]
  filtroSetores.value = [TODOS]
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
const opcoesSetores = computed(() => [
  { label: 'Todos os setores', value: TODOS },
  ...opcoesUnicas(nomesSetores.value)
])
// só os dois primeiros nomes, como no chip; se dois ficarem iguais, a chapa
// desempata
const opcoesResponsaveis = computed(() => {
  const opcoes = [...new Set(alocados.value.map(p => p.alocacao.responsavel_chapa).filter(Boolean))]
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
  return true
}

const alocadosFiltrados = computed(() =>
  alocados.value.filter(pessoa => {
    const a = pessoa.alocacao
    if (basesAtivas.value.length && !basesAtivas.value.includes(a.base)) return false
    if (setoresAtivos.value.length && !setoresAtivos.value.includes(a.setor)) return false
    if (
      responsaveisAtivos.value.length &&
      !responsaveisAtivos.value.includes(a.responsavel_chapa)
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
      !responsaveisAtivos.value.length &&
      (!basesAtivas.value.length || basesAtivas.value.includes(pessoa.base_cadastro)) &&
      casaComBusca(pessoa) &&
      casaComBusca(pessoa, buscaSemSetor.value)
  )
)

// Ordem das pessoas dentro de cada base: primeiro pelo cargo (a função que
// contém o termo, ex. "AUXILIAR DE ALMOXARIFADO" -> AUXILIAR), as demais
// depois, em ordem alfabética. COORDENADOR vem antes de SUPERVISOR por ser
// o cargo acima na hierarquia. A abreviação "SUP" (ex. "SUP OP SERV EXP E
// MANUTENÇÃO") conta como SUPERVISOR; como palavra inteira, para não pegar
// "SUPORTE".
const ORDEM_CARGOS = [
  /COORDENADOR/,
  /SUPERVISOR|\bSUP\b/,
  /ANALISTA/,
  /ENCARREGADO/,
  /ASSISTENTE/,
  /AUXILIAR/
]

// maiúsculas e sem acento, para comparar textos
function normalizarTexto(texto) {
  return String(texto || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
}

function ordemCargo(funcao) {
  const texto = normalizarTexto(funcao)
  const posicao = ORDEM_CARGOS.findIndex(cargo => cargo.test(texto))
  return posicao === -1 ? ORDEM_CARGOS.length : posicao
}

// setor -> base -> responsável -> pessoas
const gruposSetor = computed(() => {
  const porSetor = new Map()
  for (const pessoa of alocadosFiltrados.value) {
    const { setor, base, responsavel_chapa: chapaResp } = pessoa.alocacao
    if (!porSetor.has(setor)) porSetor.set(setor, new Map())
    const porBase = porSetor.get(setor)
    if (!porBase.has(base)) porBase.set(base, new Map())
    const porResp = porBase.get(base)
    const chave = chapaResp || ''
    if (!porResp.has(chave)) porResp.set(chave, [])
    porResp.get(chave).push(pessoa)
  }

  const porFuncaoENome = (a, b) =>
    ordemCargo(funcaoExibida(a)) - ordemCargo(funcaoExibida(b)) ||
    funcaoExibida(a).localeCompare(funcaoExibida(b), 'pt-BR') ||
    a.nome.localeCompare(b.nome, 'pt-BR')

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
      // Um responsável só no setor inteiro: o chip sobe para o cabeçalho
      // do setor em vez de se repetir em cada base.
      const chapas = new Set(secoes.flatMap(s => s.responsaveis.map(t => t.chapa)))
      const [chapaUnica] = chapas
      return {
        nome,
        bases: secoes,
        total: secoes.reduce((soma, s) => soma + s.total, 0),
        responsavelUnico:
          chapas.size === 1
            ? {
                chapa: chapaUnica,
                responsavel: responsavelPorChapa(chapaUnica),
                pessoas: secoes.flatMap(s => s.responsaveis[0].pessoas)
              }
            : null
      }
    })
    .sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'))
})

// ============================================================
// INDICADORES
// ============================================================

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
    chave: 'afastados',
    rotulo: 'Afastados',
    icone: 'event_busy',
    valor: pessoas.value.filter(p => p.afastado).length
  }
  // quem só consulta não vê a lista "Sem setor", então nem o indicador dela
].filter(indicador => podeEditar.value || indicador.chave !== 'semSetor'))

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
  const selecionadas = [alocacao.responsavelChapa, trocaResponsavel.chapa].filter(Boolean)
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
  responsavelChapa: null,
  funcao: null,
  observacao: ''
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
  Boolean(alocacao.chapa && setorEscolhido.value && alocacao.base && alocacao.responsavelChapa)
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
    responsavelChapa: atual?.responsavel_chapa || null,
    funcao: funcaoExibida(pessoa) || null,
    observacao: atual?.observacao || ''
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
    responsavelChapa: null,
    funcao: null,
    observacao: ''
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
          base: alocacao.base,
          responsavel_chapa: alocacao.responsavelChapa,
          // vazio ou igual à do cadastro: o servidor volta a usar a do cadastro
          funcao: alocacao.funcao || '',
          observacao: alocacao.observacao
        })
      },
      'Não foi possível alocar.'
    )
    sucesso.value = `${pessoaAlocacao.value?.nome || 'Indireto'} salvo em ${setorEscolhido.value} · ${alocacao.base}.`
    alocacao.aberto = false
    await carregar()
  } catch (e) {
    erro.value = e.message
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
    pessoas: grupo.pessoas,
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

async function baixarPlanilha() {
  baixando.value = true
  erro.value = ''
  try {
    const resposta = await fetch('/api/indiretos/planilha')
    if (!resposta.ok) {
      const dados = await resposta.json().catch(() => ({}))
      throw new Error(dados.erro || 'Erro ao gerar a planilha.')
    }
    const url = URL.createObjectURL(await resposta.blob())
    const link = document.createElement('a')
    link.href = url
    link.download = 'alocacao-indiretos.xlsx'
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
  () => Boolean(planilha.previa && !planilha.previa.erros.length && mudancasPrevia.value.length)
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
    sucesso.value = `Planilha aplicada: ${r.alocados} alocados, ${r.movidos} movidos, ${r.atualizados} atualizados.`
    planilha.aberto = false
    await carregar()
  } catch (e) {
    erro.value = e.message
    planilha.aberto = false
  } finally {
    planilha.aplicando = false
  }
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

.tabela-modelo th {
  background: var(--marca);
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
