<template>
  <v-checkbox @change="onValueChanged" v-model="checked" :label="label"></v-checkbox>
</template>

<script>
import axios from 'axios'
export default {
  name: 'user-role-checkbox',
  props: [
    'user',
    'role',
    'label'
  ],
  data () {
    return {
      checked: false
    }
  },
  methods: {
    onValueChanged (newValue) {
      const baseUrl = this.$store.state.baseUrl
      if (newValue) {
        axios.post(baseUrl + '/user/' + this.user + '/roles', {
          name: this.role
        })
      } else {
        axios.delete(baseUrl + '/user/' + this.user + '/roles/' + this.role)
      }
    }
  },
  created () {
    const baseUrl = this.$store.state.baseUrl
    axios.get(baseUrl + '/user/' + this.user + '/roles/' + this.role)
    .then(response => {
      this.checked = response.data
    })
    .catch(e => {
      this.$store.commit('logError', e)
    })
  }
}
</script>
