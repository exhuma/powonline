<template>
  <div class="station-block">
    <h1>{{ name }}</h1>
  </div>
</template>

<script>
export default {
  name: 'station-block',
  props: ['name'],
  data () {
    return {
      name: 'Unknown Station'
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
