<template>
  <v-dialog v-model="isDialogVisible" hide-overlay>
    <v-btn primary light slot="activator">{{ buttonText }}</v-btn>
    <v-card>
      <v-card-title><slot name="title">Confirm Action</slot></v-card-title>
      <v-card-text><slot name="text">Are you sure?</slot></v-card-text>
      <v-card-actions>
        <v-btn class="green--text darken-1" flat="flat" @click.native="discardAction">No</v-btn>
        <v-btn class="green--text darken-1" flat="flat" @click.native="acceptAction">Yes</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'confirmation-dialog',
  data () {
    return {
      isDialogVisible: false
    }
  },
  props: [
    'actionArgument',
    'actionName',
    'buttonText'
  ],
  methods: {
    discardAction () {
      this.isDialogVisible = false
    },
    acceptAction () {
      this.$store.dispatch(this.actionName, this.actionArgument)
      this.isDialogVisible = false
    }
  }
}
</script>
