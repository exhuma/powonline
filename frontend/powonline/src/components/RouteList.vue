<template>
  <div id="RouteList">
    <h1>Route List</h1>
    <input 
      id="RouteNameImput"
      @keyup.enter="addRoute"
      type='text'
      v-model:routename='routename'
      placeholder='Enter a new routename' />
    <button @click="addRoute">Add</button>
    <hr />
    <route-block v-on:listChanged="refresh" v-for="route in routes" :name="route.name" :key="route.name"></route-block>
    <hr />
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
  name: 'route_list',
  methods: {
    addRoute: function (event) {
      axios.post('http://192.168.1.92:5000/route', {
        name: this.routename
      })
      .then(response => {
        this.routes = response.data.items
        console.log(response)
        this.refresh()
        const input = document.getElementById('RouteNameImput')
        input.focus()
        input.select()
      })
      .catch(e => {
        if (e.response && e.response.status === 400) {
          for (var key in e.response.data) {
            this.errors.push({message: e.response.data[key] + ': ' + key})
          }
        } else {
          console.log(e)
        }
      })
    },
    refresh: function (event) {
      axios.get('http://192.168.1.92:5000/route')
      .then(response => {
        this.routes = response.data.items
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
      routename: 'default',
      routes: []
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
