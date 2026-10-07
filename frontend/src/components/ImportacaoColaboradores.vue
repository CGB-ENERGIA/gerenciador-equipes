<template>
  <div>
    <q-banner v-if="erro" class="bg-red-1 text-negative q-mb-md" rounded>
      {{ erro }}
    </q-banner>

    <q-banner v-if="sucesso" class="bg-green-1 text-positive q-mb-md" rounded>
      {{ sucesso }}
    </q-banner>

      <q-card bordered>
        <q-card-section>
          <div class="text-h6">Atualizar cadastro de colaboradores</div>
          <div class="text-caption text-grey-7">
            Exclusivo do Administrador. Envie a planilha Excel padrão do
            cadastro de colaboradores para criar ou atualizar os registros.
          </div>
        </q-card-section>

        <q-separator />

        <q-card-section>
          <div class="q-mb-md">
            <q-btn
              unelevated
              rounded
              no-caps
              dense
              color="positive"
              icon="download"
              label="Baixar planilha modelo"
              :loading="baixandoModeloColaboradores"
              class="btn-exportar"
              @click="baixarModeloColaboradores"
            />
            <div class="text-caption text-grey-7 q-mt-sm">
              Traz as colunas certas e uma linha de exemplo — preencha uma
              linha por colaborador (e uma linha extra por rateio, se houver
              mais de um) e envie abaixo. Vem também com uma aba extra:
              <strong>Consulta Colaboradores</strong> (lista completa do
              cadastro atual).
            </div>
          </div>

          <div class="row q-col-gutter-md items-start">
            <div class="col-12 col-md">
              <q-file
                v-model="arquivoColaboradores"
                outlined
                dense
                clearable
                accept=".xlsx"
                label="Planilha de colaboradores (.xlsx)"
                @update:model-value="resumoColaboradores = null"
              >
                <template #prepend>
                  <q-icon name="attach_file" />
                </template>
              </q-file>
            </div>

            <div class="col-12 col-md-auto">
              <q-btn
                color="primary"
                icon="fact_check"
                label="Analisar planilha"
                :disable="!arquivoColaboradores"
                :loading="analisandoColaboradores"
                @click="analisarPlanilhaColaboradores"
              />
            </div>
          </div>

          <!--
            Os 4 chips são o resumo clicável da análise: cada um abre o
            MESMO diálogo (detalheImportacao guarda qual), que troca só as
            colunas da tabela. Um diálogo por tipo seria 4 blocos quase
            idênticos de markup.
          -->
          <div v-if="resumoColaboradores" class="q-mt-md">
            <div class="row q-gutter-sm q-mb-sm">
              <q-chip
                v-for="chip in chipsImportacao"
                :key="chip.tipo"
                :color="chip.cor"
                text-color="white"
                :clickable="chip.total > 0"
                @click="abrirDetalheImportacao(chip.tipo)"
              >
                {{ chip.total }} {{ chip.rotulo }}
                <q-icon v-if="chip.total > 0" name="visibility" size="16px" class="q-ml-xs" />
                <q-tooltip v-if="chip.total > 0">Clique para ver os detalhes</q-tooltip>
              </q-chip>
            </div>

            <q-banner
              v-if="resumoColaboradores.erros?.length"
              class="bg-red-1 text-negative q-mb-sm"
              rounded
              dense
            >
              {{ resumoColaboradores.erros.length }} linha(s) com erro impedem a
              aplicação. Clique no chip vermelho para ver quais.
            </q-banner>

            <q-btn
              color="positive"
              label="Confirmar e aplicar"
              :disable="!!resumoColaboradores.erros?.length"
              :loading="aplicandoColaboradores"
              @click="aplicarPlanilhaColaboradores"
            />
          </div>
        </q-card-section>
      </q-card>

      <q-dialog v-model="dialogDetalheImportacao">
        <q-card style="width: 820px; max-width: 94vw">
          <q-card-section class="row items-center q-py-sm">
            <div class="text-h6">{{ tituloDetalheImportacao }}</div>
            <q-space />
            <q-btn v-close-popup flat round dense icon="close" />
          </q-card-section>

          <q-separator />

          <q-card-section class="q-pa-none" style="max-height: 62vh; overflow: auto">
            <q-markup-table flat dense separator="horizontal" class="tabela-detalhe">
              <thead>
                <tr v-if="detalheImportacao === 'criados'">
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('chapa')">
                    Chapa
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'chapa'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('nome')">
                    Nome
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'nome'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('funcao')">
                    Função
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'funcao'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('secao')">
                    Seção
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'secao'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('situacao')">
                    Situação
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'situacao'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('admissao')">
                    Admissão
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'admissao'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('tipo_funcao')">
                    Tipo de Função
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'tipo_funcao'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                </tr>
                <tr v-else-if="detalheImportacao === 'atualizados'">
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('chapa')">
                    Chapa
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'chapa'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('nome')">
                    Nome
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'nome'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('campo')">
                    Campo
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'campo'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('de')">
                    De
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'de'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('para')">
                    Para
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'para'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                </tr>
                <tr v-else-if="detalheImportacao === 'rateios'">
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('chapa')">
                    Chapa
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'chapa'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('nome')">
                    Nome
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'nome'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('rateio')">
                    Rateio
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'rateio'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('grpccusto')">
                    Grupo de custo
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'grpccusto'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                </tr>
                <tr v-else>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('linha')">
                    Linha
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'linha'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('chapa')">
                    Chapa
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'chapa'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('nome')">
                    Nome
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'nome'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('secao')">
                    Seção
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'secao'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                  <th class="text-left col-ordenavel" @click="ordenarDetalhe('erro')">
                    Erro
                    <q-icon
                      v-if="ordenacaoDetalhe.coluna === 'erro'"
                      :name="ordenacaoDetalhe.direcao === 'asc' ? 'arrow_upward' : 'arrow_downward'"
                      size="14px"
                      class="q-ml-xs"
                    />
                  </th>
                </tr>
              </thead>

              <tbody v-if="detalheImportacao === 'criados'">
                <tr v-for="item in criadosOrdenados" :key="item.chapa">
                  <td>{{ item.chapa }}</td>
                  <td>{{ item.nome || '—' }}</td>
                  <td>{{ item.funcao || '—' }}</td>
                  <td>{{ item.secao || '—' }}</td>
                  <td>{{ item.situacao || '—' }}</td>
                  <td>{{ item.admissao }}</td>
                  <td>{{ item.tipo_funcao || '—' }}</td>
                </tr>
              </tbody>

              <!--
                Por padrão (ou ordenando por Chapa/Nome), Atualizados vira
                uma linha POR MUDANÇA (de-para) agrupada por colaborador:
                chapa/nome só aparecem na primeira linha de cada pessoa.
                Ordenando por Campo/De/Para o agrupamento perde sentido
                (as mudanças de uma mesma pessoa se espalham pela tabela),
                então nesse caso a chapa/nome repete em toda linha.
              -->
              <tbody
                v-else-if="detalheImportacao === 'atualizados' && atualizadosOrdenaPorMudanca"
              >
                <tr v-for="(linha, indice) in atualizadosLinhasFlatOrdenadas" :key="indice">
                  <td>{{ linha.chapa }}</td>
                  <td>{{ linha.nome || '—' }}</td>
                  <template v-if="linha.semAlteracao">
                    <td colspan="3" class="text-grey-7">
                      Sem alteração de campo — só reconfirmado pela planilha.
                    </td>
                  </template>
                  <template v-else>
                    <td class="text-weight-medium">{{ linha.campo }}</td>
                    <td class="text-grey-7">{{ linha.de }}</td>
                    <td class="text-positive text-weight-medium">{{ linha.para }}</td>
                  </template>
                </tr>
              </tbody>

              <tbody v-else-if="detalheImportacao === 'atualizados'">
                <template
                  v-for="item in atualizadosOrdenados"
                  :key="item.chapa"
                >
                  <tr v-if="!item.mudancas?.length" class="linha-sem-mudanca">
                    <td>{{ item.chapa }}</td>
                    <td>{{ item.nome || '—' }}</td>
                    <td colspan="3" class="text-grey-7">
                      Sem alteração de campo — só reconfirmado pela planilha.
                    </td>
                  </tr>
                  <template v-else>
                    <tr
                      v-for="(mudanca, indice) in item.mudancas"
                      :key="`${item.chapa}-${indice}`"
                      :class="indice === 0 ? 'linha-inicio-grupo' : ''"
                    >
                      <td>{{ indice === 0 ? item.chapa : '' }}</td>
                      <td>{{ indice === 0 ? item.nome || '—' : '' }}</td>
                      <td class="text-weight-medium">{{ mudanca.campo }}</td>
                      <td class="text-grey-7">{{ mudanca.de }}</td>
                      <td class="text-positive text-weight-medium">{{ mudanca.para }}</td>
                    </tr>
                  </template>
                </template>
              </tbody>

              <tbody v-else-if="detalheImportacao === 'rateios'">
                <tr
                  v-for="(item, indice) in rateiosOrdenados"
                  :key="indice"
                >
                  <td>{{ item.chapa }}</td>
                  <td>{{ item.nome || '—' }}</td>
                  <td>{{ item.rateio }}</td>
                  <td>{{ item.grpccusto }}</td>
                </tr>
              </tbody>

              <tbody v-else>
                <tr
                  v-for="(item, indice) in errosOrdenados"
                  :key="indice"
                >
                  <td>{{ item.linha }}</td>
                  <td>{{ item.chapa || '—' }}</td>
                  <td>{{ item.nome || '—' }}</td>
                  <td>{{ item.secao || '—' }}</td>
                  <td class="text-negative">{{ item.erro }}</td>
                </tr>
              </tbody>
            </q-markup-table>
          </q-card-section>
        </q-card>
      </q-dialog>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

