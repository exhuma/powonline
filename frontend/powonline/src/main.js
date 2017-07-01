// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'
import Vuex from 'vuex'
import Vuetify from 'vuetify'
import axios from 'axios'

import ConfirmationDialog from './components/ConfirmationDialog'
import ErrorBlock from './components/ErrorBlock'
import MiniStatus from './components/MiniStatus'
import RouteBlock from './components/RouteBlock'
import StateIcon from './components/StateIcon'
import StationBlock from './components/StationBlock'
import TeamBlock from './components/TeamBlock'
import UserBlock from './components/UserBlock'
import UserRoleCheckbox from './components/UserRoleCheckbox'

Vue.config.productionTip = false
Vue.use(Vuex)
Vue.use(Vuetify)

axios.defaults.headers.common['Authorization'] = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImhlbGxvIiwicm9sZXMiOlsiYWRtaW4iLCJzdGF0aW9uIl19.Gyx8Jt-X1t3KVtVr9jUomdZ9z7RRtFt7B-jZApXq9XU'

import 'vuetify/dist/vuetify.min.css'

const BASE_URL = 'http://192.168.1.92:5000'
const store = new Vuex.Store({
  state: {
    users: [],
    stations: [],
    teams: [],
    routes: [],
    errors: [],
    route_station_map: {},  // map stations to routes (key=stationName, value=routeName)
    route_team_map: {},  // map teams to routes (key=teamName, value=routeName)
    dashboard: [], // maps team names to station-states
    dashboardStation: '',
    teamStates: [],
    baseUrl: BASE_URL,
    pageTitle: 'Powonline',
    isBottomNavVisible: true,
    isAddBlockVisible: {
      '/route': false,
      '/station': false,
      '/team': false,
      '/user': false
    }
  },
  mutations: {
    changeTitle (state, title) {
      state.pageTitle = title
    },
    addUser (state, user) {
      state.users.push(user)
    },
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
    replaceUsers (state, users) {
      state.users = users
    },
    replaceRoutes (state, routes) {
      state.routes = routes
    },
    replaceStations (state, stations) {
      state.stations = stations
    },
    logError (state, error) {
      state.errors.push(error)
    },
    updateDashboard (state, data) {
      state.dashboard = data
    },
    replaceAssignments (state, assignments) {
      // Replace team-to-route mapping
      state.route_team_map = {}
      for (const routeName in assignments.teams) {
        if (assignments.teams.hasOwnProperty(routeName)) {
          const teams = assignments.teams[routeName]
          teams.forEach(team => {
            state.route_team_map[team.name] = routeName
          })
        }
      }

      // Replace stations-to-routes mapping
      state.route_station_map = {}
      for (const routeName in assignments.stations) {
        if (assignments.stations.hasOwnProperty(routeName)) {
          const stations = assignments.stations[routeName]
          stations.forEach(station => {
            const container = state.route_station_map[routeName] || []
            container.push(station)
            state.route_station_map[routeName] = container
          })
        }
      }
    },
    assignTeamToRoute (state, payload) {
      const current = state.route_team_map[payload.routeName]
      if (current === undefined) {
        state.route_team_map[payload.routeName] = [payload.team.name]
      } else {
        state.route_team_map[payload.routeName].push(payload.team.name)
      }
    },
    unassignTeamFromRoute (state, payload) {
      const current = state.route_team_map[payload.routeName]
      if (current === undefined) {
        state.route_team_map[payload.routeName] = []
      } else {
        // XXX TODO implement
      }
    },
    assignStationToRoute (state, payload) {
      const current = state.route_station_map[payload.routeName]
      if (current === undefined) {
        state.route_station_map[payload.routeName] = [payload.station.name]
      } else {
        state.route_station_map[payload.routeName].push(payload.station.name)
      }
    },
    unassignStationFromRoute (state, payload) {
      const current = state.route_station_map[payload.routeName]
      if (current === undefined) {
        state.route_station_map[payload.routeName] = []
      } else {
        // XXX TODO implement
      }
    },
    deleteRoute (state, routeName) {
      let idx = -1  // TODO there must be a better way than the following loop
      state.routes.forEach(item => {
        if (item.name === routeName) {
          idx = state.routes.indexOf(item)
        }
      })

      if (idx > -1) {
        state.routes.splice(idx, 1)
      }
    },
    deleteStation (state, stationName) {
      let idx = -1  // TODO there must be a better way than the following loop
      state.stations.forEach(item => {
        if (item.name === stationName) {
          idx = state.stations.indexOf(item)
        }
      })

      if (idx > -1) {
        state.stations.splice(idx, 1)
      }
    },
    deleteTeam (state, teamName) {
      let idx = -1  // TODO there must be a better way than the following loop
      state.teams.forEach(item => {
        if (item.name === teamName) {
          idx = state.teams.indexOf(item)
        }
      })

      if (idx > -1) {
        state.teams.splice(idx, 1)
      }
    },
    deleteUser (state, userName) {
      let idx = -1  // TODO there must be a better way than the following loop
      state.users.forEach(item => {
        if (item.name === userName) {
          idx = state.users.indexOf(item)
        }
      })

      if (idx > -1) {
        state.users.splice(idx, 1)
      }
    },
    showAddBlock (state, path) {
      state.isAddBlockVisible[path] = true
    },
    closeAddBlock (state, path) {
      state.isAddBlockVisible[path] = false
    },
    showBottomNav (state) {
      state.isBottomNavVisible = true
    },
    hideBottomNav (state) {
      state.isBottomNavVisible = false
    }
  },
  actions: {
    /**
     * Advance the state of a team on a station
     */
    advanceState (context, payload) {
      axios.post(BASE_URL + '/job', {
        'action': 'advance',
        'args': {
          'station_name': payload.stationName,
          'team_name': payload.teamName
        }
      })
      .then(response => {
        context.dispatch('fetchDashboard', payload.stationName)
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Fetch the dashboard data for a station
     *
     * :param stationName: The name of the station
     */
    fetchDashboard (context, stationName) {
      axios.get(BASE_URL + '/station/' + stationName + '/dashboard')
      .then(response => {
        context.commit('updateDashboard', response.data)
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Add a user to the backend store
     *
     * :param user: The user object to add
     */
    addUserRemote (context, user) {
      axios.post(BASE_URL + '/user', user)
      .then(response => {
        context.commit('addUser', user)
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

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
        context.commit('logError', e)
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
        context.commit('addRoute', route)
      })
      .catch(e => {
        context.commit('logError', e)
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
        context.commit('logError', e)
      })
    },

    /**
     * Refresh everything from the server
     */
    refreshRemote (context) {
      context.dispatch('refreshTeams')
      context.dispatch('refreshRoutes')
      context.dispatch('refreshAssignments')
      context.dispatch('refreshStations')
      context.dispatch('refreshUsers')
    },

    refreshUsers (context, data) {
      // --- Fetch Users from server
      axios.get(BASE_URL + '/user')
      .then(response => {
        context.commit('replaceUsers', response.data.items)
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    refreshTeams (context, data) {
      // --- Fetch Teams from server
      axios.get(BASE_URL + '/team')
      .then(response => {
        context.commit('replaceTeams', response.data.items)
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    refreshRoutes (context, data) {
      // --- Fetch Routes from server
      axios.get(BASE_URL + '/route')
      .then(response => {
        context.commit('replaceRoutes', response.data.items)
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Refresh Stations from the server
     */
    refreshStations (context, data) {
      // --- Fetch Stations from server
      axios.get(BASE_URL + '/station')
      .then(response => {
        context.commit('replaceStations', response.data.items)
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Refresh assignments from the backend
     */
    refreshAssignments (context, data) {
      // --- Fetch team/route assignments from server
      axios.get(BASE_URL + '/assignments')
      .then(response => {
        context.commit('replaceAssignments', response.data)
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Assign a team to a route
     *
     * :param team: The team object to add to the route
     * :param routeName: The name of the route the team should be assigned to
     */
    assignTeamToRouteRemote (context, data) {
      // first, let's find the team object corresponding to this name (yes, I
      // know, a map would be better...)
      let team = null
      context.state.teams.forEach(item => {
        if (item.name === data.teamName) {
          team = item
        }
      })
      axios.post(BASE_URL + '/route/' + data.routeName + '/teams', team)
      .then(response => {
        context.commit('assignTeamToRoute', {routeName: data.routeName, team: team})
        context.dispatch('refreshRemote') // TODO Why is this not happening automatically?
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Unassign a team from a route
     *
     * :param teamName: The name of the team
     * :param routeName: The name of the route the team should be unassigned from
     */
    unassignTeamFromRouteRemote (context, data) {
      axios.delete(BASE_URL + '/route/' + data.routeName + '/teams/' + data.teamName)
      .then(response => {
        context.commit('unassignTeamFromRoute', data)
        context.dispatch('refreshRemote') // TODO Why is this not happening automatically?
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Assign a station to a route
     */
    assignStationToRouteRemote (context, data) {
      // first, let's find the station object corresponding to this name (yes, I
      // know, a map would be better...)
      let station = null
      context.state.stations.forEach(item => {
        if (item.name === data.stationName) {
          station = item
        }
      })
      axios.post(BASE_URL + '/route/' + data.routeName + '/stations', station)
      .then(response => {
        context.commit('assignStationToRoute', {routeName: data.routeName, station: station})
        context.dispatch('refreshRemote') // TODO Why is this not happening automatically?
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Unassign a station from a route
     */
    unassignStationFromRouteRemote (context, data) {
      axios.delete(BASE_URL + '/route/' + data.routeName + '/stations/' + data.stationName)
      .then(response => {
        context.commit('unassignStationFromRoute', data)
        context.dispatch('refreshRemote') // TODO Why is this not happening automatically?
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Delete a route
     */
    deleteRouteRemote (context, routeName) {
      axios.delete(BASE_URL + '/route/' + routeName)
      .then(response => {
        context.commit('deleteRoute', routeName)
      })
      .then(function () {
        context.dispatch('refreshAssignments')
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Delete a station
     */
    deleteStationRemote (context, stationName) {
      axios.delete(BASE_URL + '/station/' + stationName)
      .then(response => {
        context.commit('deleteStation', stationName)
      })
      .then(function () {
        context.dispatch('refreshAssignments')
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Delete a user
     */
    deleteUserRemote (context, userName) {
      axios.delete(BASE_URL + '/user/' + userName)
      .then(response => {
        context.commit('deleteUser', userName)
      })
      .then(function () {
        context.dispatch('refreshAssignments')
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Delete a team
     */
    deleteTeamRemote (context, teamName) {
      axios.delete(BASE_URL + '/team/' + teamName)
      .then(response => {
        context.commit('deleteTeam', teamName)
      })
      .then(function () {
        context.dispatch('refreshAssignments')
      })
      .catch(e => {
        context.commit('logError', e)
      })
    }
  },
  getters: {
    unassignedTeams (state, getters) {
      // fetch *all* assignments of teams
      const assignedTeams = []
      const map = state.route_team_map
      for (const teamName in map) {
        assignedTeams.push(teamName)
      }

      // now create a list of teams which are *not* in the assigned list
      const output = []
      state.teams.forEach(team => {
        if (assignedTeams.indexOf(team.name) === -1) {
          output.push(team.name)
        }
      })
      return output
    },
    assignedTeams: (state, getters) => (routeName) => {
      const assignedTeams = []
      const map = state.route_team_map
      for (const teamName in map) {
        if (map[teamName] === routeName) {
          assignedTeams.push(teamName)
        }
      }
      return assignedTeams
    },
    unassignedStations: (state, getters) => (routeName) => {
      const unassignedStations = []
      const tmp = state.route_station_map[routeName] || []
      const assignedStations = []
      tmp.forEach(item => { assignedStations.push(item.name) })

      state.stations.forEach(item => {
        if (assignedStations.indexOf(item.name) === -1) {
          unassignedStations.push(item.name)
        }
      })
      return unassignedStations
    },
    assignedStations: (state, getters) => (routeName) => {
      const tmp = state.route_station_map[routeName] || []
      const assignedStations = []
      tmp.forEach(item => { assignedStations.push(item.name) })
      return assignedStations
    },
    stationTeams: (state, getters) => (routeName) => {
      return [
        {name: routeName},
        {name: routeName}
      ]
    },
    teamState: (state, getters) => (teamName, stationName) => {
      const output = []
      state.dashboard.forEach(item => {
        console.log(teamName, stationName, item)
      })
      return output
    }
  }

})

Vue.component('confirmation-dialog', ConfirmationDialog)
Vue.component('error-block', ErrorBlock)
Vue.component('mini-status', MiniStatus)
Vue.component('route-block', RouteBlock)
Vue.component('state-icon', StateIcon)
Vue.component('station-block', StationBlock)
Vue.component('team-block', TeamBlock)
Vue.component('user-block', UserBlock)
Vue.component('user-role-checkbox', UserRoleCheckbox)

/* eslint-disable no-new */
const vue = new Vue({
  el: '#app',
  router,
  store,
  template: '<App/>',
  components: { App },
  created () {
    this.$store.dispatch('refreshRemote')
  }
})

var lastKnownScrollPos = 0
var ticking = false

window.addEventListener('scroll', function (e) {
  const isScrollingDown = lastKnownScrollPos < window.scrollY
  lastKnownScrollPos = window.scrollY
  if (!ticking) {
    window.requestAnimationFrame(function () {
      if (isScrollingDown) {
        if (vue.$store.state.isBottomNavVisible) {
          vue.$store.commit('hideBottomNav')
        }
      } else {
        if (!vue.$store.state.isBottomNavVisible) {
          vue.$store.commit('showBottomNav')
        }
      }
      ticking = false
    })
  }
  ticking = true
})
