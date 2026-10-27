<template>
  <q-layout view="lHh Lpr lFf">
    <MarcaDaguaFundo />

    <CabecalhoApp titulo="Indiretos" />

    <q-page-container>
      <q-page class="q-pa-md">
        <!-- ================================================== -->
        <!-- CABEÇALHO -->
        <!-- ================================================== -->

        <div class="row items-end q-col-gutter-md q-mb-md">
          <div class="col">
            <div class="text-h5">Alocação de Indiretos</div>
            <div class="text-subtitle2 text-grey-7">
              Controle nominal do pessoal indireto por setor e responsável
            </div>
          </div>

          <div class="col-auto row q-gutter-sm">
            <q-btn
              outline
              no-caps
              color="primary"
              icon="upload_file"
              label="Planilha de cadastro"
              @click="dialogPlanilha = true"
            />
            <q-btn
              class="btn-exportar"
              color="positive"
              text-color="white"
              no-caps
              icon="download"
              label="Exportar planilha"
            />
          </div>
        </div>

        <!-- PRÉVIA: some quando a página for ligada ao banco -->
        <q-banner rounded dense class="bg-blue-1 q-mb-md aviso-previa">
          <template #avatar>
            <q-icon name="science" color="primary" />
          </template>
          Pré-visualização com <strong>dados de exemplo</strong>. Pode clicar à
          vontade: nada é gravado no banco.
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

        <div class="row q-col-gutter-md">
          <!-- SETORES -->
          <div class="col-12 col-lg-8">
            <div class="row items-center q-mb-sm">
              <div class="text-h6">Setores</div>
              <q-chip dense class="q-ml-sm">{{ gruposSetor.length }}</q-chip>
            </div>

            <div v-if="!gruposSetor.length" class="estado-vazio">
              <q-icon name="search_off" size="40px" />
              <div>Nenhum setor com esses filtros.</div>
            </div>

            <div class="row q-col-gutter-md">
              <!--
                Um cartão por NOME de setor. O mesmo setor em várias bases
                (Almoxarifado em BCB e PDT, por exemplo) fica num cartão só,
                com uma seção por base — cada base tem o próprio responsável.
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
                          {{ grupo.unidades.length }}
                          {{ grupo.unidades.length === 1 ? 'base' : 'bases' }}
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
                    <div
                      v-for="unidade in grupo.unidades"
                      :key="unidade.id"
                      class="secao-base"
                    >
                      <div class="secao-base__cabecalho">
                        <q-chip dense class="chip-base q-ml-none" icon="place">
                          {{ unidade.base }}
                        </q-chip>

                        <button
                          type="button"
                          class="responsavel-chip"
                          @click="abrirTrocaResponsavel(unidade)"
                        >
                          <template v-if="responsavelDe(unidade)">
                            <q-avatar size="24px" class="avatar-responsavel">
                              {{ iniciais(responsavelDe(unidade).nome) }}
                            </q-avatar>
                            <span class="responsavel-chip__texto">
                              <strong>{{ responsavelDe(unidade).nome }}</strong>
                              <small>{{ responsavelDe(unidade).chapa }}</small>
                            </span>
                          </template>
                          <span v-else class="sem-responsavel">Definir responsável</span>
                          <q-icon name="edit" size="14px" class="responsavel-chip__editar" />
                          <q-tooltip>Responsável desta base · clique para trocar</q-tooltip>
                        </button>

                        <q-space />

                        <span class="secao-base__contagem">
                          {{ pessoasDoSetor(unidade.id).length }}
                        </span>
                      </div>

                      <q-list dense separator class="lista-pessoas">
                        <q-item
                          v-for="pessoa in pessoasVisiveisDoSetor(unidade.id)"
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
                                  <q-list dense style="min-width: 180px">
                                    <q-item clickable @click="abrirAlocacao(pessoa)">
                                      <q-item-section avatar>
                                        <q-icon name="swap_horiz" />
                                      </q-item-section>
                                      <q-item-section>Mover de setor</q-item-section>
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

                        <q-item v-if="!pessoasDoSetor(unidade.id).length">
                          <q-item-section class="text-grey-7 text-center q-py-xs">
                            Ninguém alocado nesta base ainda.
                          </q-item-section>
                        </q-item>
                      </q-list>
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
                  Indiretos ainda não alocados. Clique para escolher o setor.
                </div>
              </q-card-section>

              <q-separator />

              <q-list separator class="lista-sem-setor">
                <q-item
                  v-for="pessoa in semSetorFiltrados"
                  :key="pessoa.chapa"
                  clickable
                  :disable="pessoa.afastado"
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
                      {{ pessoa.chapa }} · {{ pessoa.funcao }} · {{ pessoa.base }}
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
                    Todos os indiretos estão alocados.
                  </q-item-section>
                </q-item>
              </q-list>
            </q-card>
          </div>
        </div>
      </q-page>
    </q-page-container>

    <!-- ================================================== -->
    <!-- ALOCAR (pessoa + setor + base + responsável) -->
    <!-- ================================================== -->

    <q-dialog v-model="alocacao.aberto">
      <q-card style="width: 500px; max-width: 94vw">
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
          <!-- PESSOA: fixa quando veio da lista, escolhida quando veio do setor -->
          <div v-if="alocacao.modo === 'pessoa' && pessoaAlocacao" class="pessoa-fixa">
            <q-avatar size="38px" class="avatar-pessoa">
              {{ iniciais(pessoaAlocacao.nome) }}
            </q-avatar>
            <div class="q-ml-sm">
              <div class="text-weight-medium">{{ pessoaAlocacao.nome }}</div>
              <div class="text-caption">
                {{ pessoaAlocacao.chapa }} · {{ pessoaAlocacao.funcao }} · cadastro em
                {{ pessoaAlocacao.base }}
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
                <q-item-section class="text-grey-7">Ninguém encontrado</q-item-section>
              </q-item>
            </template>
          </q-select>

          <div class="row q-col-gutter-sm">
            <div class="col-12 col-sm-7">
              <q-select
                v-model="alocacao.nomeSetor"
                outlined
                dense
                label="Setor *"
                :options="nomesSetores"
                :readonly="alocacao.modo === 'setor'"
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
                :options="BASES"
                hint="Você escolhe, independente do cadastro"
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
          </q-select>

          <q-banner v-if="avisoAlocacao" dense rounded :class="avisoAlocacao.classe">
            <template #avatar>
              <q-icon :name="avisoAlocacao.icone" />
            </template>
            {{ avisoAlocacao.texto }}
          </q-banner>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Cancelar" />
          <q-btn
            color="primary"
            label="Confirmar"
            :disable="!alocacaoCompleta"
            @click="confirmarAlocacao"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ================================================== -->
    <!-- TROCAR RESPONSÁVEL DE UMA SEÇÃO (setor numa base) -->
    <!-- ================================================== -->

    <q-dialog v-model="trocaResponsavel.aberto">
      <q-card style="width: 440px; max-width: 94vw">
        <q-card-section class="row items-center">
          <q-icon name="supervisor_account" color="primary" size="26px" class="q-mr-sm" />
          <div class="text-h6">Responsável</div>
          <q-space />
          <q-btn v-close-popup flat round dense icon="close" />
        </q-card-section>

        <q-separator />

        <q-card-section v-if="trocaResponsavel.unidade" class="q-gutter-md">
          <div class="row items-center q-gutter-sm">
            <span class="cartao-setor__nome texto-medio">
              {{ trocaResponsavel.unidade.nome }}
            </span>
            <q-chip dense class="chip-base" icon="place">
              {{ trocaResponsavel.unidade.base }}
            </q-chip>
          </div>

          <q-select
            v-model="trocaResponsavel.chapa"
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
          </q-select>

          <div class="text-caption">Vale para todas as pessoas desta seção.</div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Cancelar" />
          <q-btn
            color="primary"
            label="Salvar"
            :disable="!trocaResponsavel.chapa"
            @click="salvarResponsavel"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ================================================== -->
    <!-- PLANILHA DE CADASTRO -->
    <!-- ================================================== -->

    <q-dialog v-model="dialogPlanilha">
      <q-card style="width: 560px; max-width: 94vw">
        <q-card-section class="row items-center">
          <q-icon name="upload_file" color="primary" size="26px" class="q-mr-sm" />
          <div class="text-h6">Planilha de cadastro</div>
          <q-space />
          <q-btn v-close-popup flat round dense icon="close" />
        </q-card-section>

        <q-separator />

        <q-card-section class="q-gutter-md">
          <div class="text-body2">
            Cadastra setores, responsáveis e alocações de uma vez. Uma linha por
            indireto:
          </div>

          <q-markup-table flat bordered dense class="tabela-modelo">
            <thead>
              <tr>
                <th>SETOR</th>
                <th>BASE</th>
                <th>CHAPA RESPONSÁVEL</th>
                <th>CHAPA INDIRETO</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Almoxarifado</td>
                <td>BCB</td>
                <td>20010</td>
                <td>10021</td>
              </tr>
              <tr>
                <td>Almoxarifado</td>
                <td>PDT</td>
                <td>20015</td>
                <td>10070</td>
              </tr>
            </tbody>
          </q-markup-table>

          <div class="text-caption">
            Antes de aplicar, o sistema mostra uma prévia do que muda, igual às
            planilhas de equipes e de colaboradores.
          </div>

          <div class="row q-col-gutter-sm items-center">
            <div class="col-12 col-sm-auto">
              <q-btn outline no-caps color="primary" icon="download" label="Baixar modelo" />
            </div>
            <div class="col">
              <q-file
                v-model="arquivoPlanilha"
                outlined
                dense
                clearable
                accept=".xlsx"
                label="Escolher planilha (.xlsx)"
              >
                <template #prepend><q-icon name="attach_file" /></template>
              </q-file>
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Fechar" />
          <q-btn color="primary" label="Analisar" :disable="!arquivoPlanilha" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-layout>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'

