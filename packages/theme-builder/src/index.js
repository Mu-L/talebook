import { Command } from 'commander';
import { createRequire } from 'node:module';
import { initCommand } from './commands/init.js';
import { buildCommand } from './commands/build.js';
import { validateCommand } from './commands/validate.js';
import { packCommand } from './commands/pack.js';

const require = createRequire(import.meta.url);
const pkg = require('../package.json');

export function createProgram() {
    const program = new Command();

    program
        .name('theme-builder')
        .description('CLI tool for building Talebook themes')
        .version(pkg.version);

    program
        .command('init <theme-name>')
        .description('Scaffold a new Talebook theme project')
        .option('-o, --output <dir>', 'Output directory (defaults to theme name)')
        .option('--author <author>', 'Theme author name', 'unknown')
        .option('--description <desc>', 'Theme description', 'A custom Talebook theme')
        .action(initCommand);

    program
        .command('build')
        .description('Build theme components using Vite (run inside a theme project)')
        .option('--outDir <dir>', 'Output directory', 'components')
        .option('--config <file>', 'Path to vite.config.js', 'vite.config.js')
        .action(buildCommand);

    program
        .command('validate')
        .description('Validate theme.json and component files')
        .option('--dir <dir>', 'Theme project directory', '.')
        .action(validateCommand);

    program
        .command('pack')
        .description('Build and pack theme into a ZIP file for Talebook installation')
        .option('--dir <dir>', 'Theme project directory', '.')
        .option('--outDir <dir>', 'Components output directory', 'components')
        .option('--output <file>', 'Output ZIP path (default: dist/<theme-name>.zip)')
        .option('--no-build', 'Skip the build step (use existing components/)')
        .action(packCommandWithBuild);

    return program;
}

async function packCommandWithBuild(options) {
    if (options.build !== false) {
        // Run build first
        await buildCommand(options);
    }
    // Then pack
    await packCommand(options);
}
