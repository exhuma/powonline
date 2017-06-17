<template>
  <div class="team-block">
    {{ name }}
    <button @click="deleteTeam">Delete</button>
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
