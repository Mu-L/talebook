import { describe, expect, it } from 'vitest';
import { builtinThemeLoaders, isBuiltinTheme, loadBuiltinThemeComponent } from '~/utils/builtin-themes';

describe('builtin-themes', () => {
    it('recognizes only shipped builtin themes', () => {
        expect(isBuiltinTheme({ builtin: true, name: 'light-gray' })).toBe(true);
        expect(isBuiltinTheme({ builtin: true, name: 'minimal' })).toBe(true);
        expect(isBuiltinTheme({ builtin: true, name: 'graphite' })).toBe(true);
        expect(isBuiltinTheme({ builtin: true, name: 'brass' })).toBe(true);
        expect(isBuiltinTheme({ builtin: true, name: 'warm-red' })).toBe(true);
        expect(isBuiltinTheme({ builtin: false, name: 'light-gray' })).toBe(false);
        expect(isBuiltinTheme({ builtin: true, name: 'cobalt' })).toBe(false);
        expect(isBuiltinTheme({ builtin: true, name: 'custom-theme' })).toBe(false);
        expect(isBuiltinTheme(null)).toBe(false);
    });

    it('registers local component loaders for every builtin theme', async () => {
        for (const themeName of ['light-gray', 'minimal', 'graphite', 'brass', 'warm-red'] as const) {
            expect(builtinThemeLoaders[themeName].AppHeader).toEqual(expect.any(Function));
            expect(builtinThemeLoaders[themeName].AppFooter).toEqual(expect.any(Function));
        }
        expect(await loadBuiltinThemeComponent('custom-theme', 'AppHeader')).toBeNull();
    });
});
