<template>
  <v-card>
    <v-card-row class="green darken-1">
      <v-card-title><span class="white--text">{{ name }}</span></v-card-title>
    </v-card-row>
    <v-card-text>
      <v-card-row>
        <a :href="'#/station/' + name">Dashboard</a>
      </v-card-row>
    </v-card-text>
    <v-divider></v-divider>
    <v-card-row actions>
        <v-btn flat class="green--text darken-1" @click.native="deleteStation">Delete</v-btn>
    </v-card-row>
  </v-card>
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
