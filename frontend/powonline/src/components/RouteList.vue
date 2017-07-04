<template>
  <div id="RouteList">
    <transition name="slide">
    <!-- REDDIT when closing this card, the content below it only shifts upwards after the transition is complete. Is there no way to make it move at the same time? -->
      <v-card v-show="isAddBlockVisible">
        <v-card-row class="brown darken-4">
          <v-card-title>
            <span class="white--text">Add New Route</span>
            <v-spacer></v-spacer>
            <v-btn @click.native="closeAddBlock" icon light><v-icon>close</v-icon></v-btn>
          </v-card-title>
        </v-card-row>
        <v-card-text>
          <v-text-field
            name="route-input"
            id="RouteNameImput"
            @keyup.enter.native="addRoute"
            type='text'
            v-model:routename='routename'
            label='Enter a new routename' />
        </v-card-text>
        <v-divider></v-divider>
        <v-card-row actions>
          <v-btn @click.native="addRoute" flat>Add</v-btn>
        </v-card-row>
      </v-card>
    </transition>

    <!-- List all routes -->
    <route-block v-for="route in routes" :name="route.name" :key="route.name"></route-block>
  </div>
</template>


<script>
export default {
  name: 'route_list',
  methods: {
    addRoute: function (event) {
      this.$store.dispatch('addRouteRemote', {name: this.routename})
      const input = document.getElementById('RouteNameImput')
      input.focus()
      input.select()
    },
    closeAddBlock () {
      this.$store.commit('closeAddBlock', this.$route.path)
    }
  },
  created () {
    this.$store.commit('changeTitle', 'Route List')
    this.$store.dispatch('refreshRemote')
  },
  data () {
    return {
      routename: ''
    }
  },
  computed: {
    routes () {
      return this.$store.state.routes
    },
    isAddBlockVisible () {
      return this.$store.state.isAddBlockVisible[this.$route.path]
    }
  }
}
</script>

<style scoped>
.slide-enter-active, .slide-leave-active {
  transition: all .3s
}
.slide-enter {
  transform: translateY(-100px);
  opacity: 0;
}
.slide-leave-to {
  transform: translateY(-100px);
  opacity: 0;
}
</style>
