<script>
</script>

<template>
  <nav>
    <ul>
      <li class="img">
        <img src="@/assets/logo.png" alt="Logo" />
      </li>

      <template v-if="isAuthenticated">
        <li><a href="/formulario">formulario</a></li>
        <li><a href="/tipos">personalisado</a></li>
        <li><a href="/radar">estadísticas</a></li>
        <li><a href="/videos">videos</a></li>
        <li><a href="/voz">prueba de voz</a></li>
        <li><a href="/ranking">ranking</a></li>
        <li><a href="/logout">Logout</a></li>
      </template>

      <template v-else>
        <li><a href="/">Home</a></li>
        <li><a href="/registe">registrarse</a></li>
        <li><a href="/signin">iniciar sesión</a></li>
        <li><a href="/soporte">soporte</a></li>
      </template>
    </ul>
  </nav>
</template>

<style>
</style>