<template>
    <v-app :theme="store.theme">
        <Loading />
        <template v-if="store.nav">
            <ClientOnly>
                <component :is="dynamicHeader" />
                <template #fallback>
                    <AppHeader />
                </template>
            </ClientOnly>
        </template>
        <v-main>
            <v-container fluid>
                <AppPress v-if="store.nav" />
                <slot />
                <template v-if="store.nav">
                    <ClientOnly>
                        <component :is="dynamicFooter" />
                        <template #fallback>
                            <AppFooter />
                        </template>
                    </ClientOnly>
                </template>
            </v-container>

            <v-dialog
                v-model="store.alert.show"
                persistent
                :width="display.smAndDown.value ? '80%' : '50%'"
            >
                <v-card>
                    <v-toolbar
                        dark
                        color="primary"
                    >
                        <v-toolbar-title align-center />
                    </v-toolbar>
                    <v-card-text class="pt-12">
                        <v-alert
                            outlined
                            :model-value="store.alert.show"
                            :type="store.alert.type"
                            v-html="store.alert.msg"
                        />
                    </v-card-text>
                    <v-card-actions v-if="store.alert.type!=='success' || store.alert.to">
                        <v-spacer />
                        <v-btn
                            v-if="store.alert.to"
                            color="primary"
                            @click="router.push(store.alert.to); store.closeAlert()"
                        >
                            {{ $t('messages.ok') }}
                        </v-btn>
                        <v-btn
                            v-else
                            color="primary"
                            @click="store.closeAlert()"
                        >
                            {{ $t('messages.dialogClose') }}
                        </v-btn>
                        <v-spacer />
                    </v-card-actions>
                </v-card>
            </v-dialog>
        </v-main>
        <Upload v-if="store.nav" />
    </v-app>
</template>

<script setup>
import { shallowRef, computed, onMounted, watch } from 'vue';
import { useRouter, useHead } from 'nuxt/app';
import { useMainStore } from '@/stores/main';
import { useThemeStore } from '@/stores/theme';
import { useDisplay } from 'vuetify';
import Loading from '@/components/Loading.vue';
import AppHeader from '@/components/AppHeader.vue';
import AppFooter from '@/components/AppFooter.vue';

const store = useMainStore();
const themeStore = useThemeStore();
const display = useDisplay();
const router = useRouter();

const dynamicHeader = shallowRef(AppHeader);
const dynamicFooter = shallowRef(AppFooter);

useHead({
    title: computed(() => store.site_title),
    titleTemplate: computed(() => store.site_title_template),
});

function withThemeVersion(url, theme) {
    const version = encodeURIComponent(theme?.version || theme?.installed_at || Date.now());
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}v=${version}`;
}

async function applyThemeComponents(theme) {
    if (!theme?.components) {
        dynamicHeader.value = AppHeader;
        dynamicFooter.value = AppFooter;
        return;
    }

    if (theme.components.AppHeader) {
        try {
            const mod = await import(/* @vite-ignore */ withThemeVersion(theme.components.AppHeader, theme));
            dynamicHeader.value = mod.default || mod;
        } catch (e) {
            console.warn('主题 Header 加载失败，使用默认', e);
            dynamicHeader.value = AppHeader;
        }
    } else {
        dynamicHeader.value = AppHeader;
    }

    if (theme.components.AppFooter) {
        try {
            const mod = await import(/* @vite-ignore */ withThemeVersion(theme.components.AppFooter, theme));
            dynamicFooter.value = mod.default || mod;
        } catch (e) {
            console.warn('主题 Footer 加载失败，使用默认', e);
            dynamicFooter.value = AppFooter;
        }
    } else {
        dynamicFooter.value = AppFooter;
    }
}

onMounted(async () => {
    store.setLoading(false);
    await Promise.all([store.bootstrap(), themeStore.fetchActiveTheme()]);
    await applyThemeComponents(themeStore.activeTheme);
});

// 管理员激活/停用主题后立即切换组件，无需刷新页面
watch(() => themeStore.activeTheme, async (theme) => {
    await applyThemeComponents(theme);
});
</script>
