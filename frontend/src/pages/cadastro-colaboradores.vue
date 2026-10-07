<template>
  <q-layout view="lHh Lpr lFf">
    <MarcaDaguaFundo />

    <CabecalhoApp
      titulo="Cadastro de Colaboradores"
      :carregando="carregando"
      @atualizar="carregarColaboradores"
    />

    <q-page-container>
      <q-page class="q-pa-md">
        <div class="q-mb-md">
          <div class="text-h5"> Cadastro de Colaboradores </div>

          <div class="text-subtitle2 text-grey-7">
            Inclua, edite ou remova colaboradores um a um, ou atualize o
            cadastro inteiro por planilha. Exclusivo do Administrador.
          </div>
        </div>

        <q-banner v-if="erro" class="bg-red-1 text-negative q-mb-md" rounded>
          {{ erro }}
        </q-banner>

        <q-banner v-if="sucesso" class="bg-green-1 text-positive q-mb-md" rounded>
          {{ sucesso }}
        </q-banner>

        <!-- ================================================== -->
        <!-- IMPORTAÇÃO POR PLANILHA -->
        <!-- ================================================== -->

        <ImportacaoColaboradores class="q-mb-md" @importado="carregarColaboradores" />

        <!-- ================================================== -->
        <!-- LISTA DE COLABORADORES -->
        <!-- ================================================== -->

        <q-card bordered>
          <q-card-section>
            <div class="row items-center q-col-gutter-sm">
              <div class="col-12 col-md-auto">
                <div class="text-h6"> Colaboradores ({{ colaboradoresFiltrados.length }}) </div>
              </div>

              <div class="col-12 col-md">
                <q-input
                  v-model="filtro"
                  outlined
                  dense
                  clearable
                  placeholder="Nome, chapa, função, seção..."
                >
                  <template #prepend>
                    <q-icon name="search" />
                  </template>
                </q-input>
              </div>

              <div class="col-auto">
                <q-btn-toggle
                  v-model="filtroTipoFuncao"
                  dense
                  no-caps
                  toggle-color="primary"
                  :options="[
                    { label: 'Todos', value: '' },
                    { label: 'Diretos', value: 'DIRETO' },
                    { label: 'Indiretos', value: 'INDIRETO' }
                  ]"
                />
              </div>

              <div class="col-12 col-md-auto">
                <q-btn
                  color="primary"
                  icon="person_add"
                  label="Novo colaborador"
                  @click="abrirNovo"
                />
              </div>
            </div>
          </q-card-section>

          <q-separator />

          <q-table
            flat
            dense
            :rows="colaboradoresFiltrados"
            :columns="colunas"
            row-key="chapa"
            :loading="carregando"
            v-model:pagination="paginacao"
            :rows-per-page-options="[25, 50, 100]"
            no-data-label="Nenhum colaborador encontrado"
            rows-per-page-label="Linhas por página"
          >
            <template #body-cell-status="props">
              <q-td :props="props">
                <q-badge v-if="props.row.afastado" color="amber-8" label="Afastado" />
                <q-badge v-else-if="props.row.alocado" color="positive" label="Alocado" />
                <q-badge v-else color="grey-6" label="Livre" />
              </q-td>
            </template>

            <template #body-cell-acoes="props">
              <q-td :props="props" auto-width>
                <q-btn
                  flat
                  dense
                  round
                  color="primary"
                  icon="edit"
                  @click="abrirEdicao(props.row)"
                >
                  <q-tooltip>Editar</q-tooltip>
                </q-btn>

                <q-btn
                  flat
                  dense
                  round
                  color="negative"
                  icon="delete"
                  @click="remover(props.row)"
                >
                  <q-tooltip>Remover</q-tooltip>
                </q-btn>
              </q-td>
            </template>
          </q-table>
        </q-card>

        <!-- ================================================== -->
        <!-- FORMULÁRIO -->
        <!-- ================================================== -->

        <q-dialog v-model="dialogAberto">
          <q-card class="cartao-formulario">
            <q-card-section class="row items-center q-py-sm">
              <div class="text-h6">
                {{ editando ? 'Editar colaborador' : 'Novo colaborador' }}
              </div>
              <q-space />
              <q-btn v-close-popup flat round dense icon="close" />
            </q-card-section>

            <q-separator />

            <q-card-section class="corpo-formulario q-gutter-md">
              <q-banner v-if="erroFormulario" class="bg-red-1 text-negative" rounded dense>
                {{ erroFormulario }}
              </q-banner>

              <q-input v-model="formulario.chapa" outlined dense label="Chapa *" />

              <q-input v-model="formulario.nome" outlined dense label="Nome *" />

              <q-input v-model="formulario.funcao" outlined dense label="Função" />

              <div>
                <div class="text-caption text-grey-7 q-mb-xs">Tipo de função *</div>
                <q-btn-toggle
                  v-model="formulario.tipo_funcao"
                  dense
                  no-caps
                  toggle-color="primary"
                  :options="[
                    { label: 'Direto', value: 'DIRETO' },
                    { label: 'Indireto', value: 'INDIRETO' }
                  ]"
                />
              </div>

              <q-input v-model="formulario.secao" outlined dense label="Seção" />

              <q-input v-model="formulario.situacao" outlined dense label="Situação" />

              <q-input
                v-model="formulario.admissao"
                outlined
                dense
                type="date"
                stack-label
                label="Admissão"
              />

              <div>
                <div class="row items-center q-mb-xs">
                  <div class="text-caption text-grey-7">Rateios</div>
                  <q-space />
                  <q-btn
                    flat
                    dense
                    no-caps
                    size="sm"
                    color="primary"
                    icon="add"
                    label="Adicionar rateio"
                    @click="formulario.rateios.push({ rateio: '', grpccusto: '' })"
                  />
                </div>

                <div v-if="!formulario.rateios.length" class="text-caption text-grey-6">
                  Nenhum rateio informado.
                </div>

                <div
                  v-for="(item, indice) in formulario.rateios"
                  :key="indice"
                  class="row q-col-gutter-sm items-center q-mb-xs"
                >
                  <div class="col">
                    <q-input v-model="item.rateio" outlined dense label="Rateio" />
                  </div>

                  <div class="col">
                    <q-input v-model="item.grpccusto" outlined dense label="Grupo de custo" />
                  </div>

                  <div class="col-auto">
                    <q-btn
                      flat
                      dense
                      round
                      color="negative"
                      icon="close"
                      @click="formulario.rateios.splice(indice, 1)"
                    />
                  </div>
                </div>

                <div class="text-caption text-grey-6 q-mt-xs">
                  Ao salvar, os rateios acima substituem os que o colaborador
                  tinha, e a seção tratada e o tipo de ccusto são recalculados.
                </div>
              </div>
            </q-card-section>

            <q-separator />

            <q-card-actions align="right" class="q-py-sm">
              <q-btn v-close-popup flat dense label="Cancelar" />

              <q-btn
                dense
                color="primary"
                :label="editando ? 'Salvar' : 'Cadastrar'"
                :loading="salvando"
                @click="salvar"
              />
            </q-card-actions>
          </q-card>
        </q-dialog>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import CabecalhoApp from '../components/CabecalhoApp.vue'
