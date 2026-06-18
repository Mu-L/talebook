import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const TEMPLATES_DIR = resolve(__dirname, '../../templates');

function renderTemplate(content, vars) {
    return content.replace(/\{\{(\w+)\}\}/g, (_, key) => vars[key] ?? `{{${key}}}`);
}

function jsonEscape(val) {
    return JSON.stringify(String(val)).slice(1, -1);
}

function copyTemplate(srcPath, destPath, vars) {
    const content = readFileSync(srcPath, 'utf-8');
    writeFileSync(destPath, renderTemplate(content, vars));
}

export async function initCommand(themeName, options) {
    const NAME_PATTERN = /^[a-z][a-z0-9-]*$/;
    if (!NAME_PATTERN.test(themeName)) {
        console.error(`ERROR: Theme name "${themeName}" is invalid. Use lowercase letters, digits, and hyphens only.`);
        process.exit(1);
    }

    const outputDir = resolve(options.output || themeName);

    if (existsSync(outputDir)) {
        console.error(`ERROR: Directory "${outputDir}" already exists. Choose a different name or use --output.`);
        process.exit(1);
    }

    const vars = {
        THEME_NAME: themeName,
        THEME_AUTHOR: jsonEscape(options.author || 'unknown'),
        THEME_DESCRIPTION: jsonEscape(options.description || 'A custom Talebook theme'),
        THEME_VERSION: '1.0.0',
    };

    console.log(`Creating theme "${themeName}" in ${outputDir} ...`);

    mkdirSync(join(outputDir, 'src'), { recursive: true });

    const vueTemplates = [
        'AppHeader',
        'AppFooter',
        'AppPress',
        'BookCards',
        'BookCards_Small',
        'BookList',
        'BookSourceImportDialog',
        'CaptchaWidget',
        'ImageCaptchaWidget',
        'ListBook',
        'Loading',
        'MetaList',
        'OpdsImportDialog',
        'SSLManager',
        'SaveOnlineDialog',
        'SerializeStatusBadge',
        'Upload',
    ];

    const files = [
        ['package.json.tpl', 'package.json'],
        ['vite.config.js.tpl', 'vite.config.js'],
        ['theme.json.tpl', 'theme.json'],
        [join('src', 'index.js.tpl'), join('src', 'index.js')],
        ...vueTemplates.map(name => [
            join('src', `${name}.vue.tpl`),
            join('src', `${name}.vue`),
        ]),
    ];

    for (const [tplRelPath, destRelPath] of files) {
        const srcPath = join(TEMPLATES_DIR, tplRelPath);
        const destPath = join(outputDir, destRelPath);
        copyTemplate(srcPath, destPath, vars);
    }

    console.log(`
✓ Theme scaffolded successfully!

Next steps:
  cd ${themeName}
  npm install
  npm run dev          # start Vite in watch mode
  npm run build        # build components to dist/
  npm run pack         # build + pack into theme.zip (one-command)
  theme-builder validate  # check theme.json

Edit the Vue component files in src/ to customize your theme.
`);
}
