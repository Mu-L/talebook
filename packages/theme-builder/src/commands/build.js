import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { spawnSync } from 'node:child_process';

export async function buildCommand(options) {
    const configPath = resolve(options.config || 'vite.config.js');
    const outDir = options.outDir || 'dist';

    if (!existsSync(configPath)) {
        console.error(`ERROR: Vite config not found: ${configPath}`);
        console.error('Run "theme-builder init <name>" first, or ensure you are inside a theme project directory.');
        process.exit(1);
    }

    if (!existsSync(resolve('theme.json'))) {
        console.error('ERROR: theme.json not found. Ensure you are inside a theme project directory.');
        process.exit(1);
    }

    console.log(`Building theme with Vite (outDir: ${outDir}) ...`);

    const result = spawnSync(
        'npx',
        ['vite', 'build', '--config', configPath, '--outDir', outDir],
        { stdio: 'inherit', shell: true }
    );

    if (result.status !== 0) {
        console.error('\nBuild FAILED');
        process.exit(result.status ?? 1);
    }

    console.log(`\n✓ Build complete. Output: ${outDir}/`);
    console.log('Run "theme-builder validate" to verify the built theme.');
}
