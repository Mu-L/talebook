import { describe, expect, it } from 'vitest';
import { buildThemeDisplayList } from '~/utils/theme-display';

const t = (key: string) => ({
    'theme.defaultTheme': '默认主题',
    'theme.defaultThemeDescription': 'TaleBook 原生界面风格',
}[key] || key);

describe('theme-display', () => {
    it('keeps theme list order stable when a builtin theme is active', () => {
        const displayThemes = buildThemeDisplayList([
            { name: 'cloudflare-radar', active: false },
            { name: 'mybooks-midnight', active: true },
            { name: 'hacker-news-compact', active: false },
        ], t);

        expect(displayThemes.map(theme => theme._key)).toEqual([
            '__default__',
            'cloudflare-radar',
            'mybooks-midnight',
            'hacker-news-compact',
        ]);
        expect(displayThemes[0].active).toBe(false);
    });

    it('marks default active only when no custom or builtin theme is active', () => {
        const displayThemes = buildThemeDisplayList([
            { name: 'cloudflare-radar', active: false },
        ], t);

        expect(displayThemes.map(theme => theme._key)).toEqual(['__default__', 'cloudflare-radar']);
        expect(displayThemes[0].active).toBe(true);
    });

    it('keeps internal theme key when a builtin theme has a display name', () => {
        const displayThemes = buildThemeDisplayList([
            { name: 'cloudflare-radar', display_name: '蓝色科技主题', active: true },
        ], t);

        expect(displayThemes[1]._key).toBe('cloudflare-radar');
        expect(displayThemes[1].display_name).toBe('蓝色科技主题');
    });
});
