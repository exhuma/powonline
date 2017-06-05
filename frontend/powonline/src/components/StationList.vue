<template>
  <div id="StationList">
    <h1>Station List</h1>
    <input @keyup.enter="addStation" type='text' v-model:stationname='stationname' placeholder='Enter a new stationname' />
    <br />
    <button @click="refresh">Refresh</button>
    <table width="100%" border="1">
      <thead>
        <tr>
          <th>Station Name</th>
          <th>Ops</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="station, idx in stations">
          <td>{{ station.name }}</td>
          <td><button :data-stationid="idx" @click="removeStation">X</button></td>
        </tr>
      </tbody>
    </table>
    <ul v-if="errors && errors.length">
      <li v-for="error of errors">
        {{error.message}}
      </li>
    </ul>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'station_list',
  methods: {
    removeStation: function (event) {
      // this.stations.splice(event.target.getAttribute('data-stationname'), 1)
      this.errors.push({message: 'Removing stations is not yet implemented!'})
    },
    addStation: function (event) {
      axios.post('http://192.168.1.92:5000/station', {
        name: event.target.value
      })
      .then(response => {
        this.stations = response.data.items
        console.log(response)
        this.refresh()
      })
      .catch(e => {
        if (e.response.status === 400) {
          for (var key in e.response.data) {
            this.errors.push({message: e.response.data[key] + ': ' + key})
          }
        }
      })
    },
    refresh: function (event) {
      axios.get('http://192.168.1.92:5000/station')
      .then(response => {
        this.stations = response.data.items
        console.log(response)
      })
      .catch(e => {
        this.errors.push(e)
      })
    }
  },
  created () {
    this.refresh()
  },
  data () {
    return {
      errors: [],
      stationname: 'default',
      stations: []
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
