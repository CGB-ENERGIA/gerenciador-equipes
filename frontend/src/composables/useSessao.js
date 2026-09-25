import { computed, ref } from 'vue'
import { CHAVE_BASES_SELECIONADAS } from '../utils/equipes'

// Estado fora da função: quem está logado é um dado só, compartilhado por
// todas as telas e pelo guarda de rota.
const usuario = ref(null)
const niveis = ref([])
const tiposVinculo = ref({})
const setoresNegocio = ref([])
const carregada = ref(false)

let carregamentoEmAndamento = null

async function buscarSessao() {
  const resposta = await fetch('/api/sessao')
  const dados = await resposta.json()

  usuario.value = dados.autenticado ? dados.usuario : null
  niveis.value = dados.niveis || []
  tiposVinculo.value = dados.tipos_vinculo || {}
  setoresNegocio.value = dados.setores_negocio || []
  carregada.value = true

  return usuario.value
}

/**
 * Garante que a sessão foi consultada uma vez. Chamadas simultâneas (o guarda
 * de rota e a tela, por exemplo) compartilham a mesma requisição.
 */
async function garantirSessao() {
  if (carregada.value) {
    return usuario.value
  }

  carregamentoEmAndamento =
    carregamentoEmAndamento ||
    buscarSessao().finally(() => {
      carregamentoEmAndamento = null
    })

  return carregamentoEmAndamento
}

async function entrar(login, senha) {
  const resposta = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ usuario: login, senha })
  })

  const dados = await resposta.json()

  if (!resposta.ok || dados.erro) {
    throw new Error(dados.erro || 'Não foi possível entrar.')
  }

  // relê a sessão para trazer também níveis e tipos de vínculo
  await buscarSessao()

  return usuario.value
}

// O filtro de base fica no localStorage, que é do navegador e não da conta.
// Sem o id do usuário na chave, quem entrasse depois no mesmo computador
// herdaria o filtro de quem saiu.
function chaveBasesSelecionadas() {
  const id = usuario.value?.id
  return id == null ? null : `${CHAVE_BASES_SELECIONADAS}_${id}`
}

function lerBasesSelecionadas() {
  const chave = chaveBasesSelecionadas()
  if (!chave) {
    return []
  }
  try {
    const salvo = JSON.parse(localStorage.getItem(chave) || '[]')
    return Array.isArray(salvo) ? salvo : []
  } catch {
    return []
  }
}

function gravarBasesSelecionadas(bases) {
  const chave = chaveBasesSelecionadas()
  if (!chave) {
    return
  }
  try {
    localStorage.setItem(chave, JSON.stringify(bases))
  } catch {
    // sem localStorage (aba anônima, bloqueio): o filtro só não persiste
  }
}

function limparBasesSelecionadas() {
  try {
    const chave = chaveBasesSelecionadas()
    if (chave) {
      localStorage.removeItem(chave)
    }
    // chave antiga, global, gravada antes de o filtro ser separado por conta
    localStorage.removeItem(CHAVE_BASES_SELECIONADAS)
  } catch {
    // nada a limpar se o localStorage não está disponível
  }
}

async function sair() {
  try {
    await fetch('/api/logout', { method: 'POST' })
  } finally {
    limparBasesSelecionadas()
    usuario.value = null
    carregada.value = true
  }
}

/** Chamado quando a API responde 401: a sessão caiu por trás da tela. */
function marcarSessaoExpirada() {
  usuario.value = null
  carregada.value = true
}

export function useSessao() {
  return {
    usuario,
    niveis,
    tiposVinculo,
    setoresNegocio,
    autenticado: computed(() => Boolean(usuario.value)),
    temPermissao: permissao =>
      Boolean(usuario.value?.permissoes?.includes(permissao)),
    garantirSessao,
    buscarSessao,
    entrar,
    sair,
    lerBasesSelecionadas,
    gravarBasesSelecionadas,
    marcarSessaoExpirada
  }
}

// Permissões, iguais às do auth.py
export const PODE_VER_RESUMO = 'ver_resumo'
export const PODE_VER_EQUIPES = 'ver_equipes'
export const PODE_ALOCAR = 'alocar'
export const PODE_EDITAR_ALOCACAO = 'editar_alocacao'
export const PODE_REMOVER_ALOCACAO = 'remover_alocacao'
export const PODE_GERENCIAR_VAGAS = 'gerenciar_vagas'
export const PODE_GERENCIAR_USUARIOS = 'gerenciar_usuarios'
export const PODE_GERENCIAR_COLABORADORES = 'gerenciar_colaboradores'
