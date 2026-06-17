<template>
    <v-row class="mt-6">
        <v-col
            cols="12"
            class="text-center"
        >
            <v-divider class="mb-3" />
            <p class="text-caption text-medium-emphasis">
                Powered by
                <v-btn
                    variant="text"
                    size="small"
                    href="https://github.com/talebook/talebook"
                    target="_blank"
                >
                    Talebook
                </v-btn>
                &bull; Theme: {{THEME_NAME}}
            </p>
        </v-col>
    </v-row>
</template>

<script setup>
// vue and vuetify components are provided by the Talebook host app.
</script>
