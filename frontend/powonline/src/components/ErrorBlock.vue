<template>
  <div class="error-block">
    <p v-if="error.config.method">
      Error when retrieving <tt>{{ error.config.method}} {{error.config.url}}</tt>
      <button @click="toggleDisplay">i</button>
      <pre v-show="displayError">{{ error }}</pre>
    </p>
  </div>
</template>

<script>
export default {
  name: 'error-block',
  props: ['error'],
  data () {
    return {
      displayError: false
    }
  },
  methods: {
    toggleDisplay: function (event) {
      this.displayError = !this.displayError
    }
  }
}
</script>

<style scoped>
  .error-block {
    border: 2px solid #800;
    background: rgba(255, 0, 0, 0.2);
    margin: 1em;
  }
  PRE {
    font-weight: bold;
    text-align: left;
    border: 1px solid rgba(0, 0, 0, 0.2);
    background: rgba(0, 0, 0, 0.2);
    margin: 1em;
    padding: 1em;
    color: black;
  }
</style>