import CabecalhoApp from '../components/CabecalhoApp.vue'
import MarcaDaguaFundo from '../components/MarcaDaguaFundo.vue'
import SelectFiltroMultiplo from '../components/SelectFiltroMultiplo.vue'
import { PODE_VER_EQUIPES } from '../composables/useSessao'
import { useConfirmacao } from '../composables/useConfirmacao'

// mesmas regras do Banco de Dados; enquanto a página está em liberação
// gradual, só o Administrador abre (ver router/index.js)
definePage({ meta: { permissao: PODE_VER_EQUIPES, somenteAdministrador: true } })

const { confirmar } = useConfirmacao()

// ============================================================
// DADOS DE EXEMPLO (prévia do layout — trocados pela API depois)
// ============================================================

const BASES = ['BCB', 'BDC', 'ITM', 'PDS', 'PDT', 'STI']

// quem pode ser responsável por um setor numa base (virá da planilha de
// cadastro)
const responsaveis = ref([
  { chapa: '20010', nome: 'Carlos Mendes', funcao: 'SUPERVISOR ADMINISTRATIVO' },
  { chapa: '20011', nome: 'Ana Ribeiro', funcao: 'COORDENADORA DE FROTA' },
  { chapa: '20012', nome: 'Paulo Sousa', funcao: 'ENGENHEIRO DE SEGURANÇA' },
  { chapa: '20013', nome: 'Juliana Costa', funcao: 'SUPERVISORA ADMINISTRATIVA' },
  { chapa: '20014', nome: 'Fernanda Rocha', funcao: 'COORDENADORA DE PLANEJAMENTO' },
  { chapa: '20015', nome: 'Marcos Lima', funcao: 'SUPERVISOR DE ALMOXARIFADO' }
])

