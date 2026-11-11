<template>
  <!--
    Filtro em formato "pílula": um botão de altura fixa que mostra só o
    resumo da escolha ("Setor: Todos", "Setor: GOMAN", "Setor: 3
    selecionados") e abre um menu com busca e caixas de seleção. Mantém a
    mesma API do q-select antigo (model-value / options / label / icon),
    então as páginas não mudam: elas continuam aplicando
    proximaSelecaoMultipla no update:model-value.
  -->
  <div class="filtro-pilula" :class="{ ativo: temFiltro, aberto: menuAberto }">
    <button
      type="button"
      class="filtro-pilula__botao"
      :aria-label="`${label}: ${resumo}`"
      aria-haspopup="listbox"
      :aria-expanded="menuAberto ? 'true' : 'false'"
    >
      <span class="filtro-pilula__rotulo">{{ label }}</span>
      <span class="filtro-pilula__valor">{{ resumo }}</span>
      <q-icon
        v-if="!temFiltro"
        name="expand_more"
        size="18px"
        class="filtro-pilula__seta"
      />
    </button>

    <button
      v-if="temFiltro"
      type="button"
      class="filtro-pilula__limpar"
      :aria-label="`Limpar ${label}`"
      @click.stop="limpar"
    >
      <q-icon name="close" size="16px" />
    </button>

    <q-menu
      v-model="menuAberto"
      fit
      no-focus
      anchor="bottom left"
      self="top left"
      :offset="[0, 6]"
      class="filtro-pilula__menu"
      @show="aoAbrir"
      @hide="busca = ''"
    >
      <div class="filtro-pilula__busca" v-if="options.length > 6">
        <input
          ref="buscaRef"
          v-model="busca"
          type="text"
          :placeholder="`Buscar ${label.toLowerCase()}`"
          @keydown.down.prevent="focarPrimeira"
          @keydown.enter.prevent="marcarPrimeira"
        />
      </div>

      <q-list dense class="filtro-pilula__lista" role="listbox">
        <q-item
          v-for="opcao in opcoesVisiveis"
          :key="String(opcao.value)"
          clickable
          dense
          role="option"
          :aria-selected="estaMarcada(opcao.value) ? 'true' : 'false'"
          class="filtro-pilula__opcao"
          :class="{ marcada: estaMarcada(opcao.value), todos: opcao.value === valorTodosEfetivo }"
          @click="alternar(opcao.value)"
        >
          <q-item-section v-if="multiple" side class="q-pr-sm">
            <q-checkbox
              dense
              size="sm"
              :model-value="estaMarcada(opcao.value)"
              tabindex="-1"
              @update:model-value="alternar(opcao.value)"
            />
          </q-item-section>
          <q-item-section>
            <q-item-label>{{ opcao.label }}</q-item-label>
          </q-item-section>
          <q-item-section v-if="opcao.contagem !== undefined" side>
            <span class="filtro-pilula__contagem">{{ opcao.contagem }}</span>
          </q-item-section>
        </q-item>

        <div v-if="!opcoesVisiveis.length" class="filtro-pilula__vazio">
          Nada encontrado
        </div>
      </q-list>
    </q-menu>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'

const props = defineProps({
  modelValue: { type: [Array, String, Number], default: () => [] },
  options: { type: Array, default: () => [] },
  label: { type: String, default: '' },
  // mantido por compatibilidade com as páginas; a pílula não mostra ícone
  icon: { type: String, default: '' },
  // false = escolha única (fecha o menu ao escolher)
  multiple: { type: Boolean, default: true },
  // valor da opção "Todos/Todas"; se não vier, usa a 1ª opção quando o
  // rótulo dela começa com "Tod"
  valorTodos: { type: [String, Number], default: undefined }
})

const emit = defineEmits(['update:modelValue'])

const menuAberto = ref(false)
const busca = ref('')
const buscaRef = ref(null)

const valorTodosEfetivo = computed(() => {
  if (props.valorTodos !== undefined) {
    return props.valorTodos
  }
  const primeira = props.options[0]
  return primeira && /^tod/i.test(String(primeira.label)) ? primeira.value : undefined
})

const selecionados = computed(() => {
  if (props.multiple) {
    return Array.isArray(props.modelValue) ? props.modelValue : []
  }
  return props.modelValue === null || props.modelValue === undefined ? [] : [props.modelValue]
})

const temFiltro = computed(() => {
  const valores = selecionados.value.filter(valor => valor !== valorTodosEfetivo.value)
  return valores.length > 0
})

const rotulos = computed(() => new Map(props.options.map(opcao => [opcao.value, opcao.label])))

const resumo = computed(() => {
  const valores = selecionados.value.filter(valor => valor !== valorTodosEfetivo.value)
  if (!valores.length) {
    return 'Todos'
  }
  if (valores.length === 1) {
    return rotulos.value.get(valores[0]) ?? String(valores[0])
  }
  return `${valores.length} selecionados`
})

function semAcento(texto) {
  return String(texto).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

const opcoesVisiveis = computed(() => {
  const termo = semAcento(busca.value.trim())
  if (!termo) {
    return props.options
  }
  return props.options.filter(
    opcao => opcao.value === valorTodosEfetivo.value || semAcento(opcao.label).includes(termo)
  )
})

function estaMarcada(valor) {
  if (valor === valorTodosEfetivo.value) {
    return !temFiltro.value
  }
  return selecionados.value.includes(valor)
}

function alternar(valor) {
  if (!props.multiple) {
    emit('update:modelValue', valor)
    menuAberto.value = false
    return
  }

  const atual = selecionados.value
  const todos = valorTodosEfetivo.value

  // "Todos" sempre limpa o resto
  if (valor === todos) {
    emit('update:modelValue', todos === undefined ? [] : [todos])
    return
  }

  const semTodos = atual.filter(item => item !== todos)
  const proxima = semTodos.includes(valor)
    ? semTodos.filter(item => item !== valor)
    : [...semTodos, valor]

  emit('update:modelValue', proxima.length || todos === undefined ? proxima : [todos])
}

function limpar() {
  const todos = valorTodosEfetivo.value
  if (!props.multiple) {
    emit('update:modelValue', todos ?? null)
    return
  }
  emit('update:modelValue', todos === undefined ? [] : [todos])
}

async function aoAbrir() {
  await nextTick()
  buscaRef.value?.focus()
}

function focarPrimeira(evento) {
  const menu = evento.target.closest('.filtro-pilula__menu')
  menu?.querySelector('.filtro-pilula__opcao')?.focus()
}

function marcarPrimeira() {
  const primeira = opcoesVisiveis.value.find(opcao => opcao.value !== valorTodosEfetivo.value)
  if (primeira) {
    alternar(primeira.value)
  }
}
</script>

<style scoped>
.filtro-pilula {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
  min-width: 0;
  height: 36px;
  border-radius: 999px;
  border: 1px solid var(--linha);
  background: var(--superficie-2);
  transition: border-color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
}

.filtro-pilula:hover {
  border-color: var(--linha-forte);
}

.filtro-pilula.aberto,
.filtro-pilula:focus-within {
  border-color: var(--marca-clara);
  box-shadow: 0 0 0 3px rgba(113, 20, 36, 0.1);
}

.filtro-pilula.ativo {
  border-color: var(--marca-clara);
  background: rgba(113, 20, 36, 0.07);
}

.filtro-pilula__botao {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 10px 0 14px;
  border: 0;
  background: transparent;
  color: var(--tinta);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
  text-align: left;
  border-radius: 999px;
  outline: none;
}

.filtro-pilula__rotulo {
  color: var(--tinta-fraca);
  flex: none;
}

.filtro-pilula__rotulo::after {
  content: ':';
}

.filtro-pilula__valor {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-weight: 600;
}

.filtro-pilula.ativo .filtro-pilula__valor {
  color: var(--marca);
}

.filtro-pilula__seta {
  flex: none;
  color: var(--tinta-fraca);
  transition: transform 0.15s ease;
}

.filtro-pilula.aberto .filtro-pilula__seta {
  transform: rotate(180deg);
}

.filtro-pilula__limpar {
  flex: none;
  width: 26px;
  height: 26px;
  margin-right: 5px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--marca);
  cursor: pointer;
}

.filtro-pilula__limpar:hover,
.filtro-pilula__limpar:focus-visible {
  background: rgba(113, 20, 36, 0.12);
  outline: none;
}

body.body--dark .filtro-pilula.ativo {
  background: rgba(224, 138, 156, 0.1);
}

body.body--dark .filtro-pilula.ativo .filtro-pilula__valor,
body.body--dark .filtro-pilula__limpar {
  color: var(--marca-clara);
}

body.body--dark .filtro-pilula.aberto,
body.body--dark .filtro-pilula:focus-within {
  box-shadow: 0 0 0 3px rgba(224, 138, 156, 0.14);
}
</style>

<style>
/* o menu é teleportado para o body: estilo sem scoped */
.filtro-pilula__menu {
  min-width: 220px;
  max-width: 360px;
  border-radius: 12px;
  border: 1px solid var(--linha);
  background: var(--superficie);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.12);
}

