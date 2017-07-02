<template>
  <v-checkbox @change="onValueChanged" v-model="checked" :label="label"></v-checkbox>
</template>

<script>
import axios from 'axios'
export default {
  name: 'user-station-checkbox',
  props: [
    'user',
    'station',
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
        axios.post(baseUrl + '/user/' + this.user + '/stations', {
          name: this.station
        })
      } else {
        axios.delete(baseUrl + '/user/' + this.user + '/stations/' + this.station)
      }
    }
  },
  created () {
    const baseUrl = this.$store.state.baseUrl
    axios.get(baseUrl + '/user/' + this.user + '/stations/' + this.station)
    .then(response => {
      this.checked = response.data
    })
    .catch(e => {
      this.$store.commit('logError', e)
    })
  }
}
</script>
