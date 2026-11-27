export const TIPO_TODOS = 'TODOS'
export const TIPO_FOLGUISTA = 'FOLGUISTA'
export const OPCAO_TODAS_BASES = '__TODAS_BASES__'

// O filtro de base é compartilhado entre as telas: quem escolhe uma base no
// Banco de Dados encontra a mesma seleção no Resumo. Por isso a chave fica
// aqui, e não repetida em cada página.
export const CHAVE_BASES_SELECIONADAS = 'gerenciadorEquipes_basesSelecionadas'

function normalizarTexto(texto) {
  return String(texto || '')
    .trim()
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toUpperCase()
}

// Uma equipe pode ter vagas de varias disciplinas (TIPO EQUIPE) ao mesmo
// tempo — a equipe Folguista de uma base, por exemplo, pode ter vagas de
// construcao e de poda juntas. Por isso o tipo nao e mais um valor unico por
// equipe: ver tiposDaEquipe/ehEquipeFolguista, que sao independentes entre si.
export function ehEquipeFolguista(equipe) {
  if (typeof equipe?.folguista === 'boolean') {
    return equipe.folguista
  }
  // formato antigo da API (sem o campo 'folguista'): cai no prefixo
  return normalizarTexto(equipe?.prefixo) === TIPO_FOLGUISTA
}

export function tiposDaEquipe(equipe) {
  return Array.isArray(equipe?.tipos) ? equipe.tipos : []
}

// Aceita tanto um valor unico quanto uma lista (filtro com multipla
// selecao): a equipe entra se bater com QUALQUER um dos tipos escolhidos.
export function equipeCombinaComTipo(equipe, tipoFiltro) {
  const filtros = Array.isArray(tipoFiltro) ? tipoFiltro : tipoFiltro ? [tipoFiltro] : []

  if (!filtros.length || filtros.includes(TIPO_TODOS)) {
    return true
  }

  return filtros.some(filtro =>
    filtro === TIPO_FOLGUISTA
      ? ehEquipeFolguista(equipe)
      : tiposDaEquipe(equipe).includes(filtro)
  )
}

// Monta as opcoes do filtro de tipo a partir das disciplinas que existem de
// fato nas equipes carregadas, em vez de uma lista fixa — assim uma
// disciplina nova (cadastrada pela planilha) aparece no filtro sem precisar
// mexer no codigo.
export function opcoesTipoFiltro(equipes) {
  const disciplinas = new Set()

  for (const equipe of equipes || []) {
    for (const tipo of tiposDaEquipe(equipe)) {
      if (tipo) {
        disciplinas.add(tipo)
      }
    }
  }

  return [
    { label: 'Todos os tipos', value: TIPO_TODOS },
    // nome de tipo de equipe sempre em caixa alta
    ...[...disciplinas].sort().map(tipo => ({ label: tipo.toUpperCase(), value: tipo })),
    // Folguista só entra na lista se existir equipe Folguista no contexto
    ...((equipes || []).some(ehEquipeFolguista)
      ? [{ label: TIPO_FOLGUISTA, value: TIPO_FOLGUISTA }]
      : [])
  ]
}

// ------------------------------------------------------------
// Filtro de setor
// ------------------------------------------------------------

export const SETOR_TODOS = 'TODOS'

// O setor e informado por disciplina, entao uma equipe com vagas de construcao
// e de poda pode responder a dois setores. O filtro casa se QUALQUER vaga dela
// for do setor escolhido.
export function setoresDaEquipe(equipe) {
  return Array.isArray(equipe?.setores) ? equipe.setores : []
}

// Idem equipeCombinaComTipo: aceita um valor unico ou uma lista.
export function equipeCombinaComSetor(equipe, setorFiltro) {
  const filtros = Array.isArray(setorFiltro) ? setorFiltro : setorFiltro ? [setorFiltro] : []

  if (!filtros.length || filtros.includes(SETOR_TODOS)) {
    return true
  }

  return setoresDaEquipe(equipe).some(setor => filtros.includes(setor))
}

export function opcoesSetorFiltro(equipes) {
  const setores = new Set()

  for (const equipe of equipes || []) {
    for (const setor of setoresDaEquipe(equipe)) {
      if (setor) {
        setores.add(setor)
      }
    }
  }

  return [
    { label: 'Todos os setores', value: SETOR_TODOS },
    ...[...setores].sort().map(setor => ({ label: setor, value: setor }))
  ]
}

// ------------------------------------------------------------
// Filtro de coordenador / supervisor
// ------------------------------------------------------------
//
// Igual ao setor, os dois sao informados POR VAGA (disciplina), nao por
// equipe — a mesma equipe pode ter uma vaga de construcao com um
// coordenador e uma de poda com outro. Por isso as duas funcoes abaixo
// recebem o nome do campo ('coordenador' ou 'supervisor') em vez de existir
// um par quase identico para cada um.

export const RESPONSAVEL_TODOS = 'TODOS'

export function responsaveisDaEquipe(equipe, campo) {
  const valores = new Set()

  for (const vaga of equipe?.vagas || []) {
    const valor = String(vaga?.[campo] || '').trim()
    if (valor) {
      valores.add(valor)
    }
  }

  return [...valores]
}

