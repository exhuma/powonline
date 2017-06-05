import Vue from 'vue'
import Router from 'vue-router'
import UserList from '@/components/UserList'
import StationList from '@/components/StationList'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/station',
      component: StationList
    },
    {
      path: '/user',
      component: UserList
    }
  ]
})
