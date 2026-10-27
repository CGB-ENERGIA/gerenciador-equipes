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

          <div class="col-auto row q-gutter-sm">
            <q-btn
              outline
              no-caps
              color="primary"
              icon="upload_file"
              label="Planilha de cadastro"
              @click="abrirPlanilha"
            />
            <q-btn
              class="btn-exportar"
              color="positive"
              text-color="white"
              no-caps
              icon="download"
              label="Exportar planilha"
              :loading="baixando"
              @click="baixarPlanilha"
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
                  v-model="filtroBases"
                  :options="opcoesBases"
                  icon="place"
                  label="Base"
                />
              </div>

              <div class="col-12 col-sm-6 col-md">
                <SelectFiltroMultiplo
                  v-model="filtroSetores"
                  :options="opcoesSetores"
                  icon="apartment"
                  label="Setor"
                />
              </div>

              <div class="col-12 col-sm-6 col-md">
                <SelectFiltroMultiplo
                  v-model="filtroResponsaveis"
                  :options="opcoesResponsaveis"
                  icon="supervisor_account"
                  label="Responsável"
                />
              </div>

              <div class="col-12 col-sm-6 col-md">
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
            class="col-6 col-md-3"
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
          <div class="col-12 col-lg-8">
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
                    : 'Ninguém alocado ainda. Use "Alocar" na lista ao lado ou a planilha de cadastro.'
                }}
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <!--
                Um cartão por SETOR; dentro, uma seção por BASE; dentro da base,
                as pessoas agrupadas por RESPONSÁVEL (o responsável é por
                pessoa — pode haver mais de um no mesmo setor e base).
              -->
              <div
                v-for="grupo in gruposSetor"
                :key="grupo.nome"
                class="col-12 col-md-6"
              >
                <q-card class="cartao-setor">
                  <div class="cartao-setor__faixa" />

                  <q-card-section class="q-pb-sm">
                    <div class="row items-center no-wrap">
                      <div class="col">
                        <div class="cartao-setor__nome">{{ grupo.nome }}</div>
                        <div class="text-caption">
                          {{ grupo.bases.length }}
                          {{ grupo.bases.length === 1 ? 'base' : 'bases' }}
                        </div>
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
                      <div class="secao-base__cabecalho">
                        <q-chip dense class="chip-base q-ml-none" icon="place">
                          {{ secao.base }}
                        </q-chip>
                        <q-space />
                        <span class="secao-base__contagem">{{ secao.total }}</span>
                      </div>

                      <div
                        v-for="time in secao.responsaveis"
                        :key="time.chapa || 'sem'"
                        class="time-responsavel"
                      >
                        <button
                          type="button"
                          class="responsavel-chip"
                          @click="abrirTrocaResponsavel(time)"
                        >
                          <template v-if="time.responsavel">
                            <q-avatar size="24px" class="avatar-responsavel">
                              {{ iniciais(time.responsavel.nome) }}
                            </q-avatar>
                            <span class="responsavel-chip__texto">
                              <strong>{{ time.responsavel.nome }}</strong>
                              <small>{{ time.responsavel.chapa }}</small>
                            </span>
                          </template>
                          <span v-else class="sem-responsavel">Definir responsável</span>
                          <q-icon name="edit" size="14px" class="responsavel-chip__editar" />
                          <q-tooltip>
                            Responsável de {{ time.pessoas.length }}
                            {{ time.pessoas.length === 1 ? 'pessoa' : 'pessoas' }} · clique para trocar
                          </q-tooltip>
                        </button>

                        <q-list dense separator class="lista-pessoas">
                          <q-item
                            v-for="pessoa in time.pessoas"
                            :key="pessoa.chapa"
                            :class="{ 'linha-afastado': pessoa.afastado }"
                          >
                            <q-item-section avatar>
                              <q-avatar size="30px" class="avatar-pessoa">
                                {{ iniciais(pessoa.nome) }}
                              </q-avatar>
                            </q-item-section>

                            <q-item-section>
                              <q-item-label class="text-weight-medium">
                                {{ pessoa.nome }}
                              </q-item-label>
                              <q-item-label caption>
                                {{ pessoa.chapa }} · {{ pessoa.funcao }}
                              </q-item-label>
                              <q-item-label v-if="pessoa.alocacao.observacao" caption>
                                <q-icon name="notes" size="12px" />
                                {{ pessoa.alocacao.observacao }}
                              </q-item-label>
                            </q-item-section>

                            <q-item-section side>
                              <div class="row items-center no-wrap">
                                <q-chip
                                  v-if="pessoa.afastado"
                                  dense
                                  class="bg-afastado text-afastado"
                                  label="afastado"
                                />
                                <q-btn flat round dense icon="more_vert" size="sm">
                                  <q-menu auto-close>
                                    <q-list dense style="min-width: 190px">
                                      <q-item clickable @click="abrirAlocacao(pessoa)">
                                        <q-item-section avatar>
                                          <q-icon name="swap_horiz" />
                                        </q-item-section>
                                        <q-item-section>Mover / editar</q-item-section>
                                      </q-item>
                                      <q-item
                                        clickable
                                        @click="abrirTrocaResponsavel({ pessoas: [pessoa], responsavel: responsavelPorChapa(pessoa.alocacao.responsavel_chapa) })"
                                      >
                                        <q-item-section avatar>
                                          <q-icon name="supervisor_account" />
                                        </q-item-section>
                                        <q-item-section>Trocar responsável</q-item-section>
                                      </q-item>
                                      <q-item clickable @click="removerDoSetor(pessoa)">
                                        <q-item-section avatar>
                                          <q-icon name="person_remove" color="negative" />
                                        </q-item-section>
                                        <q-item-section>Tirar do setor</q-item-section>
                                      </q-item>
                                    </q-list>
                                  </q-menu>
                                </q-btn>
                              </div>
                            </q-item-section>
                          </q-item>
                        </q-list>
                      </div>
                    </div>
                  </div>

                  <q-card-actions>
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

          <!-- SEM SETOR -->
          <div class="col-12 col-lg-4">
            <q-card class="cartao-sem-setor">
              <q-card-section>
                <div class="row items-center">
                  <div class="text-h6">Sem setor</div>
                  <q-chip dense class="q-ml-sm bg-orange-1">
                    {{ semSetorFiltrados.length }}
                  </q-chip>
                </div>
                <div class="text-caption">
                  Indiretos ainda não alocados. Clique para escolher setor, base e
                  responsável.
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
                  <q-item-section avatar>
                    <q-avatar size="30px" class="avatar-pessoa">
                      {{ iniciais(pessoa.nome) }}
                    </q-avatar>
                  </q-item-section>

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
            <q-avatar size="38px" class="avatar-pessoa">
              {{ iniciais(pessoaAlocacao.nome) }}
            </q-avatar>
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
                <q-item-section avatar>
                  <q-avatar size="28px" class="avatar-pessoa">
                    {{ iniciais(scope.opt.nome) }}
                  </q-avatar>
                </q-item-section>
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
                <q-item-section avatar>
                  <q-avatar size="28px" class="avatar-responsavel">
                    {{ iniciais(scope.opt.nome) }}
                  </q-avatar>
                </q-item-section>
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
          <q-btn v-close-popup flat label="Cancelar" />
          <q-btn
            color="primary"
            label="Confirmar"
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
                <q-item-section avatar>
                  <q-avatar size="28px" class="avatar-responsavel">
                    {{ iniciais(scope.opt.nome) }}
                  </q-avatar>
                </q-item-section>
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
    <!-- PLANILHA DE CADASTRO -->
    <!-- ================================================== -->

    <q-dialog v-model="planilha.aberto">
      <q-card style="width: 640px; max-width: 94vw">
        <q-card-section class="row items-center">
          <q-icon name="upload_file" color="primary" size="26px" class="q-mr-sm" />
          <div class="text-h6">Planilha de cadastro</div>
          <q-space />
          <q-btn v-close-popup flat round dense icon="close" />
        </q-card-section>

        <q-separator />

        <q-card-section class="q-gutter-md">
          <div class="text-body2">
            Aloca, move ou troca o responsável de vários indiretos de uma vez. Uma
            linha por indireto. Quem não estiver na planilha continua onde está.
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
import { PODE_VER_EQUIPES } from '../composables/useSessao'
import { useConfirmacao } from '../composables/useConfirmacao'

