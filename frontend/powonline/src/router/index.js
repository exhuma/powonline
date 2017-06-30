import Vue from 'vue'
import Router from 'vue-router'
import RouteList from '@/components/RouteList'
import StationDashboard from '@/components/StationDashboard'
import StationList from '@/components/StationList'
import TeamList from '@/components/TeamList'
import UserList from '@/components/UserList'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/station',
      component: StationList
    },
    {
      path: '/station/:stationName',
      component: StationDashboard
    },
    {
      path: '/team',
      component: TeamList
    },
    {
      path: '/route',
      component: RouteList
    },
    {
      path: '/user',
      component: UserList
    }
  ]
})
