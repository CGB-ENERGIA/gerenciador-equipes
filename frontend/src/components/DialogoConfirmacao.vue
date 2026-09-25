<template>
  <q-dialog
    :model-value="estado.aberto"
    @update:model-value="aberto => !aberto && responder(false)"
  >
    <q-card style="min-width: 360px; max-width: 90vw">
      <q-card-section class="row items-center no-wrap">
        <q-icon
          :name="estado.perigo ? 'warning' : 'help_outline'"
          :color="estado.perigo ? 'negative' : 'primary'"
          size="28px"
          class="q-mr-sm"
        />
        <div class="text-h6">{{ estado.titulo }}</div>
      </q-card-section>

      <q-separator />

      <q-card-section class="mensagem-confirmacao">
        {{ estado.mensagem }}
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat label="Cancelar" @click="responder(false)" />
        <q-btn
          :color="estado.perigo ? 'negative' : 'primary'"
          :label="estado.textoConfirmar"
          @click="responder(true)"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { useConfirmacao } from '../composables/useConfirmacao'

const { estado, responder } = useConfirmacao()
</script>

<style scoped>
/* as mensagens trazem listas montadas com \n (vagas, equipes afetadas) */
.mensagem-confirmacao {
  white-space: pre-line;
}
</style>