// mesmas regras do Banco de Dados; enquanto a página está em liberação
// gradual, só o Administrador abre (ver router/index.js e indiretos.py)
definePage({ meta: { permissao: PODE_VER_EQUIPES, somenteAdministrador: true } })

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

function iniciais(nome) {
  const partes = String(nome || '').trim().split(/\s+/)
  return ((partes[0]?.[0] || '') + (partes.at(-1)?.[0] || '')).toUpperCase()
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

const filtroBases = ref([])
const filtroSetores = ref([])
const filtroResponsaveis = ref([])
const busca = ref('')
// clicar num indicador filtra por status; clicar de novo limpa
const filtroStatus = ref('')

const alocados = computed(() => pessoas.value.filter(p => p.alocacao))

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
const opcoesBases = computed(() => opcoesUnicas(alocados.value.map(p => p.alocacao.base)))
const opcoesSetores = computed(() => opcoesUnicas(nomesSetores.value))
const opcoesResponsaveis = computed(() =>
  [...new Set(alocados.value.map(p => p.alocacao.responsavel_chapa).filter(Boolean))]
    .map(chapa => ({ label: responsavelPorChapa(chapa)?.nome || chapa, value: chapa }))
    .sort((a, b) => a.label.localeCompare(b.label, 'pt-BR'))
)

function casaComBusca(pessoa) {
  const termo = (busca.value || '').trim().toLowerCase()
  if (!termo) return true
  return [pessoa.nome, pessoa.chapa, pessoa.funcao].some(valor =>
    String(valor || '').toLowerCase().includes(termo)
  )
}

function casaComStatus(pessoa) {
  if (filtroStatus.value === 'afastados') return Boolean(pessoa.afastado)
  if (filtroStatus.value === 'alocados') return Boolean(pessoa.alocacao)
  if (filtroStatus.value === 'semSetor') return !pessoa.alocacao
  return true
}

const alocadosFiltrados = computed(() =>
  alocados.value.filter(pessoa => {
    const a = pessoa.alocacao
    if (filtroBases.value?.length && !filtroBases.value.includes(a.base)) return false
    if (filtroSetores.value?.length && !filtroSetores.value.includes(a.setor)) return false
    if (
      filtroResponsaveis.value?.length &&
      !filtroResponsaveis.value.includes(a.responsavel_chapa)
    ) {
      return false
    }
    return casaComBusca(pessoa) && casaComStatus(pessoa)
  })
)

const semSetorFiltrados = computed(() =>
  pessoas.value.filter(
    pessoa =>
      !pessoa.alocacao &&
      filtroStatus.value !== 'alocados' &&
      casaComStatus(pessoa) &&
      !filtroSetores.value?.length &&
      !filtroResponsaveis.value?.length &&
      (!filtroBases.value?.length || filtroBases.value.includes(pessoa.base_cadastro)) &&
      casaComBusca(pessoa)
  )
)

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

  const porNome = (a, b) => a.nome.localeCompare(b.nome, 'pt-BR')

  return [...porSetor.entries()]
    .map(([nome, porBase]) => {
      const secoes = [...porBase.entries()]
        .map(([base, porResp]) => {
          const times = [...porResp.entries()]
            .map(([chapa, lista]) => ({
              chapa,
              responsavel: responsavelPorChapa(chapa),
              pessoas: lista.slice().sort(porNome)
            }))
            .sort((a, b) => b.pessoas.length - a.pessoas.length)
          return {
            base,
            responsaveis: times,
            total: times.reduce((soma, t) => soma + t.pessoas.length, 0)
          }
        })
        .sort((a, b) => a.base.localeCompare(b.base))
      return {
        nome,
        bases: secoes,
        total: secoes.reduce((soma, s) => soma + s.total, 0)
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
    valor: alocados.value.length
  },
  {
    chave: 'semSetor',
    rotulo: 'Sem setor',
    icone: 'person_search',
    valor: pessoas.value.length - alocados.value.length
  },
  {
    chave: 'afastados',
    rotulo: 'Afastados',
    icone: 'event_busy',
    valor: pessoas.value.filter(p => p.afastado).length
  }
])

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
  observacao: ''
})
const salvando = ref(false)
const termoPessoa = ref('')
const termoSetor = ref('')

