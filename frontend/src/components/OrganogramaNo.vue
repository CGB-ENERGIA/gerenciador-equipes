<template>
  <!--
    Uma pessoa do organograma da página Indiretos e, abaixo, quem responde a
    ela (este mesmo componente, recursivo). Assessoria fica ao lado da linha
    que desce, fora da cadeia principal.

    Arrastar (só quem edita): solte uma pessoa sobre outra —
      meio ou parte de baixo -> passa a responder a ela
      parte de cima          -> fica acima dela (assume o chefe dela)
      lado direito           -> vira assessoria dela
  -->
  <div class="org-no">
    <div
      class="org-cartao"
      :class="{
        'org-cartao--base': no.tipo === 'base',
        'org-cartao--grupo': no.tipo === 'grupo',
        'org-cartao--com-base': no.baseTitulo,
        'org-cartao--clicavel': clicavel,
        'org-cartao--externo': no.externo,
        'org-cartao--arrastavel': arrastavel,
        'org-cartao--arrastando': arrastando,
        'org-cartao--alvo': posicaoAlvo === 'abaixo',
        'org-cartao--alvo-acima': posicaoAlvo === 'acima',
        'org-cartao--alvo-lado': posicaoAlvo === 'lado',
        'org-cartao--subsetor': no.cor
      }"
      :style="estiloSubsetor"
      :draggable="arrastavel"
      :title="no.nomeCompleto"
      @dragstart="iniciarArraste"
      @dragend="encerrarArraste"
      @dragover="sobreAlvo"
      @dragleave="posicaoAlvo = null"
      @drop="soltarAqui"
      @click="clicar"
    >
      <template v-if="no.tipo === 'base'">
        <div class="org-base">
          <q-icon :name="no.icone || 'place'" size="16px" />
          {{ no.titulo }}
        </div>
        <div class="org-cartao__rodape org-cartao__rodape--base">{{ no.subtitulo }}</div>
      </template>
      <!-- mesma função, mesmo chefe: um cartão com a lista de nomes -->
      <template v-else-if="no.tipo === 'grupo'">
        <div class="org-cartao__cargo">{{ no.cargo || 'Sem função' }}</div>
        <ul class="org-grupo">
          <li
            v-for="pessoa in no.pessoas"
            :key="pessoa.chapa"
            :title="pessoa.nomeCompleto"
            :draggable="podeEditar"
            :class="{
              'org-grupo__nome--editavel': podeEditar,
              'org-grupo__nome--alvo': nomeAlvo === pessoa.chapa
            }"
            @dragstart.stop="evento => iniciarArrastePessoa(evento, pessoa)"
            @dragend.stop="encerrarArraste"
            @dragover.stop="evento => sobreNome(evento, pessoa)"
            @dragleave.stop="nomeAlvo = null"
            @drop.stop="evento => soltarNoNome(evento, pessoa)"
            @click.stop="podeEditar && arraste.abrirBases(pessoa.chapa)"
          >
            {{ pessoa.nome }}
          </li>
        </ul>
      </template>

      <template v-else>
        <!-- responsável por UMA base: a caixa da base e a dele viram uma só -->
        <div v-if="no.baseTitulo" class="org-base org-base--faixa">
          <q-icon :name="no.iconeFaixa || 'place'" size="14px" />
          {{ no.baseTitulo }}
        </div>
        <div class="org-cartao__cargo">{{ no.cargo || 'Sem função' }}</div>
        <div class="org-cartao__nome">{{ no.nome }}</div>
        <div v-if="no.externo" class="org-cartao__rodape">{{ no.externo }}</div>
        <div v-else-if="no.detalhe" class="org-cartao__rodape org-cartao__rodape--detalhe">{{ no.detalhe }}</div>
      </template>
    </div>

    <!-- assessoria: ao lado da linha que desce -->
    <div
      v-if="no.assessores.length"
      class="org-assessoria"
      :class="{
        'org-assessoria--uniforme': no.apoioDosDoisLados,
        'org-assessoria--sem-filhos': !no.filhos.length && !no.apoioDosDoisLados
      }"
    >
      <div class="org-assessoria__lista org-assessoria__lista--esquerda">
        <div v-for="assessor in assessoresDaEsquerda" :key="assessor.id" class="org-assessoria__item">
          <OrganogramaNo :no="assessor" />
        </div>
      </div>
      <div class="org-assessoria__linha" />
      <div class="org-assessoria__lista">
        <div v-for="assessor in assessoresDaDireita" :key="assessor.id" class="org-assessoria__item">
          <OrganogramaNo :no="assessor" />
        </div>
      </div>
    </div>

    <template v-if="no.filhos.length">
      <div class="org-conector" />
      <div class="org-ramos">
        <div v-for="filho in no.filhos" :key="filho.id" class="org-ramo">
          <OrganogramaNo :no="filho" />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'

