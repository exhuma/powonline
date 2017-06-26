<template>
  <div id="TeamList">
    <h1>Team List</h1>
    <input 
      id="TeamNameImput"
      @keyup.enter="addTeam"
      type='text'
      v-model:teamname='teamname'
      placeholder='Enter a new teamname' />
    <input 
      id="EmailInput"
      type='text'
      v-model:email='email'
      placeholder='Enter a new email' />
    <button @click="addTeam">Add</button>
    <hr />
    <div>
      <v-btn dark default>Normal</v-btn>
    </div>
    <team-block v-for="team in teams" :name="team.name" :key="team.name"></team-block>
  </div>
</template>

<script>
export default {
  name: 'team_list',
  methods: {
    addTeam: function (event) {
      this.$store.dispatch('addTeamRemote', {
        name: this.teamname,
        email: this.email,
        order: 500,
        cancelled: false,
        is_confirmed: true,  // <- because it's added via the admin interface
        accepted: true,  // <- because it's added via the admin interface
        completed: false,
        inserted: '2000-01-01 10:00:00',
        confirmation_key: ''
      })
      const input = document.getElementById('TeamNameImput')
      input.focus()
      input.select()
    }
  },
  data () {
    return {
      teamname: 'default',
      email: 'john.doe@example.com'
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
