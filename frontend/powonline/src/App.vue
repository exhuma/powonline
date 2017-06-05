<template>
  <div id="app">
    <router-link class="navlink" to="/">Index</router-link>
    <router-link class="navlink" to="/user">Home</router-link>
    <router-link class="navlink" to="/station">Stations</router-link>
    <router-link class="navlink" to="/team">Teams</router-link>
    <router-link class="navlink" to="/route">Routes</router-link>
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: 'app'
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
</style>
