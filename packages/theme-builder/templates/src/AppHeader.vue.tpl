<template>
    <v-app-bar
        color="primary"
        density="compact"
    >
        <v-toolbar-title>{{ title }}</v-toolbar-title>

        <template #append>
            <v-btn
                icon="mdi-magnify"
                @click="$router.push('/search')"
            />
            <v-btn
                icon="mdi-home"
                @click="$router.push('/')"
            />
        </template>
    </v-app-bar>
</template>

<script setup>
// This component is provided by the Talebook host app at runtime.
// Do not import vue or vuetify here — they are already available globally.
import { computed } from 'vue';

// Access Vue Router (provided by host)
import { useRouter } from 'vue-router';

const router = useRouter();

const title = computed(() => '{{THEME_NAME}}');
</script>
