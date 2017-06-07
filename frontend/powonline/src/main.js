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
    addTeam (state, team) {
      state.teams.push(team)
    },
    addRoute (state, route) {
      state.routes.push(route)
    },
    addStation (state, station) {
      state.stations.push(station)
    },
    replaceTeams (state, teams) {
      state.teams = teams
    },
    replaceRoutes (state, routes) {
      state.routes = routes
    },
    replaceStations (state, stations) {
      state.stations = stations
    }
  },
  actions: {
    /**
     * Add a team to the backend store
     *
     * :param team: The team object to add
     */
    addTeamRemote (context, team) {
      axios.post(BASE_URL + '/team', team)
      .then(response => {
        context.commit('addTeam', team)
      })
      .catch(e => {
        console.log(e) // TODO better error-handling
      })
    },

    /**
     * Add a team to the backend store
     *
     * :param route: The route object to add
     */
    addRouteRemote (context, route) {
      axios.post(BASE_URL + '/route', route)
      .then(response => {
        context.commit('addRoute')
      })
      .catch(e => {
        console.log(e) // TODO better error-handling
      })
    },

    /**
     * Add a station to the remote store
     *
     * :param route: The station object to add
     */
    addStationRemote (context, station) {
      axios.post(BASE_URL + '/station', station)
      .then(response => {
        context.commit('addStation', station)
      })
      .catch(e => {
        console.log(e) // TODO better error-handling
      })
    },

    /**
     * Refresh everything from the server
     */
    refreshRemote (context) {
      console.log('Refreshing State in vuex')
      // --- Fetch Teams from server
      axios.get(BASE_URL + '/team')
      .then(response => {
        context.commit('replaceTeams', response.data.items)
      })
      .catch(e => {
        // TODO use an event for this
        console.log(e)  // TODO better error-handling
      })

      // --- Fetch Routes from server
      axios.get(BASE_URL + '/route')
      .then(response => {
        context.commit('replaceRoutes', response.data.items)
      })
      .catch(e => {
        // TODO use an event for this
        console.log(e)  // TODO better error-handling
      })

      // --- Fetch Stations from server
      axios.get(BASE_URL + '/station')
      .then(response => {
        context.commit('replaceStations', response.data.items)
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
