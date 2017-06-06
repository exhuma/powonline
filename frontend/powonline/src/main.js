// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'
import Vuex from 'vuex'
import axios from 'axios'

import StationBlock from './components/StationBlock'
import TeamBlock from './components/TeamBlock'
import RouteBlock from './components/RouteBlock'

Vue.config.productionTip = false
Vue.use(Vuex)

const BASE_URL = 'http://192.168.1.92:5000'
const store = new Vuex.Store({
  state: {
    stations: [],
    teams: [],
    routes: [],
    station_team_map: {}
  },
  mutations: {
    /**
     * Add a team to the store
     *
     * :param team: The team object to add
     */
    addTeam (state, team) {
      axios.post(BASE_URL + '/team', team)
      .then(response => {
        state.teams.push(team)
      })
      .catch(e => {
        if (e.response && e.response.status === 400) {
          for (var key in e.response.data) {
            this.errors.push({message: e.response.data[key] + ': ' + key})
          }
        } else {
          console.log(e) // TODO better error-handling
        }
      })
    },

    /**
     * Add a team to the store
     *
     * :param route: The route object to add
     */
    addRoute (state, route) {
      axios.post(BASE_URL + '/route', route)
      .then(response => {
        state.routes.push(route)
      })
      .catch(e => {
        if (e.response && e.response.status === 400) {
          for (var key in e.response.data) {
            this.errors.push({message: e.response.data[key] + ': ' + key})
          }
        } else {
          console.log(e) // TODO better error-handling
        }
      })
    },

    /**
     * Add a station to the store
     *
     * :param route: The station object to add
     */
    addStation (state, station) {
      axios.post(BASE_URL + '/station', station)
      .then(response => {
        state.stations.push(station)
      })
      .catch(e => {
        console.log(e) // TODO better error-handling
      })
    },

    /**
     * Refresh everything from the server
     */
    refresh (state) {
      console.log('Refreshing State in vuex')
      // --- Fetch Teams from server
      axios.get(BASE_URL + '/team')
      .then(response => {
        state.teams = response.data.items
      })
      .catch(e => {
        // TODO use an event for this
        console.log(e)  // TODO better error-handling
      })

      // --- Fetch Routes from server
      axios.get(BASE_URL + '/route')
      .then(response => {
        state.routes = response.data.items
      })
      .catch(e => {
        // TODO use an event for this
        console.log(e)  // TODO better error-handling
      })

      // --- Fetch Stations from server
      axios.get(BASE_URL + '/station')
      .then(response => {
        state.stations = response.data.items
      })
      .catch(e => {
        // TODO use an event for this
        console.log(e)  // TODO better error-handling
      })
    }
  }
})

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  store,
  template: '<App/>',
  components: { App }
})

Vue.component('station-block', StationBlock)
Vue.component('team-block', TeamBlock)
Vue.component('route-block', RouteBlock)
