<template>
  <div class="route-block">
    {{ name }}
    <button @click="deleteRoute">Delete</button>

    <hr />

    <h2>Teams assigned to this route</h2>
    <li v-for="(team, idx) in assignedTeams">{{ team }}<button @click="unassign" :data-idx="idx">Unassign</button></li>

    <h2>Teams not assigned to any route</h2>
    <li v-for="(team, idx) in unassignedTeams">{{ team }}<button @click="assign" :data-idx="idx">Assign</button></li>
  </div>
</template>

<script>
import axios from 'axios'
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
    }
  },
  methods: {
    unassign: function (event) {
      const idx = event.target.getAttribute('data-idx')
      const team = this.assignedTeams[idx]
      this.$store.dispatch('unassignTeamFromRouteRemote', {teamName: team, routeName: this.name})
    },
    assign: function (event) {
      const idx = event.target.getAttribute('data-idx')
      const team = this.unassignedTeams[idx]
      this.$store.dispatch('assignTeamToRouteRemote', {teamName: team, routeName: this.name})
    },
    deleteRoute: function (event) {
      axios.delete('http://192.168.1.92:5000/route/' + this.name)
      .then(response => {
        this.$emit('listChanged')
      })
      .catch(e => {
        // TODO use an event for this
        if (e.response.status === 400) {
          for (var key in e.response.data) {
            this.errors.push({message: e.response.data[key] + ': ' + key})
          }
        }
      })
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
