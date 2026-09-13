import {defineStore} from 'pinia'
import {login as loginApi} from '../api/user'


interface UserInfo {
  username:string
  id?:number
}

export const useUserStore = defineStore("user",{
  state:()=>({
    token:localStorage.getItem('token') || '',
    userInfo:null as UserInfo | null
  }),
  getters:{
    isLogin:(state)=>!!state.token
  },
  actions:{
    async login(username:string,password:string) {
      const res = await loginApi({
        username,
        password,
      })

      this.token = res.token
      localStorage.setItem('token',res.token)
      this.userInfo={
        username,
      }
      return res
    },
    logout(){
      this.token='',
      this.userInfo=null
      localStorage.removeItem('token')
    }
  }
})