import { reactive } from 'vue'

// Estado + comparação reaproveitados por toda tabela de "conferir planilha"
// que precisa ordenar ao clicar no cabeçalho (colaboradores, usuários em
// lote, vagas em lote, alocação em massa...).

export function criarOrdenacaoTabela() {
  const estado = reactive({ coluna: null, direcao: 'asc' })

  function ordenarPor(coluna) {
    if (estado.coluna === coluna) {
      estado.direcao = estado.direcao === 'asc' ? 'desc' : 'asc'
    } else {
      estado.coluna = coluna
      estado.direcao = 'asc'
    }
  }

  function resetar() {
    estado.coluna = null
    estado.direcao = 'asc'
  }

  return { estado, ordenarPor, resetar }
}

export function compararValores(a, b) {
  const valorA = a ?? ''
  const valorB = b ?? ''

  if (typeof valorA === 'number' && typeof valorB === 'number') {
    return valorA - valorB
  }

  return String(valorA).localeCompare(String(valorB), 'pt-BR', {
    numeric: true,
    sensitivity: 'base'
  })
}

export function ordenarLista(lista, extrair, estado) {
  if (!estado.coluna) {
    return lista
  }

  const sinal = estado.direcao === 'asc' ? 1 : -1

  return [...lista].sort((a, b) => sinal * compararValores(extrair(a), extrair(b)))
}