const pessoaAlocacao = computed(() => pessoas.value.find(p => p.chapa === alocacao.chapa))

const tituloAlocacao = computed(() => {
  if (alocacao.modo === 'setor') return `Adicionar em ${alocacao.setor}`
  return pessoaAlocacao.value?.alocacao ? 'Mover / editar alocação' : 'Alocar em um setor'
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
  const atual = pessoa.alocacao
  Object.assign(alocacao, {
    aberto: true,
    modo: 'pessoa',
    chapa: pessoa.chapa,
    setor: atual?.setor || null,
    setorDigitado: '',
    base: atual?.base || null,
    responsavelChapa: atual?.responsavel_chapa || null,
    observacao: atual?.observacao || ''
  })
}

function abrirAdicionarNoSetor(nomeSetor) {
  termoPessoa.value = ''
  termoResponsavel.value = ''
  Object.assign(alocacao, {
    aberto: true,
    modo: 'setor',
    chapa: null,
    setor: nomeSetor,
    setorDigitado: '',
    base: null,
    responsavelChapa: null,
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
          observacao: alocacao.observacao
        })
      },
      'Não foi possível alocar.'
    )
    sucesso.value = `${pessoaAlocacao.value?.nome || 'Indireto'} alocado em ${setorEscolhido.value} · ${alocacao.base}.`
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
    await carregar()
  } catch (e) {
    erro.value = e.message
  }
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
  color: var(--marca-clara);
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
.cartao-setor {
  position: relative;
  overflow: hidden;
  height: 100%;
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
  color: var(--marca-clara);
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

.time-responsavel {
  padding: 8px 10px 0;
}

.time-responsavel + .time-responsavel {
  border-top: 1px dashed var(--linha);
}

.time-responsavel .lista-pessoas {
  margin: 6px -10px 0;
}

.lista-previa {
  max-height: 280px;
  overflow-y: auto;
}

.responsavel-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 8px 2px 2px;
  border: 1px solid var(--linha);
  border-radius: 999px;
  background: var(--superficie);
  color: var(--tinta);
  font: inherit;
  cursor: pointer;
  transition: border-color 0.14s ease, box-shadow 0.14s ease;
}

.responsavel-chip:hover,
.responsavel-chip:focus-visible {
  border-color: var(--linha-forte);
  box-shadow: 0 0 0 3px rgba(113, 20, 36, 0.1);
  outline: none;
}

.responsavel-chip__texto {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
  text-align: left;
}

.responsavel-chip__texto small {
  color: var(--tinta-fraca);
  font-size: 0.7rem;
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
  color: var(--marca-clara);
}

.sem-responsavel {
  color: var(--tinta-fraca);
  font-style: italic;
}

.secao-base__contagem {
  font-family: var(--fonte-ui);
  font-weight: 700;
  color: var(--marca-clara);
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
  color: var(--marca-clara);
}

.responsavel__rotulo {
  color: var(--tinta-fraca);
}

.lista-pessoas {
  flex: 1;
}

.avatar-pessoa {
  background: var(--realce);
  color: var(--marca-clara);
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