import { criarOrdenacaoTabela, ordenarLista } from '../utils/ordenacaoTabela'

// avisa a página quando a planilha foi aplicada, para ela recarregar a lista
const emit = defineEmits(['importado'])

const erro = ref('')
const sucesso = ref('')

function limparAvisos() {
  erro.value = ''
  sucesso.value = ''
}

const arquivoColaboradores = ref(null)
const baixandoModeloColaboradores = ref(false)
const dialogDetalheImportacao = ref(false)
const detalheImportacao = ref('criados')
const resumoColaboradores = ref(null)
const analisandoColaboradores = ref(false)
const aplicandoColaboradores = ref(false)

const chipsImportacao = computed(() => {
  const resumo = resumoColaboradores.value || {}

  return [
    {
      tipo: 'criados',
      cor: 'positive',
      rotulo: 'novo(s)',
      total: resumo.criados || 0
    },
    {
      tipo: 'atualizados',
      cor: 'primary',
      rotulo: 'atualizado(s)',
      total: resumo.atualizados || 0
    },
    {
      tipo: 'rateios',
      cor: 'grey-7',
      rotulo: 'rateio(s) novo(s)',
      total: resumo.rateios_novos || 0
    },
    {
      tipo: 'erros',
      cor: resumo.erros?.length ? 'negative' : 'grey-5',
      rotulo: 'com erro',
      total: resumo.erros?.length || 0
    }
  ]
})

