<template>
  <div class="blank-layout">
    <router-view />
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: 'BlankLayout',
})
</script>

<style scoped>
.blank-layout {
  width: 100%;
  min-height: 100vh;
}
</style>
