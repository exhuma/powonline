<template>
  <div class="station-block">
    {{ name }}
    <button @click="deleteStation">Delete</button>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'station-block',
  props: {
    'name': {
      type: String,
      default: 'Unknown Station'
    }
  },
  methods: {
    deleteStation: function (event) {
      axios.delete('http://192.168.1.92:5000/station/' + this.name)
      .then(response => {
        console.log(response)
        this.$emit('listChanged')
      })
      .catch(e => {
        if (e.response.status === 400) {
          for (var key in e.response.data) {
            this.errors.push({message: e.response.data[key] + ': ' + key})
          }
        }
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.station-block {
  border: 1px solid black;
}

</style>
