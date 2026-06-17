import { Command } from 'commander';
import { initCommand } from './commands/init.js';
import { buildCommand } from './commands/build.js';
import { validateCommand } from './commands/validate.js';

export function createProgram() {
    const program = new Command();

    program
        .name('theme-builder')
        .description('CLI tool for building Talebook themes')
        .version('1.0.0');

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
        .option('--outDir <dir>', 'Output directory', 'dist')
        .option('--config <file>', 'Path to vite.config.js', 'vite.config.js')
        .action(buildCommand);

    program
        .command('validate')
        .description('Validate theme.json and component files')
        .option('--dir <dir>', 'Theme project directory', '.')
        .action(validateCommand);

    return program;
}
