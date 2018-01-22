<template>
  <v-card class="mt-3">
    <v-card-title><span>Route: "{{ name }}"</span></v-card-title>
    <v-card-text>
      <v-layout row wrap>
        <!-- Assigned Items -->
        <v-flex xs6>
          <v-card class="mx-3">
            <v-card-title>Assigned Teams</v-card-title>
            <div v-for="(team, idx) in assignedTeams" :key="idx">
              <v-flex xs6>{{ team }}</v-flex>
              <v-flex xs6>
                <v-btn @click="unassignTeam(team)" flat><v-icon>arrow_downward</v-icon></v-btn>
              </v-flex>
            </div>
          </v-card>
        </v-flex>
        <v-flex xs6>
          <v-card class="mx-3">
            <v-card-title>Assigned Stations</v-card-title>
            <div v-for="(station, idx) in assignedStations" :key="idx">
              <v-flex xs6>{{ station }}</v-flex>
              <v-flex xs6>
                <v-btn @click="unassignStation(station)" flat><v-icon>arrow_downward</v-icon></v-btn>
              </v-flex>
            </div>
          </v-card>
        </v-flex>

        <!-- Unassigned Items -->
        <v-flex xs6 class="mt-4"> 
          <v-card class="mx-3">
            <v-card-title>Unassigned Teams</v-card-title>
            <div v-for="(team, idx) in unassignedTeams" :key="idx">
              <v-flex xs6>{{ team }}</v-flex>
              <v-flex xs6>
                <v-btn @click="assignTeam(team)" flat><v-icon>arrow_upward</v-icon></v-btn>
              </v-flex>
            </div>
          </v-card>
        </v-flex>
        <v-flex xs6 class="mt-4">
          <v-card class="mx-3">
            <v-card-title>Unassigned Stations</v-card-title>
            <div v-for="(station, idx) in unassignedStations" :key="idx">
              <v-flex xs6>{{ station }}</v-flex>
              <v-flex xs6>
                <v-btn @click="assignStation(station)" flat><v-icon>arrow_upward</v-icon></v-btn>
              </v-flex>
            </div>
          </v-card>
        </v-flex>
      </v-layout>
    </v-card-text>
    <v-divider></v-divider>
    <v-card-actions v-if="hasRole('admin')">
      <confirmation-dialog buttonText="Delete" :actionArgument="name" actionName="deleteRouteRemote">
        <v-card-title slot="title">Do you want to delete the route "{{ name }}"?</v-card-title>
        <v-card-text slot="text">
          <p>this will delete the route with the name "{{ name }}" and all
            related information!</p>
          <p>Are you sure?</p>
        </v-card-text>
      </confirmation-dialog>
    </v-card-actions>
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
    unassignTeam: function (team) {
      this.$store.dispatch('unassignTeamFromRouteRemote', {teamName: team, routeName: this.name})
    },
    assignTeam: function (team) {
      this.$store.dispatch('assignTeamToRouteRemote', {teamName: team, routeName: this.name})
    },
    unassignStation: function (station) {
      this.$store.dispatch('unassignStationFromRouteRemote', {stationName: station, routeName: this.name})
    },
    assignStation: function (station) {
      this.$store.dispatch('assignStationToRouteRemote', {stationName: station, routeName: this.name})
    },
    hasRole (roleName) {
      return this.$store.state.roles.indexOf(roleName) > -1
    }
  }
}
</script>
