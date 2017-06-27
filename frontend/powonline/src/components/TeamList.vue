<template>
  <div id="TeamList">
    <v-text-field
      name="team-input"
      id="TeamNameImput"
      @keyup.enter.native="addTeam"
      type='text'
      v-model:teamname='teamname'
      label='Enter a new teamname' />
    <v-text-field
      name="email-input"
      id="EmailInput"
      type='text'
      v-model:email='email'
      label='Enter a new email' />
    <v-btn v-on:click="addTeam">Add</v-btn>
    <hr />
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
  created () {
    this.$store.commit('changeTitle', 'Team List')
  },
  data () {
    return {
      teamname: '',
      email: ''
    }
  },
  computed: {
    teams () {
      return this.$store.state.teams
    }
  }
}
</script>