.filtro-pilula__busca {
  padding: 8px;
  border-bottom: 1px solid var(--linha);
  position: sticky;
  top: 0;
  background: var(--superficie);
  z-index: 1;
}

.filtro-pilula__busca input {
  width: 100%;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--linha);
  border-radius: 8px;
  background: var(--superficie-2);
  color: var(--tinta);
  font: inherit;
  font-size: 13px;
  outline: none;
}

.filtro-pilula__busca input:focus {
  border-color: var(--marca-clara);
}

.filtro-pilula__lista {
  max-height: 300px;
  overflow-y: auto;
  padding: 4px 0;
}

.filtro-pilula__opcao {
  min-height: 32px;
  font-size: 13px;
}

.filtro-pilula__opcao.marcada {
  color: var(--marca);
  font-weight: 600;
}

body.body--dark .filtro-pilula__opcao.marcada {
  color: var(--marca-clara);
}

.filtro-pilula__opcao.todos {
  border-bottom: 1px solid var(--linha);
}

.filtro-pilula__contagem {
  font-size: 12px;
  color: var(--tinta-fraca);
  font-variant-numeric: tabular-nums;
}

.filtro-pilula__vazio {
  padding: 10px 14px;
  font-size: 13px;
  color: var(--tinta-fraca);
}
</style>
