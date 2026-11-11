<template>
  <q-header elevated class="site-header text-white">
    <q-toolbar>
      <q-btn
        flat
        round
        dense
        icon="menu"
        class="q-mr-xs"
        :aria-label="menuAberto && !recolhidoEfetivo ? 'Recolher menu' : 'Abrir menu'"
        @click="alternarMenu"
      />

      <div class="site-logo q-mr-sm">
        <img src="/icons/logo-cabecalho.png" alt="CGB Energia" />
      </div>

      <q-toolbar-title> {{ titulo }} </q-toolbar-title>

      <q-btn
        flat
        round
        dense
        icon="refresh"
        aria-label="Atualizar"
        :loading="carregando"
        @click="emit('atualizar')"
      >
        <q-tooltip>Atualizar</q-tooltip>
      </q-btn>

      <q-btn
        flat
        round
        dense
        :icon="modoNoturno ? 'light_mode' : 'dark_mode'"
        :aria-label="modoNoturno ? 'Ativar modo claro' : 'Ativar modo noturno'"
        @click="alternarModoNoturno"
      >
        <q-tooltip>{{ modoNoturno ? 'Modo claro' : 'Modo noturno' }}</q-tooltip>
      </q-btn>

      <!-- ============================================== -->
      <!-- USUÁRIO LOGADO -->
      <!-- ============================================== -->

      <q-btn-dropdown
        v-if="usuario"
        flat
        no-caps
        auto-close
        class="q-ml-sm"
        :label="usuario.usuario"
        icon="account_circle"
        aria-label="Conta"
      >
        <q-list>
          <q-item>
            <q-item-section>
              <q-item-label class="text-weight-medium">
                {{ usuario.nome }}
              </q-item-label>
              <q-item-label caption>{{ usuario.nivel_rotulo }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-separator />

          <q-item v-close-popup clickable @click="abrirAjuda">
            <q-item-section avatar>
              <q-icon name="help_outline" />
            </q-item-section>
            <q-item-section>Ajuda</q-item-section>
          </q-item>

          <q-separator />

          <q-item v-close-popup clickable @click="abrirTrocaSenha">
            <q-item-section avatar>
              <q-icon name="key" />
            </q-item-section>
            <q-item-section>Trocar minha senha</q-item-section>
          </q-item>

          <q-item v-close-popup clickable @click="encerrar">
            <q-item-section avatar>
              <q-icon name="logout" />
            </q-item-section>
            <q-item-section>Sair</q-item-section>
          </q-item>
        </q-list>
      </q-btn-dropdown>
    </q-toolbar>
  </q-header>

  <!-- ================================================== -->
  <!-- MENU LATERAL (recolhe para só ícones no computador; -->
  <!-- no celular abre por cima pelo botão ☰)              -->
  <!-- ================================================== -->

  <q-drawer
    v-model="menuAberto"
    show-if-above
    bordered
    side="left"
    :width="232"
    :mini="recolhidoEfetivo"
    :mini-width="60"
    :breakpoint="LARGURA_MENU_FIXO"
    class="menu-lateral"
  >
    <div class="menu-lateral__conteudo">
      <q-list class="menu-lateral__lista">
        <q-item
          v-for="pagina in paginasPermitidas"
          :key="pagina.rota"
          clickable
          :active="ehPaginaAtual(pagina)"
          active-class="menu-lateral__item--ativo"
          class="menu-lateral__item"
          @click="navegar(pagina)"
        >
          <q-item-section avatar>
            <q-icon :name="pagina.icone" size="20px" />
          </q-item-section>
          <q-item-section>{{ pagina.titulo }}</q-item-section>
          <q-tooltip v-if="recolhidoEfetivo" anchor="center right" self="center left" :offset="[8, 0]">
            {{ pagina.titulo }}
          </q-tooltip>
        </q-item>
      </q-list>

      <q-item
        v-if="$q.screen.width >= LARGURA_MENU_FIXO"
        clickable
        class="menu-lateral__item menu-lateral__recolher"
        @click="recolhido = !recolhido"
      >
        <q-item-section avatar>
          <q-icon :name="recolhido ? 'chevron_right' : 'chevron_left'" size="20px" />
        </q-item-section>
        <q-item-section>Recolher menu</q-item-section>
        <q-tooltip v-if="recolhidoEfetivo" anchor="center right" self="center left" :offset="[8, 0]">
          Expandir menu
        </q-tooltip>
      </q-item>
    </div>
  </q-drawer>

  <!-- ================================================== -->
  <!-- TROCA DE SENHA -->
  <!-- ================================================== -->

  <q-dialog v-model="dialogSenha">
    <q-card style="width: 100%; max-width: 380px">
      <q-card-section class="row items-center q-pb-sm">
        <div class="text-h6">Trocar minha senha</div>
        <q-space />
        <q-btn v-close-popup flat round dense icon="close" />
      </q-card-section>

      <q-separator />

      <q-card-section class="q-gutter-md">
        <q-banner v-if="erroSenha" dense class="bg-red-1 text-negative" rounded>
          {{ erroSenha }}
        </q-banner>

        <q-banner v-if="okSenha" dense class="bg-green-1 text-positive" rounded>
          {{ okSenha }}
        </q-banner>

        <q-input
          v-model="senhaAtual"
          outlined
          dense
          type="password"
          autocomplete="current-password"
          label="Senha atual"
        />

        <q-input
          v-model="senhaNova"
          outlined
          dense
          type="password"
          autocomplete="new-password"
          label="Nova senha"
          hint="Mínimo de 6 caracteres"
        />

        <q-input
          v-model="senhaConfirma"
          outlined
          dense
          type="password"
          autocomplete="new-password"
          label="Repita a nova senha"
        />
      </q-card-section>

      <q-separator />

      <q-card-actions align="right">
        <q-btn v-close-popup flat label="Cancelar" />
        <q-btn
          color="primary"
          label="Salvar"
          :loading="salvandoSenha"
          :disable="!senhaAtual || !senhaNova || !senhaConfirma"
          @click="salvarSenha"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useQuasar } from 'quasar'
