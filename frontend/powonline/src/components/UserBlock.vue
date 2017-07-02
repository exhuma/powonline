<template>
  <v-card class="mt-3">
    <v-card-row class="brown darken-1">
      <v-card-title><span class="white--text">User: "{{ name }}"</span></v-card-title>
    </v-card-row>
    <v-card-text>
      <user-role-checkbox
        v-for="role in roles"
        :key="role[0]"
        :user="name"
        :label="role[0]"
        :role="role[0]"></user-role-checkbox>
    </v-card-text>
    <v-divider></v-divider>
    <v-card-row actions>
      <confirmation-dialog buttonText="Delete" :actionArgument="name" actionName="deleteUserRemote">
        <v-card-title slot="title">Do you want to delete the user "{{ name }}"?</v-card-title>
        <v-card-text slot="text">
          <p>this will delete the user with the name "{{ name }}" and all
            related information!</p>
          <p>Are you sure?</p>
        </v-card-text>
      </confirmation-dialog>
    </v-card-row>
  </v-card>
</template>

<script>
import axios from 'axios'
export default {
  name: 'user-block',
  data () {
    return {
      roles: []
    }
  },
  methods: {
    refreshRoles () {
      axios.get(this.$store.state.baseUrl + '/user/' + this.name + '/roles')
      .then(response => {
        this.roles = response.data
      })
      .catch(e => {
        this.$store.commit('logError', e)
      })
    }
  },
  created () {
    this.refreshRoles()
  },
  props: {
    'name': {
      type: String,
      default: 'Unknown User'
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.user-block {
  border: 1px solid black;
  padding: 1em;
}

</style>
