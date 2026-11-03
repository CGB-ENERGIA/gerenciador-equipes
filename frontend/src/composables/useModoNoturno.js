import { ref } from 'vue'
import { Dark } from 'quasar'

const CHAVE_ARMAZENAMENTO = 'gerenciadorEquipes_modoNoturno'

export function useModoNoturno() {
  const modoNoturno = ref(Dark.isActive)

  // Navegador que bloqueia o armazenamento local (aba anônima, política da
  // empresa) faz o localStorage dar erro. Isto roda antes da primeira tela
  // (boot/tema.js): sem o try, o sistema inteiro deixava de abrir. Sem
  // armazenamento, o modo escolhido só não fica salvo.
  function alternarModoNoturno() {
    modoNoturno.value = !modoNoturno.value
    Dark.set(modoNoturno.value)
    try {
      localStorage.setItem(CHAVE_ARMAZENAMENTO, String(modoNoturno.value))
    } catch {
      // segue no modo escolhido, só não lembra na próxima visita
    }
  }

  function restaurarModoNoturno() {
    let modoSalvo = null
    try {
      modoSalvo = localStorage.getItem(CHAVE_ARMAZENAMENTO)
    } catch {
      return
    }

    if (modoSalvo !== null) {
      modoNoturno.value = modoSalvo === 'true'
      Dark.set(modoNoturno.value)
    }
  }

  return { modoNoturno, alternarModoNoturno, restaurarModoNoturno }
}