// cada linha é uma SEÇÃO: um setor numa base, com o responsável dela
const setores = ref([
  { id: 1, nome: 'Almoxarifado', base: 'BCB', responsavelChapa: '20010' },
  { id: 2, nome: 'Frota', base: 'BCB', responsavelChapa: '20011' },
  { id: 3, nome: 'Segurança do Trabalho', base: 'BCB', responsavelChapa: '20012' },
  { id: 4, nome: 'Administrativo', base: 'PDT', responsavelChapa: '20013' },
  { id: 6, nome: 'Planejamento', base: 'ITM', responsavelChapa: '20014' }
])

const pessoas = ref([
  { chapa: '10021', nome: 'João Pereira', funcao: 'ALMOXARIFE', base: 'BCB', setorId: 1 },
  { chapa: '10022', nome: 'Rita Alves', funcao: 'AUXILIAR DE ALMOXARIFADO', base: 'BCB', setorId: 1 },
  { chapa: '10035', nome: 'Bruno Dias', funcao: 'ALMOXARIFE', base: 'BCB', setorId: 1, afastado: true },
  { chapa: '10040', nome: 'Lucas Martins', funcao: 'ASSISTENTE DE FROTA', base: 'BCB', setorId: 2 },
  { chapa: '10041', nome: 'Patrícia Gomes', funcao: 'ANALISTA DE FROTA', base: 'BCB', setorId: 2 },
  { chapa: '10050', nome: 'Diego Santos', funcao: 'TÉCNICO DE SEGURANÇA', base: 'BCB', setorId: 3 },
  { chapa: '10060', nome: 'Camila Nunes', funcao: 'ASSISTENTE ADMINISTRATIVO', base: 'PDT', setorId: 4 },
  { chapa: '10061', nome: 'Rafael Teixeira', funcao: 'AUXILIAR ADMINISTRATIVO', base: 'PDT', setorId: 4 },
  { chapa: '10062', nome: 'Larissa Prado', funcao: 'RECEPCIONISTA', base: 'PDT', setorId: 4 },
  { chapa: '10070', nome: 'Gustavo Freitas', funcao: 'ALMOXARIFE', base: 'PDT', setorId: null },
  { chapa: '10080', nome: 'Beatriz Moura', funcao: 'PROGRAMADORA DE OBRAS', base: 'ITM', setorId: null },
  { chapa: '10081', nome: 'Thiago Barros', funcao: 'ASSISTENTE DE PLANEJAMENTO', base: 'ITM', setorId: null },
  { chapa: '10090', nome: 'Vanessa Cardoso', funcao: 'TÉCNICA DE SEGURANÇA', base: 'BCB', setorId: null, afastado: true }
])

