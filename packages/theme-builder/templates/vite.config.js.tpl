import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'node:path';
import { readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

// __dirname is not available in ES modules — derive it from import.meta.url
const __dirname = fileURLToPath(new URL('.', import.meta.url));

// Auto-discover all Vue component files in src/
const srcDir = resolve(__dirname, 'src');
const entries = {};
for (const file of readdirSync(srcDir)) {
    const match = file.match(/^(.+)\.vue$/);
    if (match) {
        entries[match[1]] = resolve(srcDir, file);
    }
}

export default defineConfig({
    plugins: [vue()],
    build: {
        lib: {
            entry: entries,
            formats: ['es'],
            fileName: (format, entryName) => `${entryName}.js`,
        },
        // Bundle all dependencies (vue, etc.) into each component JS file so the
        // browser can dynamic-import() them without a host-provided import map.
        outDir: 'components',
        emptyOutDir: true,
    },
});
