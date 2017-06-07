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
  </div>
</template>

<script>
export default {
  name: 'route_list',
  methods: {
    addRoute: function (event) {
      this.$store.commit('addRoute', {name: this.routename})
      const input = document.getElementById('RouteNameImput')
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
      routename: 'default'
    }
  },
  computed: {
    routes () {
      return this.$store.state.routes
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
