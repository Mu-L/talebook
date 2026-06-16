import { defineStore } from 'pinia'

export interface ThemeComponent {
    [key: string]: string
}

export interface Theme {
    id: number
    name: string
    version: string
    author: string
    description: string
    active: boolean
    installed_at: string | null
    components: ThemeComponent
}

export const useThemeStore = defineStore('themePlugin', () => {
    const activeTheme = ref<Theme | null>(null)
    const loading = ref(false)

    async function fetchActiveTheme() {
        const { $backend } = useNuxtApp()
        try {
            const res = await $backend('/api/themes/active')
            if (res.err === 'ok') {
                activeTheme.value = res.theme
            }
        } catch (e) {
            // 静默失败：主题加载失败不影响主站功能
        }
    }

    async function activate(name: string) {
        const { $backend } = useNuxtApp()
        const res = await $backend('/api/themes/activate', {
            method: 'POST',
            body: JSON.stringify({ name }),
            headers: { 'Content-Type': 'application/json' },
        })
        if (res.err === 'ok') {
            activeTheme.value = res.theme ?? null
        }
        return res
    }

    async function deactivate() {
        const { $backend } = useNuxtApp()
        const res = await $backend('/api/themes/activate', {
            method: 'POST',
            body: JSON.stringify({ name: '' }),
            headers: { 'Content-Type': 'application/json' },
        })
        if (res.err === 'ok') {
            activeTheme.value = null
        }
        return res
    }

    return {
        activeTheme,
        loading,
        fetchActiveTheme,
        activate,
        deactivate,
    }
})
