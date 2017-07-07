/**
 *
 * Main application code. Creates the main vuejs instance and attaches related
 * objects (like vuex and router)
 *
 * NOTE: The Vue build version to load with the `import` command (runtime-only
 *       or standalone) has been set in webpack.base.conf with an alias.
 *
 */
import Vue from 'vue'
import App from './App'
import router from './router'
import Vuex from 'vuex'
import Vuetify from 'vuetify'
import axios from 'axios'

import ConfirmationDialog from './components/ConfirmationDialog'
import ErrorBlock from './components/ErrorBlock'
import HomePage from './components/HomePage'
import MiniStatus from './components/MiniStatus'
import RouteBlock from './components/RouteBlock'
import StateIcon from './components/StateIcon'
import StationBlock from './components/StationBlock'
import TeamBlock from './components/TeamBlock'
import UserBlock from './components/UserBlock'
import UserRoleCheckbox from './components/UserRoleCheckbox'
import UserStationCheckbox from './components/UserStationCheckbox'

Vue.config.productionTip = false
Vue.use(Vuex)
Vue.use(Vuetify)

import 'vuetify/dist/vuetify.min.css'

const BASE_URL = 'https://powonline.albert.lu/api'

/**
 * Inject the JWT token into each outgoing request if it's available
 */
