<template>
  <div id="UserList">
    <transition name="slide">
      <v-card v-show="isAddBlockVisible">
        <v-card-row class="brown darken-4">
          <v-card-title>
            <span class="white--text">Add New User</span>
            <v-spacer></v-spacer>
            <v-btn @click.native="closeAddBlock" icon light><v-icon>close</v-icon></v-btn>
          </v-card-title>
        </v-card-row>
        <v-card-text>
          <v-text-field
            name="user-input"
            id="UserNameImput"
            @keyup.enter.native="addUser"
            type='text'
            v-model:username='username'
            label='Enter a new username' />
          <v-text-field
            name="password"
            @keyup.enter.native="addUser"
            type='password'
            v-model='password'
            label='Password' />
        </v-card-text>
        <v-divider></v-divider>
        <v-card-row actions>
          <v-btn @click.native="addUser" flat>Add</v-btn>
        </v-card-row>
      </v-card>
    </transition>
    <user-block v-for="user in users" :name="user.name" :key="user.name"></user-block>
  </div>
</template>


<script>
export default {
  name: 'user_list',
  methods: {
    addUser: function (event) {
      this.$store.dispatch('addUserRemote', {
        name: this.username,
        password: this.password
      })
      const input = document.getElementById('UserNameImput')
      input.focus()
      input.select()
    },
    closeAddBlock () {
      this.$store.commit('closeAddBlock', this.$route.path)
    }
  },
  created () {
    this.$store.commit('changeTitle', 'User List')
  },
  data () {
    return {
      username: '',
      password: ''
    }
  },
  computed: {
    users () {
      return this.$store.state.users
    },
    isAddBlockVisible () {
      return this.$store.state.isAddBlockVisible[this.$route.path]
    }
  }
}
</script>

<style scoped>
.slide-enter-active, .slide-leave-active {
  transition: all .3s
}
.slide-enter {
  transform: translateY(-100px);
  opacity: 0;
}
.slide-leave-to {
  transform: translateY(-100px);
  opacity: 0;
}
</style>
