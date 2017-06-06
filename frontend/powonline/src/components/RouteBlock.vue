<template>
  <div class="route-block">
    {{ name }}
    <button @click="deleteRoute">Delete</button>

    <hr />

    <h2>Teams assigned to this route</h2>
    <li v-for="(team, idx) in assignedTeams">{{ team.name }}<button @click="unassign" :data-idx="idx">Unassign</button></li>

    <h2>Teams not assigned to any route</h2>
    <li v-for="(team, idx) in unassignedTeams">{{ team.name }}<button @click="assign" :data-idx="idx">Assign</button></li>
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
  created () {
    this.refresh_unassigned()
    this.refresh_assigned()
  },
  data () {
    return {
      unassignedTeams: [],
      assignedTeams: []
    }
  },
  methods: {
    unassign: function (event) {
      const idx = event.target.getAttribute('data-idx')
      const obj = this.assignedTeams[idx]
      axios.delete('http://192.168.1.92:5000/route/' + this.name + '/teams/' + obj.name)
      .then(response => {
        this.refresh_assigned()   // TODO use an event for this
        this.refresh_unassigned() // TODO use an event for this
      })
      .catch(e => {
        if (e.response.status === 400) {
          for (var key in e.response.data) {
            this.errors.push({message: e.response.data[key] + ': ' + key})
          }
        }
      })
    },
    assign: function (event) {
      const idx = event.target.getAttribute('data-idx')
      const obj = this.unassignedTeams[idx]
      axios.post('http://192.168.1.92:5000/route/' + this.name + '/teams', obj)
      .then(response => {
        this.refresh_assigned()   // TODO use an event for this
        this.refresh_unassigned() // TODO use an event for this
      })
      .catch(e => {
        if (e.response.status === 400) {
          for (var key in e.response.data) {
            this.errors.push({message: e.response.data[key] + ': ' + key})
          }
        }
      })
    },
    deleteRoute: function (event) {
      axios.delete('http://192.168.1.92:5000/route/' + this.name)
      .then(response => {
        console.log(response)
        this.$emit('listChanged')
      })
      .catch(e => {
        if (e.response.status === 400) {
          for (var key in e.response.data) {
            this.errors.push({message: e.response.data[key] + ': ' + key})
          }
        }
      })
    },
    refresh_assigned: function () {
      axios.get('http://192.168.1.92:5000/team?assigned_station=' + this.name)
      .then(response => {
        this.assignedTeams = response.data.items
      })
      .catch(e => {
        if (e.response.status === 400) {
          for (var key in e.response.data) {
            this.errors.push({message: e.response.data[key] + ': ' + key})
          }
        }
      })
    },
    refresh_unassigned: function () {
      axios.get('http://192.168.1.92:5000/team?quickfilter=unassigned')
      .then(response => {
        this.unassignedTeams = response.data.items
      })
      .catch(e => {
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
