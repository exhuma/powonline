<template>
  <div id="HomePage">
    <center><img src="./venividiwisel.jpg"></img></center>
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
