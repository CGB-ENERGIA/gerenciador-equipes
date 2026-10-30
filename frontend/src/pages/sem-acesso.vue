<template>
  <q-layout view="lHh Lpr lFf">
    <MarcaDaguaFundo />

    <CabecalhoApp
      titulo="Sem acesso"
      :carregando="carregando"
      @atualizar="verificarNovamente"
    />

    <q-page-container>
      <q-page class="q-pa-md flex flex-center">
        <div class="text-center" style="max-width: 460px">
          <q-icon name="lock" size="48px" color="grey-6" />

          <div class="text-h6 q-mt-md">
            {{ usuario?.sem_vinculo ? 'Sua conta ainda não tem vínculo' : 'Sem acesso a esta página' }}
          </div>

          <div class="text-body2 text-grey-7 q-mt-sm">
            {{
              usuario?.sem_vinculo
                ? 'Os dados das equipes e dos colaboradores ficam disponíveis depois que um Administrador vincular sua conta a uma base, equipe ou setor.'
                : 'Seu nível de acesso não inclui esta página. Fale com um Administrador.'
            }}
          </div>

          <q-btn
            class="q-mt-lg"
            color="primary"
            label="Verificar novamente"
            no-caps
            :loading="carregando"
            @click="verificarNovamente"
          />
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import CabecalhoApp from '../components/CabecalhoApp.vue'
import MarcaDaguaFundo from '../components/MarcaDaguaFundo.vue'
import { useSessao } from '../composables/useSessao'

const { usuario, buscarSessao } = useSessao()
const router = useRouter()

const carregando = ref(false)

// o vínculo pode ter sido criado depois do login: relê a sessão e tenta o início
async function verificarNovamente() {
  carregando.value = true

  try {
    await buscarSessao()
    await router.replace('/')
  } finally {
    carregando.value = false
  }
}
</script>
