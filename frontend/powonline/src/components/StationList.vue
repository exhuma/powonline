<template>
  <div id="StationList">
    <v-text-field
      id="StationNameImput"
      @keyup.enter.native="addStation"
      type='text'
      v-model:stationname='stationname'
      label='Enter a new stationname' />
    <v-btn @click.native="addStation">Add</v-btn>
    <hr />
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
