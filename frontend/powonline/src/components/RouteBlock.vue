<template>
  <div class="route-block">
    {{ name }}
    <button @click="deleteRoute">Delete</button>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'route-block',
  props: {
    'name': {
      type: String,
      default: 'Unknown Route'
    }
  },
  methods: {
    deleteRoute: function (event) {
      axios.delete('http://192.168.1.92:5000/route/' + this.name)
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
.route-block {
  border: 1px solid black;
  padding: 1em;
}

</style>
