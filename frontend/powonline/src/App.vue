<template>
  <div id="app">
    <router-link class="navlink" to="/">Index</router-link>
    <router-link class="navlink" to="/station">Stations</router-link>
    <router-link class="navlink" to="/team">Teams</router-link>
    <router-link class="navlink" to="/route">Routes</router-link>
    <router-view></router-view>
    <div id="errors">
      <error-block :error="error" v-for="(error, idx) in errors" :key="'error-' + idx"></error-block>
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
