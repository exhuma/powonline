<template>
  <v-card class="mt-3">
    <v-card-row class="brown darken-1">
      <v-card-title><span class="white--text">Station: "{{ name }}"</span></v-card-title>
    </v-card-row>
    <v-card-text>
      <v-card-row>
        <a :href="'#/station/' + name">Dashboard</a>
      </v-card-row>
    </v-card-text>
    <v-divider></v-divider>
    <v-card-row actions>
      <confirmation-dialog buttonText="Delete" :actionArgument="name" actionName="deleteStationRemote">
        <v-card-title slot="title">Do you want to delete the station "{{ name }}"?</v-card-title>
        <v-card-text slot="text">
          <p>this will delete the station with the name "{{ name }}" and all
            related information!</p>
          <p>Are you sure?</p>
        </v-card-text>
      </confirmation-dialog>
    </v-card-row>
  </v-card>
</template>

<script>
export default {
  name: 'station-block',
  props: {
    'name': {
      type: String,
      default: 'Unknown Station'
    }
  }
}
</script>