// Idem equipeCombinaComTipo: aceita um valor unico ou uma lista.
export function equipeCombinaComResponsavel(equipe, campo, filtro) {
  const filtros = Array.isArray(filtro) ? filtro : filtro ? [filtro] : []

  if (!filtros.length || filtros.includes(RESPONSAVEL_TODOS)) {
    return true
  }

  return responsaveisDaEquipe(equipe, campo).some(valor => filtros.includes(valor))
}

export function opcoesResponsavelFiltro(equipes, campo, rotuloTodos) {
  const valores = new Set()

  for (const equipe of equipes || []) {
    for (const valor of responsaveisDaEquipe(equipe, campo)) {
      valores.add(valor)
    }
  }

  return [
    { label: rotuloTodos, value: RESPONSAVEL_TODOS },
    ...[...valores]
      .sort((a, b) => a.localeCompare(b, 'pt-BR'))
      .map(valor => ({ label: valor, value: valor }))
  ]
}

// ------------------------------------------------------------
// Filtro de base com a opcao "Todas as bases", compartilhado entre telas
// ------------------------------------------------------------

export function normalizarSelecaoBases(bases) {
  if (!Array.isArray(bases)) {
    return []
  }

  const valores = [...new Set(bases.filter(Boolean))]

  if (valores.includes(OPCAO_TODAS_BASES)) {
    return [OPCAO_TODAS_BASES]
  }

  return valores
}

// Ao marcar "Todas as bases" com outras ja selecionadas, o esperado e que
// as outras saiam da selecao (nao o contrario).
export function proximaSelecaoBases(selecaoAtual, novaSelecao) {
  const selecao = Array.isArray(novaSelecao) ? novaSelecao : []

  if (
    selecao.includes(OPCAO_TODAS_BASES) &&
    selecaoAtual.includes(OPCAO_TODAS_BASES) &&
    selecao.length > 1
  ) {
    return selecao.filter(base => base !== OPCAO_TODAS_BASES)
  }

  return normalizarSelecaoBases(selecao)
}

export function equipeNaSelecaoDeBases(equipe, selecao) {
  if (!selecao.length || selecao.includes(OPCAO_TODAS_BASES)) {
    return true
  }

  return selecao.includes(String(equipe?.base || '').trim())
}

// ------------------------------------------------------------
// Selecao multipla generica (tipo/setor/coordenador/supervisor), com a
// mesma regra da selecao de bases: marcar a opcao "Todos" com outras ja
// selecionadas tira as outras da selecao, nao o contrario.
// ------------------------------------------------------------

export function normalizarSelecaoMultipla(selecao, opcaoTodos) {
  if (!Array.isArray(selecao)) {
    return []
  }

  // filtra so null/undefined (nao Boolean): a opcao "Todos" de alguns
  // filtros usa '' como sentinela, que Boolean descartaria
  const valores = [...new Set(selecao.filter(valor => valor !== null && valor !== undefined))]

  if (valores.includes(opcaoTodos)) {
    return [opcaoTodos]
  }

  return valores
}

export function proximaSelecaoMultipla(selecaoAtual, novaSelecao, opcaoTodos) {
  const selecao = Array.isArray(novaSelecao) ? novaSelecao : []

  if (
    selecao.includes(opcaoTodos) &&
    selecaoAtual.includes(opcaoTodos) &&
    selecao.length > 1
  ) {
    return selecao.filter(valor => valor !== opcaoTodos)
  }

  return normalizarSelecaoMultipla(selecao, opcaoTodos)
}

// ============================================================
// FUNÇÕES DOS COLABORADORES
// ============================================================

// Ordem de exibição das funções nas tabelas. Quem decide em que categoria cada
// nome do cadastro cai é o padronizar_funcao do app.py — o servidor já manda a
// função classificada, então essa regra não é repetida aqui.
export const FUNCOES_SISTEMA = [
  'ENCARREGADO',
  'ELETRICISTA',
  'MOTORISTA',
  'AUXILIAR DE ELETRICISTA',
  'PODADOR'
]

// "FULANO em 25/09/2026" (login): quem marcou o colaborador como afastado e quando
// (ver migrations/014). Afastamentos anteriores a esse registro vêm vazios.
export function descreverAfastadoPor(pessoa) {
  if (!pessoa?.afastado_por) {
    return pessoa?.afastado ? 'Não registrado' : ''
  }
  const data = pessoa.afastado_em ? new Date(pessoa.afastado_em) : null
  if (!data || Number.isNaN(data.getTime())) {
    return pessoa.afastado_por
  }
  return `${pessoa.afastado_por} em ${data.toLocaleDateString('pt-BR')}`
}

// Motivo de estar fora de operação: "Afastado" ou "Desligamento em 25/09/2026"
// (ver migrations/027). Vazio para quem está em operação.
//
// Quem não é Administrador, Gerente ou Coordenador não vê o motivo (o servidor
// nem manda os dados): `veMotivo` false só mostra que a pessoa está fora de
// operação.
export function descreverMotivoForaOperacao(pessoa, veMotivo = true) {
  if (!veMotivo) {
    return pessoa?.afastado ? 'Fora de operação' : ''
  }
  if (pessoa?.desligado) {
    const [ano, mes, dia] = String(pessoa.data_desligamento || '').split('-')
    return ano && mes && dia
      ? `Desligamento em ${dia}/${mes}/${ano}`
      : 'Desligamento'
  }
  return pessoa?.afastado ? 'Afastado' : ''
}

