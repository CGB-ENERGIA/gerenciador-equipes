<template>
  <q-select
    :model-value="modelValue"
    :options="options"
    outlined
    dense
    clearable
    multiple
    emit-value
    map-options
    @update:model-value="valor => $emit('update:modelValue', valor)"
  >
    <template v-if="icon" #prepend>
      <q-icon :name="icon" size="20px" />
    </template>

    <!--
      Slot "selected" substitui por completo a area de valores marcados do
      q-select. Em vez de um chip por selecao (que quebra linha e faz o
      campo crescer quando ha varios marcados), mede quantos chips cabem
      numa linha so e resume o resto num chip "+N".
    -->
    <template #selected>
      <div ref="containerRef" class="row no-wrap items-center chips-filtro-multiplo">
        <q-chip
          v-for="item in itensExibidos"
          :key="item.value"
          dense
          removable
          class="chip-medido q-my-none"
          @remove.stop="removerValor(item.value)"
        >
          {{ item.label }}
        </q-chip>

        <q-chip v-if="restantes > 0" dense class="q-my-none">
          +{{ restantes }}
        </q-chip>
      </div>
    </template>

    <template #option="scope">
      <q-item v-bind="scope.itemProps">
        <q-item-section side>
          <q-checkbox
            :model-value="scope.selected"
            @update:model-value="scope.toggleOption(scope.opt)"
          />
        </q-item-section>
        <q-item-section>
          <q-item-label>{{ scope.opt.label }}</q-item-label>
        </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, default: () => [] },
  icon: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue'])

// espaco reservado pro chip "+N", em px -- aproximado, pra nao precisar de
// uma segunda medicao so por causa de 1-2 digitos de diferenca no numero
const RESERVA_CHIP_MAIS = 56

const containerRef = ref(null)
const qtdVisivel = ref(0)
let observer = null

const itensSelecionados = computed(() => {
  const rotulos = new Map(props.options.map(opcao => [opcao.value, opcao.label]))

  return props.modelValue.map(valor => ({
    value: valor,
    label: rotulos.get(valor) ?? String(valor)
  }))
})

const itensExibidos = computed(() => itensSelecionados.value.slice(0, qtdVisivel.value))
const restantes = computed(() => itensSelecionados.value.length - qtdVisivel.value)

function removerValor(valor) {
  emit('update:modelValue', props.modelValue.filter(item => item !== valor))
}

// Descobre quantos chips cabem numa linha so sem quebrar: renderiza TODOS
// (escondidos pelo overflow:hidden do container) pra medir a posicao de
// cada um, depois decide quantos mostrar de fato + o chip "+N" com o resto.
async function recalcular() {
  const total = itensSelecionados.value.length

  if (!total) {
    qtdVisivel.value = 0
    return
  }

  qtdVisivel.value = total
  await nextTick()

  const container = containerRef.value
  if (!container) {
    return
  }

  const disponivel = container.clientWidth
  const chips = [...container.querySelectorAll('.chip-medido')]

  if (!chips.length) {
    return
  }

  const ultimo = chips[chips.length - 1]

  // cabe tudo numa linha so: mantem os chips normais, sem "+N"
  if (ultimo.offsetLeft + ultimo.offsetWidth <= disponivel) {
    qtdVisivel.value = total
    return
  }

  let qtd = 0
  for (const chip of chips) {
    if (chip.offsetLeft + chip.offsetWidth > disponivel - RESERVA_CHIP_MAIS) {
      break
    }
    qtd++
  }

  qtdVisivel.value = qtd
}

onMounted(() => {
  recalcular()

  observer = new ResizeObserver(() => recalcular())
  if (containerRef.value) {
    observer.observe(containerRef.value)
  }
})

onBeforeUnmount(() => {
  observer?.disconnect()
})

watch(() => props.modelValue, recalcular, { deep: true })
watch(() => props.options, recalcular)
</script>

<style scoped>
.chips-filtro-multiplo {
  overflow: hidden;
  flex: 1;
  min-width: 0;
}
</style>
