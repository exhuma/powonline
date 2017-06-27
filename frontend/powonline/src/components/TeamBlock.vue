<template>
  <div class="team-block">
    {{ name }}
    <button @click.native="deleteTeam">Delete</button>
    <mini-status
      :station="station.name"
      :team="name"
      :key="name + station.name"
      v-for="station in stations"></mini-status>
  </div>
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