// "FULANO em 25/09/2026" (login): quem escreveu a observação do colaborador
// e quando (ver migrations/019).
export function descreverObservacaoPor(pessoa) {
  if (!pessoa?.observacao_por) {
    return ''
  }
  const data = pessoa.observacao_em ? new Date(pessoa.observacao_em) : null
  if (!data || Number.isNaN(data.getTime())) {
    return pessoa.observacao_por
  }
  return `${pessoa.observacao_por} em ${data.toLocaleDateString('pt-BR')}`
}

// "FULANO em 25/09/2026" (login): quem trocou DIRETO/INDIRETO na tela e
// quando (ver migrations/015). Quem só veio da planilha fica vazio.
export function descreverTipoFuncaoAlteradoPor(pessoa) {
  if (!pessoa?.tipo_funcao_alterado_por) {
    return ''
  }
  const data = pessoa.tipo_funcao_alterado_em ? new Date(pessoa.tipo_funcao_alterado_em) : null
  if (!data || Number.isNaN(data.getTime())) {
    return pessoa.tipo_funcao_alterado_por
  }
  return `${pessoa.tipo_funcao_alterado_por} em ${data.toLocaleDateString('pt-BR')}`
}

// ------------------------------------------------------------
// Filtros que se reconhecem (em cascata)
// ------------------------------------------------------------
//
// Ao abrir um filtro, as opções são só as que ainda existem com os OUTROS
// filtros já escolhidos: filtrando o coordenador JACKSON, o filtro de base
// lista só as bases dele. Cada filtro ignora a si mesmo (senão escolher um valor
// escondia os demais valores do mesmo filtro).

function valoresAtivos(selecao, valorTodos) {
  const lista = Array.isArray(selecao) ? selecao : selecao ? [selecao] : []
  return lista.filter(valor => valor && valor !== valorTodos)
}

// As equipes com SÓ as vagas que batem com os filtros, exceto o da dimensão
// 'ignorar' ('base' | 'tipo' | 'setor' | 'coordenador' | 'supervisor').
// 'aceita' é um filtro extra opcional por equipe (ex.: só ativas, só extras).
// Tipo, setor, coordenador e supervisor valem por vaga, como nas telas.
export function equipesParaOpcoes(equipes, filtros, ignorar, aceita) {
  const bases = valoresAtivos(filtros.base, OPCAO_TODAS_BASES)
  const tipos = valoresAtivos(filtros.tipo, TIPO_TODOS)
  const setores = valoresAtivos(filtros.setor, SETOR_TODOS)
  const coordenadores = valoresAtivos(filtros.coordenador, RESPONSAVEL_TODOS)
  const supervisores = valoresAtivos(filtros.supervisor, RESPONSAVEL_TODOS)

  const filtraPorVaga =
    (ignorar !== 'tipo' && tipos.length) ||
    (ignorar !== 'setor' && setores.length) ||
    (ignorar !== 'coordenador' && coordenadores.length) ||
    (ignorar !== 'supervisor' && supervisores.length)

  const resultado = []

  for (const equipe of equipes || []) {
    if (aceita && !aceita(equipe)) {
      continue
    }
    if (ignorar !== 'base' && bases.length && !bases.includes(String(equipe.base || '').trim())) {
      continue
    }

    const vagas = (equipe.vagas || []).filter(
      vaga =>
        (ignorar === 'tipo' ||
          !tipos.length ||
          tipos.some(t => (t === TIPO_FOLGUISTA ? ehEquipeFolguista(equipe) : t === vaga.tipo))) &&
        (ignorar === 'setor' || !setores.length || setores.includes(vaga.setor)) &&
        (ignorar === 'coordenador' || !coordenadores.length || coordenadores.includes(vaga.coordenador)) &&
        (ignorar === 'supervisor' || !supervisores.length || supervisores.includes(vaga.supervisor))
    )

    if (filtraPorVaga && !vagas.length) {
      continue
    }

    resultado.push({
      ...equipe,
      vagas,
      tipos: [...new Set(vagas.map(vaga => vaga.tipo).filter(Boolean))],
      setores: [...new Set(vagas.map(vaga => vaga.setor).filter(Boolean))]
    })
  }

  return resultado
}

// Quem já está escolhido continua na lista mesmo que os outros filtros o
// tenham tirado das opções, para dar para desmarcar.
export function manterSelecionadas(opcoes, selecao, valorTodos, rotuloDe = valor => valor) {
  const existentes = new Set(opcoes.map(opcao => opcao.value))
  const faltando = valoresAtivos(selecao, valorTodos)
    .filter(valor => !existentes.has(valor))
    .map(valor => ({ label: rotuloDe(valor), value: valor }))
  return [...opcoes, ...faltando]
}
