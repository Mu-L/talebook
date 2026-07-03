export const builtinThemeLoaders = {
    'cloudflare-radar': {
        AppHeader: () => import('@/components/themes/cloudflare-radar/AppHeader.vue'),
        AppFooter: () => import('@/components/themes/cloudflare-radar/AppFooter.vue'),
    },
    'mybooks-midnight': {
        AppHeader: () => import('@/components/themes/mybooks-midnight/AppHeader.vue'),
        AppFooter: () => import('@/components/themes/mybooks-midnight/AppFooter.vue'),
    },
    'hacker-news-compact': {
        AppHeader: () => import('@/components/themes/hacker-news-compact/AppHeader.vue'),
        AppFooter: () => import('@/components/themes/hacker-news-compact/AppFooter.vue'),
    },
} as const

export function isBuiltinTheme(theme: { builtin?: boolean, name?: string } | null | undefined) {
    return Boolean(theme?.builtin && theme.name && theme.name in builtinThemeLoaders)
}

export async function loadBuiltinThemeComponent(themeName: string, componentName: 'AppHeader' | 'AppFooter') {
    const loader = builtinThemeLoaders[themeName as keyof typeof builtinThemeLoaders]?.[componentName]
    if (!loader) return null
    const mod = await loader()
    return mod.default || mod
}
