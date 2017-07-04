<template>
  <v-alert error dismissible v-model="visible">
    {{ title }} <v-btn @click.native="toggleDisplay" icon><v-icon>info</v-icon></v-btn>
    <pre v-show="displayError">
      {{error}}
    </pre>
  </v-alert>
</template>

<script>
export default {
  name: 'error-block',
  props: ['error'],
  data () {
    return {
      displayError: false,
      visible: true
    }
  },
  computed: {
    title () {
      // REDDIT the following line "guesses" that it's an XHR error from axios. I tried to use "typeof" first, but saw that it inherits from "object". Is this a limitation of axios or JS?
      if (this.error && this.error.config && this.error.config.method) {
        if (this.error.response.status === 401) {
          return this.error.response.data
        } else {
          return 'Error when retrieving ' + this.error.config.method.toUpperCase() + ' ' + this.error.config.url
        }
      } else {
        return 'Unexpected Error!'
      }
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
