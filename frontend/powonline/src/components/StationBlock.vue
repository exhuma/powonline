<template>
  <div class="station-block">
    <a :href="'#/station/' + name">{{ name }}</a>
    <button @click="deleteStation">Delete</button>
  </div>
</template>

<script>
export default {
  name: 'station-block',
  props: {
    'name': {
      type: String,
      default: 'Unknown Station'
    }
  },
  methods: {
    deleteStation: function (event) {
      this.$store.dispatch('deleteStationRemote', this.name)
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.station-block {
  border: 1px solid black;
  padding: 1em;
}

</style>