defineOptions({ name: 'OrganogramaNo' })

const props = defineProps({
  // pessoa: { id, tipo: 'pessoa', chapa, cargo, nome, nomeCompleto, externo, semAlocacao,
  //           baseTitulo (responde por uma base), filhos, assessores }
  // base:   { id, tipo: 'base', titulo, subtitulo, filhos, assessores: [] }
  // grupo:  { id, tipo: 'grupo', cargo, chefe, chefeNome, pessoas: [{ chapa, nome }], filhos: [] }
  // cor:    { fundo, borda, fundoEscuro, bordaEscura } do subsetor, ou null (Geral)
  // externo: false, ou o motivo ("fora do setor" / "fora do filtro")
  // visão geral: arrastarComo (o que vai no arraste), aoClicar, naoRecebe, icone,
  //              iconeFaixa, detalhe (linha discreta no pé do cartão),
  //              apoioDosDoisLados (assessoria alternando esquerda e direita da linha),
  //              semGerente e acimaDeTodos (para a página saber onde soltaram)
  no: { type: Object, required: true }
})

// fornecido pela página: { habilitado (ref), emArraste (ref), soltar(origem, alvo, posicao),
// abrirBases(chapa) }
const arraste = inject('arrasteOrganograma', null)

// 'acima' | 'abaixo' | 'lado' enquanto alguém passa por cima desta caixa
const posicaoAlvo = ref(null)
const arrastando = ref(false)
const podeEditar = computed(() => Boolean(arraste?.habilitado.value))
const ehPessoa = computed(() => props.no.tipo === 'pessoa')
const ehGrupo = computed(() => props.no.tipo === 'grupo')
// nome dentro de um cartão de grupo sobre o qual algo está passando
const nomeAlvo = ref(null)
// sem alocação (ex.: chefe que não está em setor nenhum) não dá para mover
// o cartão de grupo também se arrasta inteiro (todas as pessoas juntas)
const arrastavel = computed(
  () =>
    podeEditar.value &&
    (Boolean(props.no.arrastarComo) ||
      ehGrupo.value ||
      (ehPessoa.value && !props.no.externo && !props.no.semAlocacao))
)
// clicar na pessoa: escolher as bases pelas quais ela responde. Na visão
// geral, setor e responsável abrem o organograma (também para quem só consulta)
const clicavel = computed(
  () => Boolean(props.no.aoClicar) || (arrastavel.value && ehPessoa.value)
)

// dos dois lados, a lista não empurra os níveis abaixo
const assessoresDaEsquerda = computed(() =>
  props.no.apoioDosDoisLados ? props.no.assessores.filter((_, i) => i % 2) : []
)
const assessoresDaDireita = computed(() =>
  props.no.assessores.filter((_, i) => !props.no.apoioDosDoisLados || !(i % 2))
)

function clicar() {
  if (props.no.aoClicar) props.no.aoClicar()
  else if (clicavel.value) arraste.abrirBases(props.no.chapa)
}

// cor discreta do subsetor (a página gera a paleta: ver coresDosSubsetores)
const estiloSubsetor = computed(() =>
  props.no.cor
    ? {
        '--sub-fundo': props.no.cor.fundo,
        '--sub-borda': props.no.cor.borda,
        '--sub-fundo-escuro': props.no.cor.fundoEscuro,
        '--sub-borda-escura': props.no.cor.bordaEscura
      }
    : null
)

// arraste terminou (soltou em qualquer lugar): apaga o destaque
watch(
  () => arraste?.emArraste.value,
  valor => {
    if (!valor) {
      posicaoAlvo.value = null
      nomeAlvo.value = null
    }
  }
)

