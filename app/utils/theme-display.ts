export function buildThemeDisplayList(themes: any[], t: (key: string) => string) {
    const hasActiveCustomTheme = themes.some(theme => theme.active);
    const defaultItem = {
        _key: '__default__',
        _isDefault: true,
        name: t('theme.defaultTheme'),
        description: t('theme.defaultThemeDescription'),
        active: !hasActiveCustomTheme,
    };
    const customItems = themes.map(theme => ({
        ...theme,
        _key: theme.name,
        _isDefault: false,
    }));

    return [defaultItem, ...customItems];
}
