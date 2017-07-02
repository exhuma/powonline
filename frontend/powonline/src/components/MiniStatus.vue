<template>
  <v-icon>{{ stateIcon }}</v-icon>
</template>

<script>
import axios from 'axios'
export default {
  name: 'mini-status',
  props: ['team', 'station'],
  data () {
    return {
      state: 'unknown',
      stateIcon: 'u'
    }
  },
  created () {
    const baseUrl = this.$store.state.baseUrl
    axios.get(baseUrl + '/station/' + this.station + '/teams/' + this.team)
    .then(response => {
      switch (response.data.state) {
        case 'unknown':
          this.stateIcon = 'radio_button_unchecked'
          break
        case 'arrived':
          this.stateIcon = 'radio_button_checked'
          break
        case 'finished':
          this.stateIcon = 'check'
          break
        default:
          this.stateIcon = 'radio_button_unchecked'
          break
      }
    })
    .catch(e => {
      this.$store.commit('logError', e)
    })
  },
  computed: {
    teamState () {
      return this.$store.getters.teamState(this.team, this.station)
    }
  }
}
</script>