import ImportacaoColaboradores from '../components/ImportacaoColaboradores.vue'
import MarcaDaguaFundo from '../components/MarcaDaguaFundo.vue'
import { PODE_GERENCIAR_COLABORADORES } from '../composables/useSessao'
import { useConfirmacao } from '../composables/useConfirmacao'

definePage({ meta: { permissao: PODE_GERENCIAR_COLABORADORES } })

const { confirmar } = useConfirmacao()

const colaboradores = ref([])
const carregando = ref(false)
const erro = ref('')
const sucesso = ref('')

const filtro = ref('')
const filtroTipoFuncao = ref('')
const paginacao = ref({ page: 1, rowsPerPage: 25 })

function limparAvisos() {
  erro.value = ''
  sucesso.value = ''
}

// ------------------------------------------------------------
// Lista
// ------------------------------------------------------------

function dataBr(iso) {
  if (!iso) {
    return '—'
  }

  const [ano, mes, dia] = iso.split('-')
  return `${dia}/${mes}/${ano}`
}

const colunas = [
  { name: 'chapa', label: 'CHAPA', field: 'chapa', align: 'left', sortable: true },
  { name: 'nome', label: 'NOME', field: 'nome', align: 'left', sortable: true },
  {
    name: 'funcao',
    label: 'FUNÇÃO',
    field: 'funcao',
    align: 'left',
    sortable: true,
    format: valor => valor || '—'
  },
  {
    name: 'tipo_funcao',
    label: 'TIPO',
    field: 'tipo_funcao',
    align: 'left',
    sortable: true
  },
  {
    name: 'secao',
    label: 'SEÇÃO',
    field: row => row.secao_tratada || row.secao,
    align: 'left',
    sortable: true,
    format: valor => valor || '—'
  },
  {
    name: 'situacao',
    label: 'SITUAÇÃO',
    field: 'situacao',
    align: 'left',
    sortable: true,
    format: valor => valor || '—'
  },
  {
    name: 'admissao',
    label: 'ADMISSÃO',
    field: 'admissao',
    align: 'left',
    sortable: true,
    format: dataBr
  },
  {
    name: 'rateios',
    label: 'RATEIOS',
    field: row => row.rateios.map(item => item.rateio).join(' / '),
    align: 'left',
    format: valor => valor || '—'
  },
  { name: 'status', label: 'STATUS', field: 'alocado', align: 'center' },
  { name: 'acoes', label: '', field: 'chapa', align: 'right' }
]