axios.interceptors.request.use(config => {
  const jwt = localStorage.getItem('jwt') || ''
  if (jwt !== '') {
    config.headers['Authorization'] = 'Bearer ' + jwt
    console.debug('Intercepted and set auth token to ' + jwt)
  } else {
    console.debug('JWT was null!')
  }
  return config
}, error => {
  // nothing to do
  return Promise.reject(error)
})

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
    jwt: '',
    roles: [],
    userName: '',
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
    /**
     * Sets a new JWT token
     *
     * :param data: An object with two keys:
     *    * token - The JWT token (without "Bearer" prefix)
     *    * roles - A list of role-names which the user has assigned to himself
     */
    setToken (state, data) {
      state.jwt = data['token']
      state.roles = data['roles']
      state.userName = data['userName']
    },

    /**
     * Flag the user as "logged in".
     *
     * :param data: An object with two keys:
     *    * token - The JWT token (without "Bearer" prefix)
     *    * roles - A list of role-names which the user has assigned to himself
     */
    loginUser (state, data) {
      localStorage.setItem('roles', data['roles'])
      localStorage.setItem('jwt', data['token'])
      localStorage.setItem('userName', data['user'])
      state.jwt = data['token']
      state.roles = data['roles']
      state.userName = data['user']
      console.debug('Set auth token in LS to ' + data['token'])
    },

    /**
     * Flag the user as "logged out"
     */
    logoutUser (state) {
      localStorage.removeItem('jwt')
      localStorage.removeItem('roles')
      localStorage.removeItem('userName')
      state.jwt = ''
      state.roles = []
      console.debug('cleared LS')
    },

    /**
     * Change the page title
     *
     * :param title (str): The new page title
     */
    changeTitle (state, title) {
      state.pageTitle = title
    },

    /**
     * Add a new user to the local state
     *
     * This is triggered by the completion of a corresponding remote call.
     *
     * :param user (object): The new user. Thas the same fields as the object
     *     returned from the backend.
     */
    addUser (state, user) {
      state.users.push(user)
    },

    /**
     * Add a new team to the local state
     *
     * This is triggered by the completion of a corresponding remote call.
     *
     * :param team (object): The new team. Thas the same fields as the object
     *     returned from the backend.
     */
    addTeam (state, team) {
      state.teams.push(team)
    },

    /**
     * Add a new route to the local state
     *
     * This is triggered by the completion of a corresponding remote call.
     *
     * :param route (object): The new route. Thas the same fields as the object
     *     returned from the backend.
     */
    addRoute (state, route) {
      state.routes.push(route)
    },

    /**
     * Add a new station to the local state
     *
     * This is triggered by the completion of a corresponding remote call.
     *
     * :param station (object): The new station. Thas the same fields as the
     *     object returned from the backend.
     */
    addStation (state, station) {
      state.stations.push(station)
    },

    /**
     * Replace the teams with a new list of teams
     *
     * This is triggered by the completion of a corresponding remote call.
     *
     * :param leams (array of object): A list containing the replacement teams.
     *     Each list element has the same fields as the team objects returned
     *     from the backend.
     */
    replaceTeams (state, teams) {
      state.teams = teams
    },

    /**
     * Replace the users with a new list of users
     *
     * This is triggered by the completion of a corresponding remote call.
     *
     * :param leams (array of object): A list containing the replacement users.
     *     Each list element has the same fields as the user objects returned
     *     from the backend.
     */
    replaceUsers (state, users) {
      state.users = users
    },

    /**
     * Replace the routes with a new list of routes
     *
     * This is triggered by the completion of a corresponding remote call.
     *
     * :param leams (array of object): A list containing the replacement routes.
     *     Each list element has the same fields as the route objects returned
     *     from the backend.
     */
    replaceRoutes (state, routes) {
      state.routes = routes
    },

    /**
     * Replace the stations with a new list of stations
     *
     * This is triggered by the completion of a corresponding remote call.
     *
     * :param leams (array of object): A list containing the replacement
     *     stations.  Each list element has the same fields as the station
     *     objects returned from the backend.
     */
    replaceStations (state, stations) {
      state.stations = stations
    },

    /**
     * Display an error to the user
     *
     * :param error (object): The error object. No keys are obligatory. If the
     *     error comes from axios it will have specific fields which change the
     *     layout a bit.
     */
    logError (state, error) {
      state.errors.push(error)
    },

    /**
     * Replace the dashboard data with new data
     *
     * This is triggered by the completion of a corresponding remote call.
     *
     * :param data: The new dashboard data
     */
    updateDashboard (state, data) {
      state.dashboard = data
    },

    /**
     * Replace team-to-route mapping
     *
     * :param assignments: An object as returned by the backend
     */
    replaceAssignments (state, assignments) {
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

    /**
     * Assigns a team to a route
     *
     * :param payload (object): An object with the following keys:
     *    * routeName: The name of the route
     *    * team: Object with the key "name" representing the team name.
     */
    assignTeamToRoute (state, payload) {
      const current = state.route_team_map[payload.routeName]
      if (current === undefined) {
        state.route_team_map[payload.routeName] = [payload.team.name]
      } else {
        state.route_team_map[payload.routeName].push(payload.team.name)
      }
    },

    /**
     * Unassigns a team from a route
     *
     * :param payload (object): An object with the following keys:
     *    * routeName: The name of the route
     *    * teamName: The name of the team to remove
     */
    unassignTeamFromRoute (state, payload) {
      const current = state.route_team_map[payload.routeName]
      if (current === undefined) {
        state.route_team_map[payload.routeName] = []
      } else {
        // XXX TODO implement
      }
    },

    /**
     * Assigns a station to a route
     *
     * :param payload (object): An object with the following keys:
     *    * routeName: The name of the route
     *    * station: An object with the key "name" representing the station
     *      name
     */
    assignStationToRoute (state, payload) {
      const current = state.route_station_map[payload.routeName]
      if (current === undefined) {
        state.route_station_map[payload.routeName] = [payload.station.name]
      } else {
        state.route_station_map[payload.routeName].push(payload.station.name)
      }
    },

    /**
     * Unassigns a station from a route
     *
     * :param payload (object): An object with the following keys:
     *    * routeName: The name of the route
     *    * stationName: The name of the station to remove
     */
    unassignStationFromRoute (state, payload) {
      const current = state.route_station_map[payload.routeName]
      if (current === undefined) {
        state.route_station_map[payload.routeName] = []
      } else {
        // XXX TODO implement
      }
    },

    /**
     * Removes a route
     *
     * :param routeName (str): The name of the route to remove.
     */
    deleteRoute (state, routeName) {
      let idx = -1  // TODO REDDIT there must be a better way than the following loop
      state.routes.forEach(item => {
        if (item.name === routeName) {
          idx = state.routes.indexOf(item)
        }
      })

      if (idx > -1) {
        state.routes.splice(idx, 1)
      }
    },

    /**
     * Removes a station
     *
     * :param stationName (str): The name of the station to remove.
     */
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

    /**
     * Removes a team
     *
     * :param teamName (str): The name of the team to remove.
     */
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

    /**
     * Removes a user
     *
     * :param userName (str): The name of the user to remove.
     */
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

    /**
     * Displays a block to add a new entity. Which block to show depends on the
     * route.
     *
     * :param path (str): The "router" path (current URL) of the current page
     */
    showAddBlock (state, path) {
      state.isAddBlockVisible[path] = true
    },

    /**
     * Hides the block which allows adding a new entity. Which block to hide
     * depends on the route.
     *
     * :param path (str): The "router" path (current URL) of the current page
     */
    closeAddBlock (state, path) {
      state.isAddBlockVisible[path] = false
    },

    /**
     * Show the bottom navigation panel
     */
    showBottomNav (state) {
      state.isBottomNavVisible = true
    },

    /**
     * Hide the bottom navigation panel
     */
    hideBottomNav (state) {
      // this is disabled as it currently causes problems on iPhone
      // state.isBottomNavVisible = false
    }
  },
  actions: {
    /**
     * Advance the state of a team on a station
     *
     * :param payload (object): An object with the following keys:
     *     * stationName: The name of the station
     *     * teamName: The name of the team
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

    /**
     * Refreshes the local users from the backend
     */
    refreshUsers (context) {
      if (context.state.roles.indexOf('admin') === -1) {
        return
      }
      axios.get(BASE_URL + '/user')
      .then(response => {
        context.commit('replaceUsers', response.data.items)
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Refreshes the local teams from the backend
     */
    refreshTeams (context) {
      axios.get(BASE_URL + '/team')
      .then(response => {
        context.commit('replaceTeams', response.data.items)
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Refreshes the local routes from the backend
     */
    refreshRoutes (context) {
      axios.get(BASE_URL + '/route')
      .then(response => {
        context.commit('replaceRoutes', response.data.items)
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Refreshes the local stations from the backend
     */
    refreshStations (context) {
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
     * Refreshes the local assignments from the backend
     */
    refreshAssignments (context) {
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
     * :param data (object): An object with the following keys:
     *     *  team: The team object to add to the route
     *     *  routeName: The name of the route the team should be assigned to
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
     * :param data (object): An object with the following keys:
     *     * teamName: The name of the team
     *     * routeName: The name of the route the team should be unassigned from
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
     *
     * :param data (object): An object with the following keys:
     *     *  station: The station object to add to the route
     *     *  routeName: The name of the route the station should be assigned to
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
        context.dispatch('refreshRemote') // TODO Something causes a non-rective change which is why this is needed. Investigate!
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Unassign a station from a route
     *
     * :param data (object): An object with the following keys:
     *     * stationName: The name of the station
     *     * routeName: The name of the route the station should be unassigned from
     */
    unassignStationFromRouteRemote (context, data) {
      axios.delete(BASE_URL + '/route/' + data.routeName + '/stations/' + data.stationName)
      .then(response => {
        context.commit('unassignStationFromRoute', data)
        context.dispatch('refreshRemote') // TODO Something causes a non-rective change which is why this is needed. Investigate!
      })
      .catch(e => {
        context.commit('logError', e)
      })
    },

    /**
     * Delete a route
     *
     * :param routeName: The name of the route to delete
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
     *
     * :param stationName: The name of the station to delete
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
     *
     * :param userName: The name of the user to delete
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
     *
     * :param teamName: The name of the team to delete
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

    /**
     * Get a list of team names which are not assigned to any route
     *
     * :returns: a list of strings
     */
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

    /**
     * Given the name of a route, this returns all team names assigned to that
     * route.
     *
     * :param routeName: The name of the route of which we want to find the
     *     assigned users.
     * :returns: A list of strings
     */
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

    /**
     * Given the name of a route, this returns a list of station names which
     * are not assigned to that route.
     *
     * :param routeName: The name of the route of which we want to list the
     *     unassigned stations.
     * :returns: a list of strings
     */
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

    /**
     * Given the name of a route, this returns all stations which are assigned
     * to that route.
     *
     * :param routeName: The name of the route of which we want to list the
     *     assigned stations.
     * :returns: a list of strings
     */
    assignedStations: (state, getters) => (routeName) => {
      const tmp = state.route_station_map[routeName] || []
      const assignedStations = []
      tmp.forEach(item => { assignedStations.push(item.name) })
      return assignedStations
    }
  }

})

Vue.component('confirmation-dialog', ConfirmationDialog)
Vue.component('error-block', ErrorBlock)
Vue.component('home-page', HomePage)
Vue.component('mini-status', MiniStatus)
Vue.component('route-block', RouteBlock)
Vue.component('state-icon', StateIcon)
Vue.component('station-block', StationBlock)
Vue.component('team-block', TeamBlock)
Vue.component('user-block', UserBlock)
Vue.component('user-role-checkbox', UserRoleCheckbox)
Vue.component('user-station-checkbox', UserStationCheckbox)

/* eslint-disable no-new */
const vue = new Vue({
  el: '#app',
  router,
  store,
  template: '<App/>',
  components: { App },
  created () {
    const savedToken = localStorage.getItem('jwt') || ''
    const savedRoles = localStorage.getItem('roles') || []
    const savedUsername = localStorage.getItem('userName') || ''
    this.$store.commit('setToken', {token: savedToken, roles: savedRoles, userName: savedUsername})
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
