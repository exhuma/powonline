<template>
  <div id="HomePage">
  </div>
</template>
<script>
export default {
  name: 'homepage',
  created () {
    this.$store.commit('changeTitle', 'PowOnline v1.1.1')
  }
}
</script>
