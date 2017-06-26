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
export default {
  name: 'station_dashboard',
  computed: {
    states () {
      return this.$store.state.dashboard
    }
  },
  created () {
    this.$store.dispatch('fetchDashboard', this.$route.params.stationName)
  },
  methods: {
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
