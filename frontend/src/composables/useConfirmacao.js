import { ref } from 'vue'

// Confirmação dentro do próprio sistema, no lugar do window.confirm: o
// diálogo nativo do navegador pode ser bloqueado ou ignorado em silêncio
// ("impedir esta página de criar diálogos") e não segue o visual do projeto.
//
// Estado único, fora da função: o diálogo (DialogoConfirmacao.vue) fica
// montado uma vez no App.vue e qualquer tela abre ele por aqui.
const estado = ref({
  aberto: false,
  titulo: '',
  mensagem: '',
  textoConfirmar: '',
  perigo: true
})

let resolverPendente = null

function responder(confirmado) {
  estado.value.aberto = false
  const resolver = resolverPendente
  resolverPendente = null
  if (resolver) {
    resolver(confirmado)
  }
}

/**
 * Abre o diálogo e devolve uma Promise que resolve true (Confirmar) ou false
 * (Cancelar, Esc, clique fora). Uso: `if (!(await confirmar('...'))) return`.
 */
function confirmar(
  mensagem,
  { titulo = 'Confirmar ação', textoConfirmar = 'Confirmar', perigo = true } = {}
) {
  // uma confirmação nova cancela a anterior que ainda estivesse aberta
  if (resolverPendente) {
    responder(false)
  }

  estado.value = {
    aberto: true,
    titulo,
    mensagem,
    textoConfirmar,
    perigo
  }

  return new Promise(resolve => {
    resolverPendente = resolve
  })
}

export function useConfirmacao() {
  return { estado, confirmar, responder }
}
