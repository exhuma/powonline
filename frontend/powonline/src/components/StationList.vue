<template>
  <div id="StationList">
    <v-card>
      <v-card-row class="brown darken-4">
        <v-card-title>
          <span class="white--text">Add New Station</span>
        </v-card-title>
      </v-card-row>
      <v-card-text>
        <v-text-field
          id="StationNameImput"
          @keyup.enter.native="addStation"
          type='text'
          v-model:stationname='stationname'
          label='Enter a new stationname' />
      </v-card-text>
      <v-divider></v-divider>
      <v-card-row actions>
        <v-btn @click.native="addStation" flat>Add</v-btn>
      </v-card-row>
    </v-card>
    <station-block v-for="station in stations" :name="station.name" :key="station.name"></station-block>
  </div>
</template>

<script>
export default {
  name: 'station_list',
  methods: {
    addStation: function (event) {
      this.$store.dispatch('addStationRemote', {name: this.stationname})
      const input = document.getElementById('StationNameImput')
      input.focus()
      input.select()
    }
  },
  created () {
    this.$store.commit('changeTitle', 'Station List')
  },
  data () {
    return {
      stationname: ''
    }
  },
  computed: {
    stations () {
      return this.$store.state.stations
    }
  }
}
</script>
