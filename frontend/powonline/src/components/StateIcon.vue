<template>
  <v-icon>{{ stateIcon }}</v-icon>
</template>

<script>
export default {
  name: 'state-icon',
  props: ['state'],
  computed: {
    stateIcon () {
      switch (this.state) {
        case 'unknown':
          return 'radio_button_unchecked'
        case 'arrived':
          return 'radio_button_checked'
        case 'finished':
          return 'check'
      }
    }
  }
}
</script>
