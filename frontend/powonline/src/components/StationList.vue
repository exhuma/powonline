<template>
  <div id="StationList">
    <h1>Station List</h1>
    <input 
      id="StationNameImput"
      @keyup.enter="addStation"
      type='text'
      v-model:stationname='stationname'
      placeholder='Enter a new stationname' />
    <button @click="addStation">Add</button>
    <hr />
    <station-block v-on:listChanged="refresh" v-for="station in stations" :name="station.name" :key="station.name"></station-block>
  </div>
</template>

<script>
export default {
  name: 'station_list',
  methods: {
    addStation: function (event) {
      this.$store.commit('addStation', {name: this.stationname})
      const input = document.getElementById('StationNameImput')
      input.focus()
      input.select()
    },
    refresh: function (event) {
      this.$store.dispatch('refreshRemote')
    }
  },
  created () {
    this.$store.dispatch('refreshRemote')
  },
  data () {
    return {
      stationname: 'default'
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
h1, h2 {
  font-weight: normal;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  display: inline-block;
  margin: 0 10px;
}

a {
  color: #42b983;
}
</style>