function semAcento(texto) {
  return String(texto || '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
}

const colaboradoresFiltrados = computed(() => {
  const termo = semAcento(filtro.value).trim()

  return colaboradores.value.filter(colaborador => {
    if (filtroTipoFuncao.value && colaborador.tipo_funcao !== filtroTipoFuncao.value) {
      return false
    }

    if (!termo) {
      return true
    }

    return semAcento(
      [
        colaborador.chapa,
        colaborador.nome,
        colaborador.funcao,
        colaborador.secao,
        colaborador.secao_tratada,
        colaborador.situacao,
        colaborador.rateios.map(item => item.rateio).join(' ')
      ].join(' ')
    ).includes(termo)
  })
})

async function carregarColaboradores() {
  carregando.value = true
  erro.value = ''

  try {
    const resposta = await fetch('/api/colaboradores/cadastro')
    const dados = await resposta.json()

    if (!resposta.ok || dados.erro) {
      throw new Error(dados.erro || 'Erro ao carregar os colaboradores.')
    }

    colaboradores.value = dados
  } catch (e) {
    erro.value = e.message || 'Erro ao carregar os colaboradores.'
  } finally {
    carregando.value = false
  }
}

// ------------------------------------------------------------
// Formulário (novo / editar)
// ------------------------------------------------------------

const dialogAberto = ref(false)
const editando = ref(false)
const chapaOriginal = ref('')
const salvando = ref(false)
const erroFormulario = ref('')

const formulario = reactive({
  chapa: '',
  nome: '',
  funcao: '',
  tipo_funcao: 'DIRETO',
  secao: '',
  situacao: '',
  admissao: '',
  rateios: []
})

function preencher(colaborador) {
  formulario.chapa = colaborador?.chapa || ''
  formulario.nome = colaborador?.nome || ''
  formulario.funcao = colaborador?.funcao || ''
  formulario.tipo_funcao = colaborador?.tipo_funcao || 'DIRETO'
  formulario.secao = colaborador?.secao || ''
  formulario.situacao = colaborador?.situacao || ''
  formulario.admissao = colaborador?.admissao || ''
  formulario.rateios = (colaborador?.rateios || []).map(item => ({ ...item }))
}

function abrirNovo() {
  limparAvisos()
  erroFormulario.value = ''
  editando.value = false
  chapaOriginal.value = ''
  preencher(null)
  dialogAberto.value = true
}

function abrirEdicao(colaborador) {
  limparAvisos()
  erroFormulario.value = ''
  editando.value = true
  chapaOriginal.value = colaborador.chapa
  preencher(colaborador)
  dialogAberto.value = true
}

async function salvar() {
  erroFormulario.value = ''
  salvando.value = true

  try {
    const corpo = {
      chapa: formulario.chapa.trim(),
      nome: formulario.nome.trim(),
      funcao: formulario.funcao.trim(),
      tipo_funcao: formulario.tipo_funcao,
      secao: formulario.secao.trim(),
      situacao: formulario.situacao.trim(),
      admissao: formulario.admissao,
      rateios: formulario.rateios
    }

    const resposta = await fetch(
      editando.value
        ? `/api/colaboradores/cadastro/${encodeURIComponent(chapaOriginal.value)}`
        : '/api/colaboradores/cadastro',
      {
        method: editando.value ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(corpo)
      }
    )

    const dados = await resposta.json()

    if (!resposta.ok || dados.erro) {
      throw new Error(dados.erro || 'Não foi possível salvar o colaborador.')
    }

    dialogAberto.value = false
    sucesso.value = editando.value ? 'Colaborador atualizado.' : 'Colaborador cadastrado.'
    await carregarColaboradores()
  } catch (e) {
    erroFormulario.value = e.message || 'Não foi possível salvar o colaborador.'
  } finally {
    salvando.value = false
  }
}

// ------------------------------------------------------------
// Remover
// ------------------------------------------------------------

async function remover(colaborador) {
  limparAvisos()

  const mensagem = colaborador.alocado
    ? `${colaborador.nome} está alocado em uma equipe. Remover o colaborador também libera a vaga dele. Deseja continuar?`
    : `Deseja realmente remover ${colaborador.nome} (chapa ${colaborador.chapa})?`

  if (!(await confirmar(mensagem, { titulo: 'Remover colaborador', textoConfirmar: 'Remover' }))) {
    return
  }

  try {
    const resposta = await fetch(
      `/api/colaboradores/cadastro/${encodeURIComponent(colaborador.chapa)}` +
        (colaborador.alocado ? '?desalocar=1' : ''),
      { method: 'DELETE' }
    )

    const dados = await resposta.json()

    if (!resposta.ok || dados.erro) {
      throw new Error(dados.erro || 'Não foi possível remover o colaborador.')
    }

    sucesso.value = 'Colaborador removido.'
    await carregarColaboradores()
  } catch (e) {
    erro.value = e.message || 'Não foi possível remover o colaborador.'
  }
}

onMounted(carregarColaboradores)
</script>

<style scoped>
.cartao-formulario {
  width: 100%;
  max-width: 480px;
}

/* formulário longo: rola só o miolo e deixa cabeçalho e botões à vista */
.corpo-formulario {
  max-height: 68vh;
  overflow-y: auto;
}
</style>
