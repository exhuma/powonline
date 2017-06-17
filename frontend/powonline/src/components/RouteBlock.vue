<template>
  <div class="route-block">
    {{ name }}
    <button @click="deleteRoute">Delete</button>

    <hr />

    <table>
      <tr>
        <td>
          <h2>Teams assigned to this route</h2>
          <li v-for="(team, idx) in assignedTeams">{{ team }}<button @click="unassignTeam" :data-idx="idx">Unassign</button></li>

          <h2>Teams not assigned to any route</h2>
          <li v-for="(team, idx) in unassignedTeams">{{ team }}<button @click="assignTeam" :data-idx="idx">Assign</button></li>
        </td>
        <td>
          <h2>Stations assigned to this route</h2>
          <li v-for="(station, idx) in assignedStations">{{ station }}<button @click="unassignStation" :data-idx="idx">Unassign</button></li>

          <h2>Stations not assigned to this route</h2>
          <li v-for="(station, idx) in unassignedStations">{{ station }}<button @click="assignStation" :data-idx="idx">Assign</button></li>
        </td>
      </tr>
    </table>

  </div>
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
