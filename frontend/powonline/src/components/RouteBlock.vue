<template>
  <v-card class="mt-3">
    <v-card-row class="brown darken-1">
      <v-card-title><span class="white--text">Route: "{{ name }}"</span></v-card-title>
    </v-card-row>
    <v-card-text>
      <v-layout row wrap>
        <!-- Assigned Items -->
        <v-flex xs6>
          <v-card class="mx-3">
            <v-card-row class="brown lighten-2">
              <v-card-title>Assigned Teams</v-card-title>
            </v-card-row>
            <v-card-row v-for="(team, idx) in assignedTeams" :key="idx">
              <v-flex xs6>{{ team }}</v-flex>
              <v-flex xs6>
                <v-btn @click.native="unassignTeam" :data-idx="idx" flat><v-icon>arrow_downward</v-icon></v-btn>
              </v-flex>
            </v-card-row>
          </v-card>
        </v-flex>
        <v-flex xs6>
          <v-card class="mx-3">
            <v-card-row class="brown lighten-2">
              <v-card-title>Assigned Stations</v-card-title>
            </v-card-row>
            <v-card-row v-for="(station, idx) in assignedStations" :key="idx">
              <v-flex xs6>{{ station }}</v-flex>
              <v-flex xs6>
                <v-btn @click.native="unassignStation" :data-idx="idx" flat><v-icon>arrow_downward</v-icon></v-btn>
              </v-flex>
            </v-card-row>
          </v-card>
        </v-flex>

        <!-- Unassigned Items -->
        <v-flex xs6 class="mt-4"> 
          <v-card class="mx-3">
            <v-card-row class="brown lighten-2">
              <v-card-title>Unassigned Teams</v-card-title>
            </v-card-row>
            <v-card-row v-for="(team, idx) in unassignedTeams" :key="idx">
              <v-flex xs6>{{ team }}</v-flex>
              <v-flex xs6>
                <v-btn @click.native="assignTeam" :data-idx="idx" flat><v-icon>arrow_upward</v-icon></v-btn>
              </v-flex>
            </v-card-row>
          </v-card>
        </v-flex>
        <v-flex xs6 class="mt-4">
          <v-card class="mx-3">
            <v-card-row class="brown lighten-2">
              <v-card-title>Unassigned Stations</v-card-title>
            </v-card-row>
            <v-card-row v-for="(station, idx) in unassignedStations" :key="idx">
              <v-flex xs6>{{ station }}</v-flex>
              <v-flex xs6>
                <v-btn @click.native="assignStation" :data-idx="idx" flat><v-icon>arrow_upward</v-icon></v-btn>
              </v-flex>
            </v-card-row>
          </v-card>
        </v-flex>
      </v-layout>
    </v-card-text>
    <v-divider></v-divider>
    <v-card-row actions>
      <v-btn flat class="brown--text darken-1" @click.native="deleteRoute">Delete</v-btn>
    </v-card-row>
  </v-card>
</template>

<script>
export default {
  name: 'route-block',
  props: {
    'name': {
      type: String,
      default: 'Unknown Route'
    }
  },
  computed: {
    assignedTeams () {
      return this.$store.getters.assignedTeams(this.name)
    },
    unassignedTeams () {
      return this.$store.getters.unassignedTeams
    },
    assignedStations () {
      return this.$store.getters.assignedStations(this.name)
    },
    unassignedStations () {
      return this.$store.getters.unassignedStations(this.name)
    }
  },
  methods: {
    unassignTeam: function (event) {
      const idx = event.target.getAttribute('data-idx')
      const team = this.assignedTeams[idx]
      this.$store.dispatch('unassignTeamFromRouteRemote', {teamName: team, routeName: this.name})
    },
    assignTeam: function (event) {
      const idx = event.target.getAttribute('data-idx')
      const team = this.unassignedTeams[idx]
      this.$store.dispatch('assignTeamToRouteRemote', {teamName: team, routeName: this.name})
    },
    unassignStation: function (event) {
      const idx = event.target.getAttribute('data-idx')
      const station = this.assignedStations[idx]
      this.$store.dispatch('unassignStationFromRouteRemote', {stationName: station, routeName: this.name})
    },
    assignStation: function (event) {
      const idx = event.target.getAttribute('data-idx')
      const station = this.unassignedStations[idx]
      this.$store.dispatch('assignStationToRouteRemote', {stationName: station, routeName: this.name})
    },
    deleteRoute: function (event) {
      this.$store.dispatch('deleteRouteRemote', this.name)
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.route-block {
  border: 1px solid black;
  padding: 1em;
}

</style>