function podeReceber() {
  const origem = arraste?.emArraste.value
  if (props.no.naoRecebe) return false
  // "Sem gerente": só recebe o que veio de um setor
  if (props.no.semGerente) return Boolean(origem?.setor && podeEditar.value)
  // grupo sobre ele mesmo não faz sentido
  if (ehGrupo.value) return Boolean(origem && podeEditar.value && origem.grupo !== props.no.id)
  // caixa da base: volta a responder a quem está acima da base
  if (props.no.tipo === 'base') return Boolean(origem && podeEditar.value && props.no.chefe)
  return Boolean(origem && podeEditar.value && ehPessoa.value && origem.chapa !== props.no.chapa)
}

function posicaoDoPonteiro(evento) {
  if (props.no.externo || ehGrupo.value || props.no.tipo === 'base') return 'abaixo'
  const caixa = evento.currentTarget.getBoundingClientRect()
  const x = (evento.clientX - caixa.left) / caixa.width
  const y = (evento.clientY - caixa.top) / caixa.height
  if (y < 0.3) return 'acima'
  if (x > 0.75) return 'lado'
  return 'abaixo'
}

function iniciarArraste(evento) {
  if (!arrastavel.value) return
  arrastando.value = true
  if (props.no.arrastarComo) arraste.emArraste.value = props.no.arrastarComo
  else if (ehGrupo.value) {
    arraste.emArraste.value = {
      grupo: props.no.id,
      chapas: props.no.pessoas.map(p => p.chapa),
      nome: `${props.no.pessoas.length} ${props.no.cargo}`,
      cargo: props.no.cargo
    }
  } else {
    arraste.emArraste.value = { chapa: props.no.chapa, nome: props.no.nome, cargo: props.no.cargo }
  }
  evento.dataTransfer.effectAllowed = 'move'
  evento.dataTransfer.setData('text/plain', props.no.nome || props.no.cargo)
}

function iniciarArrastePessoa(evento, pessoa) {
  if (!podeEditar.value) return
  arraste.emArraste.value = { chapa: pessoa.chapa, nome: pessoa.nome, cargo: props.no.cargo }
  evento.dataTransfer.effectAllowed = 'move'
  evento.dataTransfer.setData('text/plain', pessoa.nome)
}

function sobreNome(evento, pessoa) {
  const origem = arraste?.emArraste.value
  if (!origem || !podeEditar.value || origem.chapa === pessoa.chapa || origem.grupo === props.no.id) return
  evento.preventDefault()
  evento.dataTransfer.dropEffect = 'move'
  posicaoAlvo.value = null
  nomeAlvo.value = pessoa.chapa
}

// soltar sobre um nome do grupo: passa a responder a essa pessoa
function soltarNoNome(evento, pessoa) {
  const origem = arraste?.emArraste.value
  nomeAlvo.value = null
  if (!origem || !podeEditar.value || origem.chapa === pessoa.chapa || origem.grupo === props.no.id) return
  evento.preventDefault()
  arraste.soltar(origem, { chapa: pessoa.chapa, nome: pessoa.nome }, 'abaixo')
}

function encerrarArraste() {
  arrastando.value = false
  arraste.emArraste.value = null
}

function sobreAlvo(evento) {
  if (!podeReceber()) return
  evento.preventDefault()
  evento.dataTransfer.dropEffect = 'move'
  posicaoAlvo.value = posicaoDoPonteiro(evento)
}

function soltarAqui(evento) {
  if (!podeReceber()) return
  evento.preventDefault()
  const posicao = posicaoDoPonteiro(evento)
  posicaoAlvo.value = null
  if (props.no.semGerente) {
    arraste.soltar(arraste.emArraste.value, { semGerente: true, nome: props.no.titulo }, 'abaixo')
    return
  }
  // soltar na caixa da base: responde a quem está acima dela (ex.: tirar
  // alguém de baixo de um colega e devolver ao nível da base)
  if (props.no.tipo === 'base') {
    arraste.soltar(arraste.emArraste.value, { chapa: props.no.chefe, nome: props.no.chefeNome }, 'abaixo')
    return
  }
  // soltar no cartão do grupo (fora de um nome): a página decide — mesma
  // função entra no grupo; outra função escolhe a quem do grupo responde
  if (ehGrupo.value) {
    arraste.soltar(
      arraste.emArraste.value,
      {
        grupo: true,
        cargo: props.no.cargo,
        subsetor: props.no.subsetor || '',
        assessoria: Boolean(props.no.assessoria),
        chefe: props.no.chefe,
        chefeNome: props.no.chefeNome,
        pessoas: props.no.pessoas
      },
      'grupo'
    )
    return
  }
  arraste.soltar(
    arraste.emArraste.value,
    {
      chapa: props.no.chapa,
      nome: props.no.nome,
      externo: props.no.externo,
      acimaDeTodos: props.no.acimaDeTodos
    },
    posicao
  )
}
</script>

