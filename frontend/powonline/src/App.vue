<template>
  <div id="app">
    <router-link class="navlink" to="/">Index</router-link>
    <router-link class="navlink" to="/station">Stations</router-link>
    <router-link class="navlink" to="/team">Teams</router-link>
    <router-link class="navlink" to="/route">Routes</router-link>
    <router-view></router-view>
    <div id="errors">
      <error-block :error="error" v-for="error in errors"></error-block>
    </div>
  </div>
</template>

<script>
export default {
  name: 'app',
  computed: {
    errors () {
      return this.$store.state.errors
    }
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
.error {
  border: 1px solid #a00;
  background: #fee;
  text-align: left;
  padding: 1em;
}
</style>
