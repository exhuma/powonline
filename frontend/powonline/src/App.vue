<template>
  <div id="app">
    <v-app>

      <v-navigation-drawer persistent light :mini-variant.sync="mini" v-model="drawer">
        <v-list class="pa-0">
          <v-list-item>
            <v-list-tile avatar tag="div">
              <v-list-tile-content>
                <v-list-tile-title>Powonline</v-list-tile-title>
              </v-list-tile-content>
              <v-list-tile-action>
                <v-btn icon @click.native.stop="mini = !mini">
                  <v-icon>chevron_left</v-icon>
                </v-btn>
              </v-list-tile-action>
            </v-list-tile>
          </v-list-item>
        </v-list>
        <v-list class="pt-0" dense>
          <v-divider></v-divider>
          <v-list-item v-for="route in routes">
            <v-list-tile>
              <v-list-tile-action>
                <v-icon>{{route.icon}}</v-icon>
              </v-list-tile-action>
              <v-list-tile-content>
                <v-list-tile-title><router-link class="navlink" :to="route.to">{{ route.label }}</router-link></v-list-tile-title>
              </v-list-tile-content>
            </v-list-tile>
          </v-list-item>
        </v-list>
      </v-navigation-drawer>

      <v-toolbar>
        <v-toolbar-side-icon light @click.native.stop="drawer = !drawer"></v-toolbar-side-icon>
        <v-toolbar-title>Toolbar</v-toolbar-title>
      </v-toolbar>
      <main>
        <v-container fluid>
          <router-view></router-view>
          <div id="errors">
            <error-block :error="error" v-for="(error, idx) in errors" :key="'error-' + idx"></error-block>
          </div>
        </v-container>
      </main>
      <v-footer></v-footer>
    </v-app>
  </div>
</template>

<script>
export default {
  name: 'app',
  data () {
    return {
      drawer: true,
      routes: [
        { label: 'Home', to: '/', icon: 'home' },
        { label: 'Stations', to: '/station', icon: 'place' },
        { label: 'Teams', to: '/team', icon: 'group' },
        { label: 'Routes', to: '/route', icon: 'gesture' }
      ],
      mini: false,
      right: null
    }
  },
  computed: {
    errors () {
      return this.$store.state.errors
    }
  }
}
</script>
