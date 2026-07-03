export const builtinThemeLoaders = {
    'light-gray': {
        AppHeader: () => import('@/components/themes/light-gray/AppHeader.vue'),
        AppFooter: () => import('@/components/themes/light-gray/AppFooter.vue'),
    },
    'minimal': {
        AppHeader: () => import('@/components/themes/minimal/AppHeader.vue'),
        AppFooter: () => import('@/components/themes/minimal/AppFooter.vue'),
    },
    'graphite': {
        AppHeader: () => import('@/components/themes/graphite/AppHeader.vue'),
        AppFooter: () => import('@/components/themes/graphite/AppFooter.vue'),
    },
    'brass': {
        AppHeader: () => import('@/components/themes/brass/AppHeader.vue'),
        AppFooter: () => import('@/components/themes/brass/AppFooter.vue'),
    },
    'warm-red': {
        AppHeader: () => import('@/components/themes/warm-red/AppHeader.vue'),
        AppFooter: () => import('@/components/themes/warm-red/AppFooter.vue'),
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
