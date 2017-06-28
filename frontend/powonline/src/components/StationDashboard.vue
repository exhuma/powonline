<template>
  <div id="Dashboard">
    <v-card v-for="(state, idx) in states" class="mb-2">
      <v-card-row class="brown darken-4">
        <v-card-title>
          <span class="white--text">{{ state.team }}</span>
        </v-card-title>
      </v-card-row>
      <v-card-text v-ripple>
        <state-icon class="clickable" @click.native="advanceState" :data-idx="idx" :state="state.state"></state-icon> <span class="clickable" @click="advanceState" :data-idx="idx">{{ state.state }}</span>
      </v-card-text>
    </v-card>
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
<style scoped>
.clickable {
  cursor: pointer;
}
</style>
