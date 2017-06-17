<template>
  <div id="StationList">
    <h1>Dashboard for {{ $route.params.stationName }}</h1>
    <p v-for="(state, idx) in states">
      {{ state.team }} -
      {{ state.score }} -
      {{ state.state }}
      <br />
      <button @click="advanceState" :data-idx="idx">Advance</button>
    </p>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'station_dashboard',
  created () {
    this.update()
  },
  data () {
    return {
      states: []
    }
  },
  methods: {
    update: function (event) {
      this.states = []
      const baseUrl = this.$store.state.baseUrl
      axios.get(baseUrl + '/station/' + this.$route.params.stationName + '/dashboard')
      .then(response => {
        response.data.forEach(state => {
          this.states.push(state)
        })
      }) // TODO better error handling
    },
    advanceState: function (event) {
      const state = this.states[event.target.getAttribute('data-idx')]
      this.$store.dispatch('advanceState', {
        teamName: state['team'],
        stationName: this.$route.params.stationName})
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped></style>