import { LARGURA_MENU_FIXO, useMenuLateral } from '../composables/useMenuLateral'

import { useRoute, useRouter } from 'vue-router'
import { useModoNoturno } from '../composables/useModoNoturno'
import {
  PODE_GERENCIAR_COLABORADORES,
  PODE_GERENCIAR_USUARIOS,
  PODE_GERENCIAR_VAGAS,
  PODE_VER_EQUIPES,
  PODE_VER_RESUMO,
  useSessao
} from '../composables/useSessao'

defineProps({
  titulo: {
    type: String,
    required: true
  },
  carregando: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['atualizar'])

const $q = useQuasar()
const { menuAberto, recolhido } = useMenuLateral()

// recolher (só ícones) vale para o computador; no celular o menu abre inteiro
const recolhidoEfetivo = computed(() => recolhido.value && $q.screen.width >= LARGURA_MENU_FIXO)

function alternarMenu() {
  if ($q.screen.width >= LARGURA_MENU_FIXO) {
    if (!menuAberto.value) {
      menuAberto.value = true
      recolhido.value = false
    } else {
      recolhido.value = !recolhido.value
    }
  } else {
    menuAberto.value = !menuAberto.value
  }
}

const router = useRouter()
const route = useRoute()
const { modoNoturno, alternarModoNoturno, restaurarModoNoturno } = useModoNoturno()
const { usuario, temPermissao, sair } = useSessao()

const PAGINAS = [
  {
    titulo: 'Resumo',
    rota: '/',
    caminhos: ['/', '/resumo'],
    icone: 'assessment',
    permissao: PODE_VER_RESUMO
  },
  {
    titulo: 'Banco de Dados',
    rota: '/banco-dados',
    caminhos: ['/banco-dados'],
    icone: 'storage',
    permissao: PODE_VER_EQUIPES
  },
  {
    titulo: 'Indiretos',
    rota: '/alocacao-indiretos',
    caminhos: ['/alocacao-indiretos'],
    icone: 'groups',
    // todos consultam; editar é só do Administrador (controlado na página)
    permissao: PODE_VER_EQUIPES
  },
  {
    titulo: 'Vagas',
    rota: '/cadastro-vagas',
    caminhos: ['/cadastro-vagas'],
    icone: 'assignment',
    permissao: PODE_GERENCIAR_VAGAS
  },
  {
    titulo: 'Colaboradores',
    rota: '/cadastro-colaboradores',
    caminhos: ['/cadastro-colaboradores'],
    icone: 'badge',
    permissao: PODE_GERENCIAR_COLABORADORES
  },
  {
    titulo: 'Usuários',
    rota: '/usuarios',
    caminhos: ['/usuarios'],
    icone: 'manage_accounts',
    permissao: PODE_GERENCIAR_USUARIOS
  }
]

// o menu mostra só o que o nível da pessoa alcança
const paginasPermitidas = computed(() =>
  PAGINAS.filter(
    pagina =>
      temPermissao(pagina.permissao) &&
      (!pagina.somenteAdministrador || Boolean(usuario.value?.ignora_vinculos))
  )
)

function ehPaginaAtual(pagina) {
  return pagina.caminhos.includes(route.path)
}

function navegar(pagina) {
  if ($q.screen.width < LARGURA_MENU_FIXO) {
    menuAberto.value = false
  }
  if (!ehPaginaAtual(pagina)) {
    router.push(pagina.rota)
  }
}

async function encerrar() {
  await sair()
  router.replace('/login')
}

function abrirAjuda() {
  window.open('/ajuda.html', '_blank', 'noopener')
}

// ============================================================
// TROCA DE SENHA
// ============================================================

const dialogSenha = ref(false)
const senhaAtual = ref('')
const senhaNova = ref('')
const senhaConfirma = ref('')
const salvandoSenha = ref(false)
const erroSenha = ref('')
const okSenha = ref('')

function abrirTrocaSenha() {
  senhaAtual.value = ''
  senhaNova.value = ''
  senhaConfirma.value = ''
  erroSenha.value = ''
  okSenha.value = ''
  dialogSenha.value = true
}

async function salvarSenha() {
  erroSenha.value = ''
  okSenha.value = ''

  if (senhaNova.value !== senhaConfirma.value) {
    erroSenha.value = 'A nova senha e a repetição não conferem.'
    return
  }

  salvandoSenha.value = true

  try {
    const resposta = await fetch('/api/minha-senha', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        senha_atual: senhaAtual.value,
        senha_nova: senhaNova.value
      })
    })

    const dados = await resposta.json()

    if (!resposta.ok || dados.erro) {
      throw new Error(dados.erro || 'Não foi possível alterar a senha.')
    }

    okSenha.value = 'Senha alterada.'
    senhaAtual.value = ''
    senhaNova.value = ''
    senhaConfirma.value = ''
  } catch (e) {
    erroSenha.value = e.message || 'Não foi possível alterar a senha.'
  } finally {
    salvandoSenha.value = false
  }
}

