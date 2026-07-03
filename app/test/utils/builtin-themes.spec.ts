import { describe, expect, it } from 'vitest';
import { builtinThemeLoaders, isBuiltinTheme, loadBuiltinThemeComponent } from '~/utils/builtin-themes';

describe('builtin-themes', () => {
    it('recognizes only shipped builtin themes', () => {
        expect(isBuiltinTheme({ builtin: true, name: 'cloudflare-radar' })).toBe(true);
        expect(isBuiltinTheme({ builtin: true, name: 'mybooks-midnight' })).toBe(true);
        expect(isBuiltinTheme({ builtin: true, name: 'hacker-news-compact' })).toBe(true);
        expect(isBuiltinTheme({ builtin: false, name: 'cloudflare-radar' })).toBe(false);
        expect(isBuiltinTheme({ builtin: true, name: 'custom-theme' })).toBe(false);
        expect(isBuiltinTheme(null)).toBe(false);
    });

    it('registers local component loaders for every builtin theme', async () => {
        for (const themeName of ['cloudflare-radar', 'mybooks-midnight', 'hacker-news-compact'] as const) {
            expect(builtinThemeLoaders[themeName].AppHeader).toEqual(expect.any(Function));
            expect(builtinThemeLoaders[themeName].AppFooter).toEqual(expect.any(Function));
        }
        expect(await loadBuiltinThemeComponent('custom-theme', 'AppHeader')).toBeNull();
    });
});
