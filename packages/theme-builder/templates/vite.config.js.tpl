import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'node:path';
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

// __dirname is not available in ES modules — derive it from import.meta.url
const __dirname = fileURLToPath(new URL('.', import.meta.url));

// Auto-discover all Vue component files in src/
const srcDir = resolve(__dirname, 'src');
const themeJson = JSON.parse(readFileSync(resolve(__dirname, 'theme.json'), 'utf-8'));
const entries = {};
for (const componentName of Object.keys(themeJson.components || {})) {
    const filePath = resolve(srcDir, `${componentName}.vue`);
    if (existsSync(filePath)) {
        entries[componentName] = filePath;
    }
}

function injectCssIntoJs() {
    return {
        name: 'talebook-theme-css-inject',
        enforce: 'post',
        generateBundle(_options, bundle) {
            const cssAssets = Object.entries(bundle).filter(
                ([fileName, item]) => item.type === 'asset' && fileName.endsWith('.css')
            );
            if (cssAssets.length === 0) return;

            const css = cssAssets.map(([, item]) => String(item.source)).join('\n');
            const injection = `
const __talebookThemeCss = ${JSON.stringify(css)};
if (typeof document !== 'undefined') {
  const __talebookThemeStyleId = 'talebook-theme-style-{{THEME_NAME}}';
  let __talebookThemeStyle = document.getElementById(__talebookThemeStyleId);
  if (!__talebookThemeStyle) {
    __talebookThemeStyle = document.createElement('style');
    __talebookThemeStyle.id = __talebookThemeStyleId;
    __talebookThemeStyle.setAttribute('data-talebook-theme', '{{THEME_NAME}}');
    document.head.appendChild(__talebookThemeStyle);
  }
  __talebookThemeStyle.textContent = __talebookThemeCss;
}
`;

            for (const item of Object.values(bundle)) {
                if (item.type === 'chunk' && item.isEntry) {
                    item.code = injection + item.code;
                }
            }

            for (const [fileName] of cssAssets) {
                delete bundle[fileName];
            }
        },
    };
}

export default defineConfig({
    plugins: [vue(), injectCssIntoJs()],
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
