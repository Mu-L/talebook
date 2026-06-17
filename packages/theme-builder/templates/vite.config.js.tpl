import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'node:path';

// Pre-configured Vite config for Talebook themes.
// Each component is built as a self-contained ESM file (vue bundled inline)
// so it can be loaded via native browser dynamic import() without an import map.
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
            // Output to components/ so the ZIP layout matches what Talebook serves:
            //   <theme-name>/components/AppHeader.js
            //   <theme-name>/components/AppFooter.js
            fileName: (format, entryName) => `${entryName}.js`,
        },
        // Output directly into components/ — keep src/ for source only.
        outDir: 'components',
        emptyOutDir: true,
    },
});
