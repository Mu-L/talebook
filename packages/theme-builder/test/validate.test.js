import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { validateThemeJson } from '../src/commands/validate.js';

describe('validateThemeJson', () => {
    const validTheme = {
        name: 'dark-elegant',
        version: '1.0.0',
        author: 'talebook',
        description: 'A dark elegant theme',
        requires: '>=0.9.0',
        components: {
            AppHeader: '/static/themes/dark-elegant/components/AppHeader.js',
            AppFooter: '/static/themes/dark-elegant/components/AppFooter.js',
        },
    };

    it('accepts a valid theme.json', () => {
        const { valid, errors } = validateThemeJson(validTheme, '/nonexistent');
        assert.equal(errors.length, 0, `Expected no errors, got: ${errors.join(', ')}`);
        assert.equal(valid, true);
    });

    it('rejects theme with missing required fields', () => {
        const theme = { name: 'my-theme' };
        const { valid, errors } = validateThemeJson(theme, '/nonexistent');
        assert.equal(valid, false);
        assert.ok(errors.some(e => e.includes('version')));
        assert.ok(errors.some(e => e.includes('author')));
        assert.ok(errors.some(e => e.includes('description')));
        assert.ok(errors.some(e => e.includes('components')));
    });

    it('rejects name with uppercase letters', () => {
        const theme = { ...validTheme, name: 'DarkElegant' };
        const { valid, errors } = validateThemeJson(theme, '/nonexistent');
        assert.equal(valid, false);
        assert.ok(errors.some(e => e.includes('"name"')));
    });

    it('rejects name with spaces', () => {
        const theme = { ...validTheme, name: 'dark elegant' };
        const { valid, errors } = validateThemeJson(theme, '/nonexistent');
        assert.equal(valid, false);
        assert.ok(errors.some(e => e.includes('"name"')));
    });

    it('rejects invalid semver version', () => {
        const theme = { ...validTheme, version: 'v1.0' };
        const { valid, errors } = validateThemeJson(theme, '/nonexistent');
        assert.equal(valid, false);
        assert.ok(errors.some(e => e.includes('"version"')));
    });

    it('rejects empty components object', () => {
        const theme = { ...validTheme, components: {} };
        const { valid, errors } = validateThemeJson(theme, '/nonexistent');
        assert.equal(valid, false);
        assert.ok(errors.some(e => e.includes('"components"')));
    });

    it('rejects components as an array', () => {
        const theme = { ...validTheme, components: ['AppHeader'] };
        const { valid, errors } = validateThemeJson(theme, '/nonexistent');
        assert.equal(valid, false);
        assert.ok(errors.some(e => e.includes('"components"')));
    });

    it('warns about unusual requires format', () => {
        const theme = { ...validTheme, requires: 'latest' };
        const { valid, warnings } = validateThemeJson(theme, '/nonexistent');
        // Still valid (requires is optional), but should have a warning
        assert.equal(valid, true);
        assert.ok(warnings.some(w => w.includes('"requires"')));
    });

    it('accepts valid requires patterns', () => {
        for (const req of ['>=0.9.0', '0.9.0', '>1.0.0', '<=2.0.0']) {
            const theme = { ...validTheme, requires: req };
            const { warnings } = validateThemeJson(theme, '/nonexistent');
            assert.ok(!warnings.some(w => w.includes('"requires"')), `Unexpected warning for requires="${req}"`);
        }
    });

    it('warns about missing component files', () => {
        const theme = {
            ...validTheme,
            components: {
                AppHeader: '/static/themes/dark-elegant/components/AppHeader.js',
            },
        };
        const { valid, warnings } = validateThemeJson(theme, '/nonexistent/dist');
        // Valid structure, but files don't exist on disk
        assert.equal(valid, true);
        assert.ok(warnings.some(w => w.includes('AppHeader') && w.includes('not found')));
    });
});