const TITULOS_DETALHE_IMPORTACAO = {
  criados: 'Colaboradores novos',
  atualizados: 'Colaboradores atualizados (de → para)',
  rateios: 'Rateios novos',
  erros: 'Linhas com erro'
}

const tituloDetalheImportacao = computed(
  () => TITULOS_DETALHE_IMPORTACAO[detalheImportacao.value] || 'Detalhes'
)

function abrirDetalheImportacao(tipo) {
  const chip = chipsImportacao.value.find(item => item.tipo === tipo)

  if (!chip?.total) {
    return
  }

  detalheImportacao.value = tipo
  resetarOrdenacaoDetalhe()
  dialogDetalheImportacao.value = true
}

// ------------------------------------------------------------
// Ordenação das tabelas do diálogo de detalhe (clique no cabeçalho)
// ------------------------------------------------------------

const {
  estado: ordenacaoDetalhe,
  ordenarPor: ordenarDetalhe,
  resetar: resetarOrdenacaoDetalhe
} = criarOrdenacaoTabela()

const EXTRATORES_DETALHE = {
  criados: {
    chapa: item => item.chapa,
    nome: item => item.nome,
    funcao: item => item.funcao,
    tipo_funcao: item => item.tipo_funcao,
    secao: item => item.secao,
    situacao: item => item.situacao,
    admissao: item => item.admissao
  },
  atualizados: {
    chapa: item => item.chapa,
    nome: item => item.nome
  },
  rateios: {
    chapa: item => item.chapa,
    nome: item => item.nome,
    rateio: item => item.rateio,
    grpccusto: item => item.grpccusto
  },
  erros: {
    linha: item => item.linha,
    chapa: item => item.chapa,
    nome: item => item.nome,
    secao: item => item.secao,
    erro: item => item.erro
  }
}

function ordenarDetalheImportacao(lista) {
  const extratores = EXTRATORES_DETALHE[detalheImportacao.value] || {}
  const extrair = extratores[ordenacaoDetalhe.coluna]

  return extrair ? ordenarLista(lista, extrair, ordenacaoDetalhe) : lista
}

const criadosOrdenados = computed(() =>
  ordenarDetalheImportacao(resumoColaboradores.value?.detalhes_criados || [])
)

const atualizadosOrdenados = computed(() =>
  ordenarDetalheImportacao(resumoColaboradores.value?.detalhes_atualizados || [])
)

// Ordenar por Campo/De/Para só faz sentido linha a linha (por mudança), não
// por colaborador — nesse caso a tabela troca o agrupamento por uma lista
// achatada, com chapa/nome repetidos em toda linha.
const COLUNAS_ATUALIZADOS_POR_MUDANCA = ['campo', 'de', 'para']

const atualizadosOrdenaPorMudanca = computed(
  () =>
    detalheImportacao.value === 'atualizados' &&
    COLUNAS_ATUALIZADOS_POR_MUDANCA.includes(ordenacaoDetalhe.coluna)
)

