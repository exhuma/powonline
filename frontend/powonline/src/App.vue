<template>
  <div id="app">
    <v-app>
      <v-toolbar class="red darken-1">
        <v-toolbar-title class="white--text">{{ pageTitle }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn @click.native="addElement" icon light><v-icon>add</v-icon></v-btn>
        <v-btn v-tooltip:bottom="{html: 'Logout'}" v-if="tokenIsAvailable" @click.native.stop="logoutUser" icon light><v-icon>exit_to_app</v-icon></v-btn>
        <v-btn v-tooltip:bottom="{html: 'Login'}" v-else @click.native.stop="showLoginDialog" icon light><v-icon>perm_identity</v-icon></v-btn>
      </v-toolbar>
      <main>
        <v-container fluid>

          <v-dialog v-model="loginDialogVisible">

            <v-card>
              <v-card-row class="brown darken-4">
                <v-card-title>
                  <span class="white--text">Login</span>
                </v-card-title>
              </v-card-row>
              <v-card-text>
                <v-text-field
                  type='text'
                  @keyup.enter.native="loginUser"
                  v-model:username='username'
                  label='Enter a new username' />
                <v-text-field
                  @keyup.enter.native="loginUser"
                  type='password'
                  v-model='password'
                  label='Password' />
              </v-card-text>
              <v-divider></v-divider>
              <v-card-row actions>
                <v-btn class="green--text darken-1" flat="flat" @click.native="cancelLogin">Cancel</v-btn>
                <v-btn class="green--text darken-1" flat="flat" @click.native="loginUser">Login</v-btn>
              </v-card-row>
            </v-card>
          </v-dialog>

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
import axios from 'axios'
export default {
  name: 'app',
  data () {
    return {
      loginDialogVisible: false,
      username: '',
      password: ''
    }
  },
  methods: {
    go (e) {
      const destination = e.target.getAttribute('data-to')
      this.$router.push(destination)
    },
    loginUser () {
      axios.post(this.$store.state.baseUrl + '/login', {
        'username': this.username,
        'password': this.password
      }).then(response => {
        if (response.status < 300) {
          this.$store.commit('loginUser', response.data)
        } else {
          this.$store.commit('logoutUser')
        }
      })
      this.loginDialogVisible = false
    },
    logoutUser () {
      this.$store.commit('logoutUser')
    },
    cancelLogin () {
      this.loginDialogVisible = false
    },
    showLoginDialog () {
      this.loginDialogVisible = true
    },
    addElement () {
      this.$store.commit('showAddBlock', this.$route.path)
    }
  },
  computed: {
    routes () {
      const output = [
        { label: 'Home', to: '/', icon: 'home' },
        { label: 'Stations', to: '/station', icon: 'place' },
        { label: 'Teams', to: '/team', icon: 'group' },
        { label: 'Routes', to: '/route', icon: 'gesture' }
      ]
      if (this.$store.state.roles.indexOf('admin') > -1) {
        output.push({ label: 'Users', to: '/user', icon: 'face' })
      }
      return output
    },
    tokenIsAvailable () {
      return this.$store.state.jwt !== ''
    },
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