<style scoped>
.org-no {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* ---------- cartão: claro, arredondado, sombra leve ---------- */
.org-cartao {
  position: relative;
  /* largura = a do maior texto (cargo ou nome), sem quebrar linha */
  width: max-content;
  min-width: 110px;
  padding: 7px 11px 7px 15px;
  border: 1px solid var(--linha);
  border-radius: 12px;
  background: var(--superficie);
  text-align: left;
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.1),
    0 8px 22px rgba(0, 0, 0, 0.12);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    border-color 0.15s ease;
}

/* faixa lateral: vinho (Geral) ou a cor do subsetor */
.org-cartao::before {
  content: '';
  position: absolute;
  top: 7px;
  bottom: 7px;
  left: 6px;
  width: 4px;
  border-radius: 4px;
  background: var(--marca);
  opacity: 0.85;
}

.org-cartao--subsetor {
  background: var(--sub-fundo);
  border-color: var(--sub-borda);
}

.org-cartao--subsetor::before {
  background: var(--sub-borda);
  opacity: 1;
}

:global(.body--dark) .org-cartao--subsetor {
  background: var(--sub-fundo-escuro);
  border-color: var(--sub-borda-escura);
}

:global(.body--dark) .org-cartao--subsetor::before {
  background: var(--sub-borda-escura);
}

.org-cartao--arrastavel:hover,
.org-cartao--clicavel:hover {
  transform: translateY(-2px);
  box-shadow:
    0 2px 6px rgba(0, 0, 0, 0.12),
    0 14px 30px rgba(0, 0, 0, 0.16);
}

.org-cartao__cargo {
  white-space: nowrap;
  font-family: var(--fonte-ui);
  font-size: 0.66rem;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--tinta-fraca);
}

.org-cartao__nome {
  margin-top: 2px;
  font-family: var(--fonte-ui);
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--titulo);
  white-space: nowrap;
}

.org-cartao__rodape {
  margin-top: 2px;
  font-size: 0.68rem;
  font-style: italic;
  color: var(--tinta-fraca);
}

/* cabe numa linha; só uma lista grande de bases quebra */
.org-cartao__rodape--detalhe {
  max-width: 230px;
  font-style: normal;
}

.org-cartao--externo {
  border-style: dashed;
  background: transparent;
  box-shadow: none;
}

.org-cartao--externo::before {
  opacity: 0.35;
}

/* ---------- base: pílula vinho ---------- */
.org-cartao--base {
  width: auto;
  min-width: 108px;
  padding: 7px 18px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--marca), var(--marca-clara));
  color: #fff;
  text-align: center;
  box-shadow: 0 8px 20px rgba(113, 20, 36, 0.32);
}

.org-cartao--base::before {
  display: none;
}

.org-base {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-family: var(--fonte-ui);
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.org-cartao--base .org-cartao__rodape--base {
  margin-top: 0;
  font-style: normal;
  font-weight: 600;
  color: #fff;
  opacity: 0.9;
}

/* responsável por uma base: a base vira o topo do cartão dele */
.org-base--faixa {
  display: flex;
  justify-content: center;
  margin: -7px -11px 6px -15px;
  padding: 4px 0;
  border-radius: 11px 11px 0 0;
  background: linear-gradient(135deg, var(--marca), var(--marca-clara));
  color: #fff;
  font-size: 0.85rem;
}

.org-cartao--com-base {
  padding-top: 10px;
}

.org-cartao--com-base::before {
  top: 38px;
}

/* ---------- grupo (mesma função): cargo e a lista de nomes ---------- */
.org-grupo {
  margin: 4px 0 0;
  padding: 0;
  list-style: none;
}

.org-grupo li {
  padding: 2px 4px;
  border-top: 1px solid var(--linha);
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--titulo);
  white-space: nowrap;
}

.org-grupo li:first-child {
  border-top: none;
}

.org-grupo__nome--editavel {
  cursor: grab;
  border-radius: 6px;
}

