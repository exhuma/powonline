<template>
  <v-card class="mt-3">
    <v-card-row class="green darken-1">
      <v-card-title><span class="white--text">Team: "{{ name }}"</span></v-card-title>
    </v-card-row>
    <v-card-text>
      <mini-status
        :station="station.name"
        :team="name"
        :key="name + station.name"
        v-for="station in stations"></mini-status>
    </v-card-text>
    <v-divider></v-divider>
    <v-card-row actions>
      <v-btn flat class="green--text darken-1" @click.native="deleteTeam">Delete</v-btn>
    </v-card-row>
  </v-card>
</template>

<script>
export default {
  name: 'team-block',
  props: {
    'name': {
      type: String,
      default: 'Unknown Team'
    }
  },
  computed: {
    stations () {
      return this.$store.state.stations
    }
  },
  methods: {
    deleteTeam: function (event) {
      this.$store.dispatch('deleteTeamRemote', this.name)
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.team-block {
  border: 1px solid black;
  padding: 1em;
}

</style>
