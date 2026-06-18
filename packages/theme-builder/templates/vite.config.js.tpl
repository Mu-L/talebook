import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'node:path';
import { readdirSync } from 'node:fs';

// Auto-discover all Vue component files in src/
const srcDir = resolve('src');
const entries = {};
for (const file of readdirSync(srcDir)) {
    const match = file.match(/^(.+)\.vue$/);
    if (match) {
        entries[match[1]] = resolve(srcDir, file);
    }
}

// Host-provided dependencies — not bundled, loaded at runtime from the Talebook app
const hostExternals = [
    'vue',
    'vue-router',
    'vue-i18n',
    'vuetify',
    'nuxt/app',
];

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            // @ maps to the host app's source root — all @/ imports are external
            '@': resolve(__dirname, 'node_modules/.host-app'),
        },
    },
    build: {
        lib: {
            entry: entries,
            formats: ['es'],
            fileName: (format, entryName) => `${entryName}.js`,
        },
        rollupOptions: {
            external: (id) => {
                // Explicit host packages
                if (hostExternals.includes(id)) return true;
                // Nuxt aliases: @/stores/..., #i18n, ~/utils/...
                if (id.startsWith('@/') || id.startsWith('#') || id.startsWith('~/')) return true;
                // Sub-paths of host packages (e.g. vuetify/components, vue/dist/...)
                if (hostExternals.some(pkg => id === pkg || id.startsWith(pkg + '/'))) return true;
                return false;
            },
            output: {
                // Preserve module structure so each component is self-contained
                preserveModules: false,
            },
        },
        outDir: 'components',
        emptyOutDir: true,
    },
});
