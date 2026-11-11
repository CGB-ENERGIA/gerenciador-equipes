import { ref, watch } from 'vue'

// largura a partir da qual o menu fica fixo ao lado; abaixo disso abre por cima
export const LARGURA_MENU_FIXO = 1024

const CHAVE = 'menuLateralRecolhido'

function lerRecolhido() {
  try {
    return localStorage.getItem(CHAVE) === '1'
  } catch {
    return false
  }
}

// estado único para todas as páginas: cada página monta o próprio q-layout,
// então o menu precisa lembrar aberto/recolhido ao trocar de aba
const menuAberto = ref(false)
const recolhido = ref(lerRecolhido())

watch(recolhido, valor => {
  try {
    localStorage.setItem(CHAVE, valor ? '1' : '0')
  } catch {
    // sem armazenamento (aba privada etc.): só não lembra
  }
})

export function useMenuLateral() {
  return { menuAberto, recolhido }
}