onMounted(restaurarModoNoturno)
</script>

<style>
/* sem scoped: o q-drawer monta fora da raiz deste componente */
.q-drawer__content.menu-lateral {
  background: linear-gradient(180deg, #5a0f1c 0%, #711424 55%, #8d2136 100%);
  color: #fff;
  overflow: hidden;
}

body.body--dark .q-drawer__content.menu-lateral {
  background: linear-gradient(180deg, #2a0a10 0%, #4a0d18 55%, #5e1424 100%);
}

.q-drawer--bordered:has(.menu-lateral) {
  border-right: 0 !important;
}

/* marca d'água bem leve do logo, no pé do menu */
.q-drawer__content.menu-lateral {
  position: relative;
}

.q-drawer__content.menu-lateral::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 70px;
  width: 180px;
  height: 180px;
  transform: translateX(-50%);
  background: url('/icons/logo-fundo.png') center / contain no-repeat;
  filter: brightness(0) invert(1);
  opacity: 0.06;
  pointer-events: none;
}

.q-drawer--mini .menu-lateral::after {
  width: 44px;
  height: 44px;
}

.menu-lateral__conteudo {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 10px 8px;
}

.menu-lateral__lista {
  flex: 1;
}

.menu-lateral__item {
  min-height: 40px;
  margin-bottom: 2px;
  padding: 0 10px;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.82);
  font-size: 14px;
}

.menu-lateral__item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.menu-lateral__item .q-item__section--avatar {
  min-width: 34px;
  color: inherit;
}

.menu-lateral__item .q-focus-helper {
  display: none;
}

.menu-lateral__item--ativo,
body.body--dark .menu-lateral__item--ativo {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  font-weight: 600;
  box-shadow: inset 3px 0 0 #fff;
}

.menu-lateral__recolher {
  color: rgba(255, 255, 255, 0.65);
  font-size: 13px;
  border-top: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 0 0 8px 8px;
  padding-top: 4px;
}

/* recolhido: só o ícone, centralizado */
.q-drawer--mini .menu-lateral__item {
  justify-content: center;
  padding: 0;
}

.q-drawer--mini .menu-lateral__item .q-item__section--avatar {
  min-width: 0;
  padding-right: 0;
}
</style>
