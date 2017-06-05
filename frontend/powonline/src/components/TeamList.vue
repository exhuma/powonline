<template>
  <div id="TeamList">
    <h1>Team List</h1>
    <input 
      id="TeamNameImput"
      @keyup.enter="addTeam"
      type='text'
      v-model:teamname='teamname'
      placeholder='Enter a new teamname' />
    <button @click="addTeam">Add</button>
    <hr />
    <team-block v-on:listChanged="refresh" v-for="team in teams" :name="team.name" :key="team.name"></team-block>
    <hr />
    <ul v-if="errors && errors.length">
      <li v-for="error of errors">
        {{error.message}}
      </li>
    </ul>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'team_list',
  methods: {
    addTeam: function (event) {
      axios.post('http://192.168.1.92:5000/team', {
        name: this.teamname
      })
      .then(response => {
        this.teams = response.data.items
        console.log(response)
        this.refresh()
        const input = document.getElementById('TeamNameImput')
        input.focus()
        input.select()
      })
      .catch(e => {
        if (e.response && e.response.status === 400) {
          for (var key in e.response.data) {
            this.errors.push({message: e.response.data[key] + ': ' + key})
          }
        } else {
          console.log(e)
        }
      })
    },
    refresh: function (event) {
      axios.get('http://192.168.1.92:5000/team')
      .then(response => {
        this.teams = response.data.items
        console.log(response)
      })
      .catch(e => {
        this.errors.push(e)
      })
    }
  },
  created () {
    this.refresh()
  },
  data () {
    return {
      errors: [],
      teamname: 'default',
      teams: []
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h1, h2 {
  font-weight: normal;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  display: inline-block;
  margin: 0 10px;
}

a {
  color: #42b983;
}
</style>
