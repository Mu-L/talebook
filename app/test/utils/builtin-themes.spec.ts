import { describe, expect, it } from 'vitest';
import { buildBuiltinThemeOverlayCss, builtinThemeNames } from '~/utils/builtin-theme-overlay';
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

    it('generates overlay styles for teleported dialogs and menus', () => {
        for (const themeName of builtinThemeNames) {
            const css = buildBuiltinThemeOverlayCss(themeName);

            expect(css).toContain(`body.tb-current-builtin-theme-${themeName}.tb-current-builtin-theme-mode-light .v-overlay-container`);
            expect(css).toContain(`body.tb-current-builtin-theme-${themeName}.tb-current-builtin-theme-mode-dark .v-overlay-container`);
            expect(css).toContain('.v-overlay__content .v-toolbar.bg-primary');
            expect(css).toContain('.v-overlay__content .v-card');
        }
    });

    it('uses the minimal theme primary color for overlay toolbars', () => {
        const css = buildBuiltinThemeOverlayCss('minimal');

        expect(css).toContain('body.tb-current-builtin-theme-minimal.tb-current-builtin-theme-mode-light .v-overlay-container');
        expect(css).toContain('background: #ff6600 !important;');
        expect(css).toContain('body.tb-current-builtin-theme-minimal.tb-current-builtin-theme-mode-dark .v-overlay-container');
        expect(css).toContain('background: #d35400 !important;');
    });
});
