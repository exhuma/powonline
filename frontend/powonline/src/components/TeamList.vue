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
    <team-block v-for="team in teams" :name="team.name" :key="team.name"></team-block>
  </div>
</template>

<script>
export default {
  name: 'team_list',
  methods: {
    addTeam: function (event) {
      this.$store.dispatch('addTeamRemote', {name: this.teamname})
      const input = document.getElementById('TeamNameImput')
      input.focus()
      input.select()
    }
  },
  data () {
    return {
      teamname: 'default'
    }
  },
  computed: {
    teams () {
      return this.$store.state.teams
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