function responsavelDe(unidade) {
  return responsaveis.value.find(r => r.chapa === unidade?.responsavelChapa) || null
}

function iniciais(nome) {
  const partes = String(nome || '').trim().split(/\s+/)
  return ((partes[0]?.[0] || '') + (partes.at(-1)?.[0] || '')).toUpperCase()
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

function opcoesUnicas(valores) {
  return [...new Set(valores)].sort().map(valor => ({ label: valor, value: valor }))
}

const nomesSetores = computed(() => [...new Set(setores.value.map(s => s.nome))].sort())
const opcoesBases = computed(() => opcoesUnicas(setores.value.map(s => s.base)))
const opcoesSetores = computed(() => opcoesUnicas(nomesSetores.value))
const opcoesResponsaveis = computed(() =>
  responsaveis.value
    .filter(r => setores.value.some(s => s.responsavelChapa === r.chapa))
    .map(r => ({ label: r.nome, value: r.chapa }))
)

function casaComBusca(pessoa) {
  const termo = (busca.value || '').trim().toLowerCase()
  if (!termo) return true
  return [pessoa.nome, pessoa.chapa, pessoa.funcao].some(valor =>
    String(valor).toLowerCase().includes(termo)
  )
}

function casaComStatus(pessoa) {
  if (filtroStatus.value === 'afastados') return Boolean(pessoa.afastado)
  if (filtroStatus.value === 'alocados') return Boolean(pessoa.setorId)
  if (filtroStatus.value === 'semSetor') return !pessoa.setorId
  return true
}

const setoresFiltrados = computed(() =>
  setores.value.filter(setor => {
    if (filtroStatus.value === 'semSetor') return false
    if (filtroBases.value?.length && !filtroBases.value.includes(setor.base)) return false
    if (filtroSetores.value?.length && !filtroSetores.value.includes(setor.nome)) return false
    if (
      filtroResponsaveis.value?.length &&
      !filtroResponsaveis.value.includes(setor.responsavelChapa)
    ) {
      return false
    }
    // com busca ou status ativos, só aparecem seções com alguém que case
    if ((busca.value || '').trim() || filtroStatus.value) {
      return pessoasVisiveisDoSetor(setor.id).length > 0
    }
    return true
  })
)

const semSetorFiltrados = computed(() =>
  pessoas.value.filter(
    pessoa =>
      !pessoa.setorId &&
      (filtroStatus.value === '' ||
        filtroStatus.value === 'semSetor' ||
        filtroStatus.value === 'afastados') &&
      casaComStatus(pessoa) &&
      (!filtroBases.value?.length || filtroBases.value.includes(pessoa.base)) &&
      casaComBusca(pessoa)
  )
)

// Um grupo por nome de setor, com as bases dele dentro ("unidades": cada
// unidade é o setor numa base, com o próprio responsável).
const gruposSetor = computed(() => {
  const porNome = new Map()
  for (const unidade of setoresFiltrados.value) {
    if (!porNome.has(unidade.nome)) {
      porNome.set(unidade.nome, { nome: unidade.nome, unidades: [] })
    }
    porNome.get(unidade.nome).unidades.push(unidade)
  }
  return [...porNome.values()]
    .map(grupo => ({
      ...grupo,
      unidades: grupo.unidades.sort((a, b) => a.base.localeCompare(b.base)),
      total: grupo.unidades.reduce((soma, u) => soma + pessoasDoSetor(u.id).length, 0)
    }))
    .sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'))
})

function pessoasDoSetor(setorId) {
  return pessoas.value.filter(pessoa => pessoa.setorId === setorId)
}

function pessoasVisiveisDoSetor(setorId) {
  return pessoasDoSetor(setorId).filter(
    pessoa => casaComBusca(pessoa) && casaComStatus(pessoa)
  )
}

// ============================================================
// INDICADORES
// ============================================================

const indicadores = computed(() => [
  { chave: '', rotulo: 'Indiretos', icone: 'groups', valor: pessoas.value.length },
  {
    chave: 'alocados',
    rotulo: 'Alocados',
    icone: 'how_to_reg',
    valor: pessoas.value.filter(p => p.setorId).length
  },
  {
    chave: 'semSetor',
    rotulo: 'Sem setor',
    icone: 'person_search',
    valor: pessoas.value.filter(p => !p.setorId).length
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
// RESPONSÁVEL: campo de seleção (dois diálogos usam)
// ============================================================

// pesquisa por nome ou chapa; a opção mostra iniciais, chapa e função para
// não haver dúvida entre homônimos
const termoResponsavel = ref('')

const opcoesResponsavelSelect = computed(() => {
  const termo = termoResponsavel.value.toLowerCase()
  return responsaveis.value
    .filter(r => !termo || `${r.nome} ${r.chapa}`.toLowerCase().includes(termo))
    .map(r => ({ label: `${r.nome} (${r.chapa})`, value: r.chapa, ...r }))
})

function filtrarResponsaveis(termo, atualizar) {
  atualizar(() => {
    termoResponsavel.value = termo || ''
  })
}

// ============================================================
// ALOCAR / MOVER / ADICIONAR (só na tela, enquanto é prévia)
// ============================================================

// modo 'pessoa': veio da lista (pessoa fixa, escolhe o setor)
// modo 'setor': veio do botão do cartão (setor fixo, escolhe a pessoa)
const alocacao = reactive({
  aberto: false,
  modo: 'pessoa',
  chapa: null,
  nomeSetor: null,
  base: null,
  responsavelChapa: null
})
const termoPessoa = ref('')

const pessoaAlocacao = computed(() => pessoas.value.find(p => p.chapa === alocacao.chapa))

const tituloAlocacao = computed(() => {
  if (alocacao.modo === 'setor') return `Adicionar em ${alocacao.nomeSetor}`
  return pessoaAlocacao.value?.setorId ? 'Mover de setor' : 'Alocar em um setor'
})

const opcoesPessoas = computed(() => {
  const termo = termoPessoa.value.toLowerCase()
  return pessoas.value
    .filter(p => !p.setorId && !p.afastado)
    .filter(p => !termo || `${p.nome} ${p.chapa}`.toLowerCase().includes(termo))
    .map(p => ({ label: `${p.nome} (${p.chapa})`, value: p.chapa, nome: p.nome, funcao: p.funcao }))
})

function filtrarPessoas(termo, atualizar) {
  atualizar(() => {
    termoPessoa.value = termo || ''
  })
}

// a seção (setor + base) escolhida, se já existir
const unidadeEscolhida = computed(() =>
  setores.value.find(s => s.nome === alocacao.nomeSetor && s.base === alocacao.base)
)

// seção existente já tem responsável: o campo vem preenchido com ele
watch(unidadeEscolhida, unidade => {
  alocacao.responsavelChapa = unidade?.responsavelChapa || null
})

const alocacaoCompleta = computed(() =>
  Boolean(alocacao.chapa && alocacao.nomeSetor && alocacao.base && alocacao.responsavelChapa)
)

const avisoAlocacao = computed(() => {
  if (!alocacao.nomeSetor || !alocacao.base) return null
  const unidade = unidadeEscolhida.value
  if (!unidade) {
    return {
      classe: 'bg-blue-1',
      icone: 'add_circle',
      texto: `${alocacao.nomeSetor} ainda não tem a base ${alocacao.base}: a seção será criada com o responsável escolhido.`
    }
  }
  if (alocacao.responsavelChapa && alocacao.responsavelChapa !== unidade.responsavelChapa) {
    return {
      classe: 'bg-orange-1',
      icone: 'warning',
      texto: `Isso troca o responsável de toda a seção ${unidade.nome} · ${unidade.base}.`
    }
  }
  return null
})

function abrirAlocacao(pessoa) {
  termoResponsavel.value = ''
  Object.assign(alocacao, {
    aberto: true,
    modo: 'pessoa',
    chapa: pessoa.chapa,
    nomeSetor: null,
    base: null,
    responsavelChapa: null
  })
}

function abrirAdicionarNoSetor(nomeSetor) {
  termoPessoa.value = ''
  termoResponsavel.value = ''
  Object.assign(alocacao, {
    aberto: true,
    modo: 'setor',
    chapa: null,
    nomeSetor,
    base: null,
    responsavelChapa: null
  })
}

function confirmarAlocacao() {
  let unidade = unidadeEscolhida.value
  if (!unidade) {
    unidade = {
      id: Math.max(0, ...setores.value.map(s => s.id)) + 1,
      nome: alocacao.nomeSetor,
      base: alocacao.base,
      responsavelChapa: alocacao.responsavelChapa
    }
    setores.value.push(unidade)
  } else {
    unidade.responsavelChapa = alocacao.responsavelChapa
  }
  pessoaAlocacao.value.setorId = unidade.id
  alocacao.aberto = false
}

async function removerDoSetor(pessoa) {
  const setor = setores.value.find(s => s.id === pessoa.setorId)
  if (
    !(await confirmar(`Tirar ${pessoa.nome} do setor ${setor?.nome} (${setor?.base})?`, {
      textoConfirmar: 'Tirar do setor'
    }))
  ) {
    return
  }
  pessoa.setorId = null
}

// ============================================================
// RESPONSÁVEL DA SEÇÃO
// ============================================================

const trocaResponsavel = reactive({ aberto: false, unidade: null, chapa: null })

function abrirTrocaResponsavel(unidade) {
  termoResponsavel.value = ''
  Object.assign(trocaResponsavel, {
    aberto: true,
    unidade,
    chapa: unidade.responsavelChapa
  })
}

function salvarResponsavel() {
  trocaResponsavel.unidade.responsavelChapa = trocaResponsavel.chapa
  trocaResponsavel.aberto = false
}

// ============================================================
// PLANILHA DE CADASTRO (layout — ligação ao backend depois)
// ============================================================

const dialogPlanilha = ref(false)
const arquivoPlanilha = ref(null)
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
