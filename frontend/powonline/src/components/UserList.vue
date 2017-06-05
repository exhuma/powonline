<template>
  <div id="UserList">
    <h1>User List</h1>
    <input @keyup.enter="addUser" type='text' v-model:username='username' placeholder='Enter a new username' />
    <br />
    <table>
      <thead>
        <tr>
          <th>User Name</th>
          <th>Ops</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user, idx in users">
          <td>{{ user.name }}</td>
          <td><button :data-userid="idx" @click="refresh">X</button></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'user_list',
  methods: {
    removeUser: function (event) {
      this.users.splice(event.target.getAttribute('data-username'), 1)
    },
    addUser: function (event) {
      this.users.push({name: this.username})
    },
    increment: function (event) {
      this.$store.commit('increment')
    },
    refresh: function (event) {
      axios.get('http://192.168.1.92:5000/station')
      .then(response => {
        this.posts = response.data
        console.log(response)
      })
      .catch(e => {
        this.errors.push(e)
      })
    }
  },
  computed: {
    stc () {
      return this.$store.state.counter
    }
  },
  created () {
    axios.get('http://192.168.1.92:5000/station')
    .then(response => {
      this.posts = response.data
      console.log(response)
    })
    .catch(e => {
      this.errors.push(e)
    })
  },
  data () {
    return {
      errors: [],
      posts: [],
      username: 'default',
      users: [
        {name: 'John'},
        {name: 'Jane'}
      ]
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h1, h2 {
  font-weight: normal;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  display: inline-block;
  margin: 0 10px;
}

a {
  color: #42b983;
}
</style>
