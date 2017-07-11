<template>
  <v-list-tile>
    <v-list-tile-content>
      <v-list-tile-title>{{ name }}</v-list-tile-title>
    </v-list-tile-content>
    <v-list-tile-action>
      <v-btn icon ripple @click.native="openDashBoard(name)">
        <v-icon class="grey--text text--lighten-1">info</v-icon>
      </v-btn>
    </v-list-tile-action>
    <v-list-tile-action v-if="hasRole('admin')">
      <confirmation-dialog buttonText="Delete" :actionArgument="name" actionName="deleteStationRemote">
        <v-card-title slot="title">Do you want to delete the station "{{ name }}"?</v-card-title>
        <v-card-text slot="text">
          <p>this will delete the station with the name "{{ name }}" and all
            related information!</p>
          <p>Are you sure?</p>
        </v-card-text>
      </confirmation-dialog>
    </v-list-tile-action>
  </v-list-tile>
</template>

<script>
export default {
  name: 'station-block',
  props: {
    'name': {
      type: String,
      default: 'Unknown Station'
    }
  },
  methods: {
    openDashBoard (name) {
      this.$router.push('/station/' + name)
    },
    hasRole (roleName) {
      return this.$store.state.roles.indexOf(roleName) > -1
    }
  }
}
</script>
