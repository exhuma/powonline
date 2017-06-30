<template>
  <div id="app">
    <v-app>
      <v-toolbar class="red darken-1">
        <v-toolbar-title class="white--text">{{ pageTitle }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn @click.native="addElement" icon light><v-icon>add</v-icon></v-btn>
      </v-toolbar>
      <main>
        <v-container fluid>
          <router-view></router-view>
          <div id="errors">
            <error-block :error="error" v-for="(error, idx) in errors" :key="'error-' + idx"></error-block>
          </div>
          <br clear="all"/>
        </v-container>
        <v-bottom-nav :value="isBottomNavVisible" class="red darken-1">
          <v-btn v-for="route in routes" @click.native="go" :data-to="route.to" :key="route.to" flat light :value="here === route.to">
            <span>{{ route.label }}</span>
            <v-icon>{{route.icon}}</v-icon>
          </v-btn>
        </v-bottom-nav>
      </main>
    </v-app>
  </div>
</template>

<script>
export default {
  name: 'app',
  data () {
    return {
      routes: [
        { label: 'Home', to: '/', icon: 'home' },
        { label: 'Stations', to: '/station', icon: 'place' },
        { label: 'Teams', to: '/team', icon: 'group' },
        { label: 'Routes', to: '/route', icon: 'gesture' }
      ]
    }
  },
  methods: {
    go (e) {
      const destination = e.target.getAttribute('data-to')
      this.$router.push(destination)
    },
    addElement () {
      this.$store.commit('showAddBlock', this.$route.path)
    }
  },
  computed: {
    isBottomNavVisible () {
      return this.$store.state.isBottomNavVisible
    },
    pageTitle () {
      return this.$store.state.pageTitle
    },
    errors () {
      return this.$store.state.errors
    },
    here () {
      return this.$route.path
    }
  }
}
</script>
