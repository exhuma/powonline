import Vue from 'vue'
import Router from 'vue-router'
import TeamList from '@/components/TeamList'
import StationList from '@/components/StationList'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/station',
      component: StationList
    },
    {
      path: '/team',
      component: TeamList
    }
  ]
})
