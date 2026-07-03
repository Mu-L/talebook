import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it } from 'vitest';
import { useThemeStore } from '~/stores/theme';

const activeThemeCacheKey = 'talebook.activeTheme';

const cachedTheme = {
    id: 'builtin-hacker-news-compact',
    name: 'hacker-news-compact',
    version: '1.0.0',
    author: 'Talebook',
    description: 'Hacker News 式紧凑风格',
    active: true,
    installed_at: null,
    builtin: true,
    components: {
        AppHeader: 'builtin:hacker-news-compact/AppHeader',
        AppFooter: 'builtin:hacker-news-compact/AppFooter',
    },
};

describe('theme store', () => {
    beforeEach(() => {
        window.localStorage.clear();
        setActivePinia(createPinia());
    });

    it('hydrates active theme synchronously from localStorage', () => {
        window.localStorage.setItem(activeThemeCacheKey, JSON.stringify(cachedTheme));

        const store = useThemeStore();

        expect(store.activeTheme).toEqual(cachedTheme);
    });

    it('ignores invalid cached theme JSON', () => {
        window.localStorage.setItem(activeThemeCacheKey, '{invalid');

        const store = useThemeStore();

        expect(store.activeTheme).toBeNull();
    });
});