const atualizadosLinhasFlat = computed(() => {
  const itens = resumoColaboradores.value?.detalhes_atualizados || []
  const linhas = []

  itens.forEach(item => {
    if (!item.mudancas?.length) {
      linhas.push({ chapa: item.chapa, nome: item.nome, semAlteracao: true })
      return
    }

    item.mudancas.forEach(mudanca => {
      linhas.push({
        chapa: item.chapa,
        nome: item.nome,
        campo: mudanca.campo,
        de: mudanca.de,
        para: mudanca.para
      })
    })
  })

  return linhas
})

const EXTRATORES_ATUALIZADOS_POR_MUDANCA = {
  campo: linha => linha.campo,
  de: linha => linha.de,
  para: linha => linha.para
}

const atualizadosLinhasFlatOrdenadas = computed(() => {
  const extrair = EXTRATORES_ATUALIZADOS_POR_MUDANCA[ordenacaoDetalhe.coluna]
  return extrair
    ? ordenarLista(atualizadosLinhasFlat.value, extrair, ordenacaoDetalhe)
    : atualizadosLinhasFlat.value
})

const rateiosOrdenados = computed(() =>
  ordenarDetalheImportacao(resumoColaboradores.value?.detalhes_rateios || [])
)

const errosOrdenados = computed(() =>
  ordenarDetalheImportacao(resumoColaboradores.value?.erros || [])
)

async function baixarModeloColaboradores() {
  limparAvisos()
  baixandoModeloColaboradores.value = true

  try {
    const resposta = await fetch('/api/colaboradores/planilha/modelo')

    if (!resposta.ok) {
      const dados = await resposta.json().catch(() => ({}))
      throw new Error(dados.erro || 'Erro ao gerar o modelo.')
    }

    const blob = await resposta.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'cadastro-colaboradores.xlsx'
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    erro.value = e.message || 'Erro ao gerar o modelo.'
  } finally {
    baixandoModeloColaboradores.value = false
  }
}

async function analisarPlanilhaColaboradores() {
  if (!arquivoColaboradores.value) {
    return
  }

  limparAvisos()
  analisandoColaboradores.value = true

  try {
    const corpo = new FormData()
    corpo.append('arquivo', arquivoColaboradores.value)

    const resposta = await fetch('/api/colaboradores/planilha/previa', {
      method: 'POST',
      body: corpo
    })

    const dados = await resposta.json()

    // mesma checagem de analisarPlanilhaUsuarios: qualquer falha do servidor
    // é erro, mesmo que a resposta traga contagens parciais
    if (!resposta.ok || dados.erro) {
      throw new Error(dados.erro || 'Erro ao analisar a planilha.')
    }

    resumoColaboradores.value = dados
  } catch (e) {
    erro.value = e.message || 'Erro ao analisar a planilha.'
  } finally {
    analisandoColaboradores.value = false
  }
}

async function aplicarPlanilhaColaboradores() {
  if (!arquivoColaboradores.value) {
    return
  }

  limparAvisos()
  aplicandoColaboradores.value = true

  try {
    const corpo = new FormData()
    corpo.append('arquivo', arquivoColaboradores.value)

    const resposta = await fetch('/api/colaboradores/planilha/aplicar', {
      method: 'POST',
      body: corpo
    })

    const dados = await resposta.json()

    if (!resposta.ok || dados.erro) {
      resumoColaboradores.value = dados.resumo || resumoColaboradores.value
      throw new Error(dados.erro || 'Erro ao aplicar a planilha.')
    }

    sucesso.value =
      `Cadastro atualizado: ${dados.criados} novo(s), ` +
      `${dados.atualizados} atualizado(s), ${dados.rateios_novos} rateio(s) novo(s), ` +
      `${dados.rateios_removidos || 0} rateio(s) removido(s).`
    arquivoColaboradores.value = null
    resumoColaboradores.value = null
    emit('importado')
  } catch (e) {
    erro.value = e.message || 'Erro ao aplicar a planilha.'
  } finally {
    aplicandoColaboradores.value = false
  }
}
</script>

<style scoped>
/* tabela do diálogo de detalhe da importação */
.tabela-detalhe :deep(th) {
  font-family: var(--fonte-ui);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-size: 0.7rem;
  position: sticky;
  top: 0;
  z-index: 1;
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

/* no "de-para", cada colaborador ocupa várias linhas (uma por campo
   alterado); a régua mais forte marca onde começa a próxima pessoa */
.tabela-detalhe :deep(tr.linha-inicio-grupo:not(:first-child) td),
.tabela-detalhe :deep(tr.linha-sem-mudanca:not(:first-child) td) {
  border-top: 2px solid var(--linha-forte);
}
</style>
