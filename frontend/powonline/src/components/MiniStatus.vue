<template>
  <div class="mini-status">
    {{ stateIcon }}
  </div>
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
          this.stateIcon = 'u'
          break
        case 'arrived':
          this.stateIcon = 'a'
          break
        case 'finished':
          this.stateIcon = 'f'
          break
        default:
          this.stateIcon = 'u'
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

<style scoped>
  DIV {
    width: 32px;
    height: 32px;
    border: 1px solid black;
    display: inline-block;
  }
</style>
