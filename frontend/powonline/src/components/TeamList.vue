<template>
  <div id="TeamList">
    <transition name="slide">
      <v-card v-show="isAddBlockVisible">
        <v-card-title>
          <span>Add New Team</span>
          <v-spacer></v-spacer>
          <v-btn @click.native="closeAddBlock" icon light><v-icon>close</v-icon></v-btn>
        </v-card-title>
        <v-card-text>
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
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions>
          <v-btn @click.native="addTeam" flat>Add</v-btn>
        </v-card-actions>
      </v-card>
    </transition>
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
    },
    closeAddBlock () {
      this.$store.commit('closeAddBlock', this.$route.path)
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
    },
    isAddBlockVisible () {
      return this.$store.state.isAddBlockVisible[this.$route.path]
    }
  }
}
</script>

<style scoped>

#TeamList {
  padding-bottom: 5em;
}

.slide-enter-active, .slide-leave-active {
  transition: all .3s
}
.slide-enter {
  transform: translateY(-100px);
  opacity: 0;
}
.slide-leave-to {
  transform: translateY(-100px);
  opacity: 0;
}
</style>
