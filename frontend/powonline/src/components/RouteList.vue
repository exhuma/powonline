<template>
  <div id="RouteList">
    <input 
      id="RouteNameImput"
      @keyup.enter="addRoute"
      type='text'
      v-model:routename='routename'
      placeholder='Enter a new routename' />
    <button @click.native="addRoute">Add</button>
    <hr />
    <route-block v-for="route in routes" :name="route.name" :key="route.name"></route-block>
  </div>
</template>

<script>
export default {
  name: 'route_list',
  methods: {
    addRoute: function (event) {
      this.$store.dispatch('addRouteRemote', {name: this.routename})
      const input = document.getElementById('RouteNameImput')
      input.focus()
      input.select()
    }
  },
  created () {
    this.$store.commit('changeTitle', 'Route List')
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
