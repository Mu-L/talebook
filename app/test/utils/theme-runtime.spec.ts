import { describe, expect, it } from 'vitest';
import { clearInjectedThemeStyles, resolveThemeModuleUrl, withThemeVersion } from '~/utils/theme-runtime';

describe('theme-runtime', () => {
    it('keeps theme module imports same-origin and adds cache busting', () => {
        const url = resolveThemeModuleUrl('/static/themes/night/components/AppHeader.js', { version: '1.0.0' });
        expect(url).toBe('/static/themes/night/components/AppHeader.js?v=1.0.0');
    });

    it('preserves existing query strings when appending theme version', () => {
        expect(withThemeVersion('/static/themes/night/AppHeader.js?import', { installed_at: '2026-01-01' }))
            .toBe('/static/themes/night/AppHeader.js?import&v=2026-01-01');
    });

    it('removes previously injected theme styles', () => {
        const style = document.createElement('style');
        style.setAttribute('data-talebook-theme', 'night');
        document.head.appendChild(style);

        clearInjectedThemeStyles();

        expect(document.querySelector('style[data-talebook-theme]')).toBeNull();
    });
});
