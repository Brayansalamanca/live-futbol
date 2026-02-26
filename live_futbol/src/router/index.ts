import { createRouter, createWebHistory } from 'vue-router'

// Importa tus vistas desde views
import Home from '../views/hom.vue'
import Soporte from '../views/soport.vue'
import Terminos from '../views/termino.vue'
import Tipos from '../views/tipo.vue'
import Estadisticas from '../views/estadistica.vue'
import Ranking from '../views/rankin.vue'
import Register from '../views/registe.vue'
import Login from '../views/logi.vue'
import Formularion from '../views/formulario.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/soporte', component: Soporte },
  { path: '/terminos', component: Terminos },
  { path: '/tipos', component: Tipos },
  { path: '/estadisticas', component: Estadisticas },
  { path: '/ranking', component: Ranking },
  { path: '/register', component: Register },
  { path: '/login', component: Login },
  { path: '/formularion', component: Formularion }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
