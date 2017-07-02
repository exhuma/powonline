<template>
  <v-card class="mt-3">
    <v-card-row class="brown darken-1">
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
      <confirmation-dialog buttonText="Delete" :actionArgument="name" actionName="deleteTeamRemote">
        <v-card-title slot="title">Do you want to delete the team "{{ name }}"?</v-card-title>
        <v-card-text slot="text">
          <p>this will delete the team with the name "{{ name }}" and all
            related information!</p>
          <p>Are you sure?</p>
        </v-card-text>
      </confirmation-dialog>
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
