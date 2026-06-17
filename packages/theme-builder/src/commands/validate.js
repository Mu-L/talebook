import { readFileSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';

const REQUIRED_FIELDS = ['name', 'version', 'author', 'description', 'components'];
const NAME_PATTERN = /^[a-z][a-z0-9-]*$/;
const VERSION_PATTERN = /^\d+\.\d+\.\d+$/;
const REQUIRES_PATTERN = /^(>=|<=|>|<|=|~|\^)?\d+\.\d+\.\d+$/;

export function validateThemeJson(themeJson, themeDir = '.') {
    const errors = [];
    const warnings = [];

    for (const field of REQUIRED_FIELDS) {
        if (!themeJson[field]) {
            errors.push(`Missing required field: "${field}"`);
        }
    }

    if (errors.length > 0) {
        return { valid: false, errors, warnings };
    }

    if (!NAME_PATTERN.test(themeJson.name)) {
        errors.push(`"name" must be lowercase letters, digits and hyphens only (got: "${themeJson.name}")`);
    }

    if (!VERSION_PATTERN.test(themeJson.version)) {
        errors.push(`"version" must be a valid semver like "1.0.0" (got: "${themeJson.version}")`);
    }

    if (themeJson.requires && !REQUIRES_PATTERN.test(themeJson.requires)) {
        warnings.push(`"requires" format is unusual (got: "${themeJson.requires}"), expected e.g. ">=0.9.0"`);
    }

    if (typeof themeJson.components !== 'object' || Array.isArray(themeJson.components)) {
        errors.push('"components" must be an object mapping component names to file paths');
    } else if (Object.keys(themeJson.components).length === 0) {
        errors.push('"components" must have at least one entry');
    } else {
        for (const [componentName, componentPath] of Object.entries(themeJson.components)) {
            if (!componentPath || typeof componentPath !== 'string') {
                errors.push(`Component "${componentName}" has invalid path`);
                continue;
            }
            const absolutePath = resolve(themeDir, componentPath.replace(/^\/static\/themes\/[^/]+\//, ''));
            if (!existsSync(absolutePath)) {
                warnings.push(`Component "${componentName}" file not found: ${componentPath} (expected at ${absolutePath})`);
            }
        }
    }

    return { valid: errors.length === 0, errors, warnings };
}

export async function validateCommand(options) {
    const themeDir = resolve(options.dir || '.');
    const themeJsonPath = join(themeDir, 'theme.json');

    console.log(`Validating theme at: ${themeDir}`);

    if (!existsSync(themeJsonPath)) {
        console.error('ERROR: theme.json not found');
        process.exit(1);
    }

    let themeJson;
    try {
        themeJson = JSON.parse(readFileSync(themeJsonPath, 'utf-8'));
    } catch (err) {
        console.error(`ERROR: Failed to parse theme.json: ${err.message}`);
        process.exit(1);
    }

    // Validate against the project root: after "theme-builder build" the output
    // lands in components/ at the project root, which is the same layout the
    // backend serves under /static/themes/<name>/.
    const { valid, errors, warnings } = validateThemeJson(themeJson, themeDir);

    if (warnings.length > 0) {
        console.warn('\nWarnings:');
        for (const w of warnings) {
            console.warn(`  ⚠  ${w}`);
        }
    }

    if (!valid) {
        console.error('\nErrors:');
        for (const e of errors) {
            console.error(`  ✗  ${e}`);
        }
        console.error('\nValidation FAILED');
        process.exit(1);
    }

    console.log('\n✓ theme.json is valid');
}