.org-grupo__nome--editavel:hover,
.org-grupo__nome--alvo {
  background: var(--realce);
}

/* ---------- arrastar ---------- */
.org-cartao--arrastavel {
  cursor: grab;
}

.org-cartao--arrastando {
  opacity: 0.4;
}

.org-cartao--alvo {
  outline: 2px solid var(--marca-texto);
  outline-offset: 2px;
  box-shadow: 0 8px 0 -2px var(--marca-texto);
}

.org-cartao--alvo-acima {
  outline: 2px solid var(--marca-texto);
  outline-offset: 2px;
  box-shadow: 0 -8px 0 -2px var(--marca-texto);
}

.org-cartao--alvo-lado {
  outline: 2px solid var(--marca-texto);
  outline-offset: 2px;
  box-shadow: 8px 0 0 -2px var(--marca-texto);
}

/* ---------- linhas de ligação ----------
   Cor sólida (transparente escurece onde as linhas se cruzam) e cada linha
   vertical centrada no meio do galho, para emendar sem degrau. */
.org-no {
  --org-linha: #c9a7ae;
}

:global(.body--dark) .org-no {
  --org-linha: #6e5a5e;
}

.org-conector {
  width: 2px;
  height: 20px;
  background: var(--org-linha);
}

.org-ramos {
  display: flex;
  justify-content: center;
}

.org-ramo {
  position: relative;
  padding: 20px 8px 0;
}

.org-ramo::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  width: 2px;
  height: 20px;
  transform: translateX(-50%);
  background: var(--org-linha);
}

.org-ramo::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--org-linha);
}

.org-ramo:first-child::after {
  left: calc(50% - 1px);
  border-top-left-radius: 6px;
}

.org-ramo:last-child::after {
  right: calc(50% - 1px);
  border-top-right-radius: 6px;
}

.org-ramo:only-child::after {
  display: none;
}

/* ---------- assessoria: ao lado da linha que desce ---------- */
.org-assessoria {
  display: grid;
  grid-template-columns: 1fr 2px 1fr;
  width: 100%;
}

.org-assessoria__linha {
  background: var(--org-linha);
}

.org-assessoria__lista {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 0;
}

.org-assessoria__lista--esquerda {
  align-items: flex-end;
}

.org-assessoria__item {
  position: relative;
  padding-left: 18px;
}

.org-assessoria__lista--esquerda .org-assessoria__item {
  padding-right: 18px;
  padding-left: 0;
}

/* O traço vai até o meio do item, por trás do cartão: quem tem assessoria ou
   equipe própria ocupa mais largura que o cartão, que fica centralizado nela,
   e um traço de tamanho fixo não chegaria até ele. */
.org-assessoria__item::before {
  content: '';
  position: absolute;
  top: 24px;
  left: 0;
  width: calc(50% + 9px);
  height: 2px;
  background: var(--org-linha);
}

.org-assessoria__item > .org-no > .org-cartao--externo {
  background: var(--superficie);
}

/* Sem ninguém abaixo, a linha para no último traço em vez de seguir até o fim
   da lista: cada item desenha o seu trecho, e o último, só até o traço. */
.org-assessoria--sem-filhos > .org-assessoria__linha {
  background: none;
}

.org-assessoria--sem-filhos > .org-assessoria__lista > .org-assessoria__item::after {
  content: '';
  position: absolute;
  top: -12px;
  bottom: 0;
  left: -2px;
  width: 2px;
  background: var(--org-linha);
}

.org-assessoria--sem-filhos > .org-assessoria__lista > .org-assessoria__item:last-child::after {
  bottom: auto;
  height: 38px;
}

.org-assessoria__lista--esquerda .org-assessoria__item::before {
  right: 0;
  left: auto;
}

/* pílula de setor no apoio: da largura do item, para o traço da linha chegar nela */
.org-assessoria__item > .org-no > .org-cartao--base {
  width: 100%;
}

/* apoios da visão geral: todos da largura do maior texto (não a do desenho
   todo), alinhados dos dois lados */
.org-assessoria--uniforme {
  width: max-content;
}

.org-assessoria--uniforme > .org-assessoria__lista {
  align-items: stretch;
  gap: 12px;
}

.org-assessoria--uniforme > .org-assessoria__lista > .org-assessoria__item > .org-no > .org-cartao {
  width: 100%;
}
</style>
