import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'node:path';

// Pre-configured Vite config for Talebook themes.
// vue, vuetify, pinia, and vue-router are marked as external so the theme
// reuses the host app's instances — keeping bundle size small and avoiding
// duplicate Vue reactivity systems.
export default defineConfig({
    plugins: [vue()],
    build: {
        lib: {
            // Each component is compiled to its own ESM file.
            // Add or remove entries to match the components in theme.json.
            entry: {
                AppHeader: resolve('src/AppHeader.vue'),
                AppFooter: resolve('src/AppFooter.vue'),
            },
            formats: ['es'],
            fileName: (format, entryName) => `components/${entryName}.js`,
        },
        rollupOptions: {
            // These packages are provided by Talebook at runtime.
            // Do NOT include them in the theme bundle.
            external: ['vue', 'vuetify', 'vuetify/components', 'vuetify/directives', 'pinia', 'vue-router'],
            output: {
                globals: {
                    vue: 'Vue',
                    vuetify: 'Vuetify',
                    pinia: 'Pinia',
                    'vue-router': 'VueRouter',
                },
            },
        },
        outDir: 'dist',
        emptyOutDir: true,
    },
});
