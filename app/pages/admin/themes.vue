<template>
    <div>
        <v-card class="my-2 elevation-4">
            <v-card-title class="py-4 pl-4">
                {{ $t('theme.title') }}
            </v-card-title>
            <v-card-text>
                <p class="text-medium-emphasis mb-4">
                    {{ $t('theme.description') }}
                </p>

                <!-- 安装新主题 -->
                <v-row class="mb-4">
                    <v-col cols="12">
                        <v-text-field
                            v-model="installUrl"
                            :label="$t('theme.installUrlLabel')"
                            :placeholder="$t('theme.installUrlPlaceholder')"
                            prepend-icon="mdi-download"
                            variant="outlined"
                            density="compact"
                            hide-details
                            class="mb-2"
                        />
                        <v-btn
                            color="primary"
                            :loading="installing"
                            :disabled="!installUrl"
                            prepend-icon="mdi-package-down"
                            @click="installTheme"
                        >
                            {{ $t('theme.install') }}
                        </v-btn>
                    </v-col>
                </v-row>

                <v-divider class="mb-4" />

                <!-- 已安装主题列表 -->
                <div class="text-subtitle-1 mb-2">
                    {{ $t('theme.installed') }}
                </div>
                <v-alert
                    v-if="themes.length === 0"
                    type="info"
                    variant="tonal"
                    density="compact"
                >
                    {{ $t('theme.noThemes') }}
                </v-alert>
                <v-row>
                    <v-col
                        v-for="theme in themes"
                        :key="theme.name"
                        cols="12"
                        sm="6"
                        md="4"
                    >
                        <v-card
                            :color="theme.active ? 'primary' : undefined"
                            :variant="theme.active ? 'tonal' : 'outlined'"
                            class="pa-3"
                        >
                            <div class="d-flex align-center mb-2">
                                <v-icon
                                    :color="theme.active ? 'primary' : 'default'"
                                    class="mr-2"
                                >
                                    mdi-palette
                                </v-icon>
                                <span class="font-weight-bold">{{ theme.name }}</span>
                                <v-chip
                                    v-if="theme.active"
                                    color="primary"
                                    size="x-small"
                                    class="ml-2"
                                >
                                    {{ $t('theme.active') }}
                                </v-chip>
                            </div>
                            <div class="text-caption text-medium-emphasis mb-1">
                                v{{ theme.version }}
                                <span v-if="theme.author"> · {{ theme.author }}</span>
                            </div>
                            <div
                                v-if="theme.description"
                                class="text-body-2 mb-3"
                            >
                                {{ theme.description }}
                            </div>
                            <div class="d-flex gap-2">
                                <v-btn
                                    v-if="!theme.active"
                                    size="small"
                                    color="primary"
                                    variant="tonal"
                                    :loading="activating === theme.name"
                                    @click="activateTheme(theme.name)"
                                >
                                    {{ $t('theme.activate') }}
                                </v-btn>
                                <v-btn
                                    v-else
                                    size="small"
                                    variant="tonal"
                                    :loading="activating === '__deactivate__'"
                                    @click="deactivateTheme"
                                >
                                    {{ $t('theme.deactivate') }}
                                </v-btn>
                                <v-btn
                                    size="small"
                                    color="error"
                                    variant="text"
                                    :loading="deleting === theme.name"
                                    @click="deleteTheme(theme.name)"
                                >
                                    {{ $t('common.delete') }}
                                </v-btn>
                            </div>
                        </v-card>
                    </v-col>
                </v-row>
            </v-card-text>
        </v-card>

        <v-snackbar
            v-model="snackbar.show"
            :color="snackbar.color"
            timeout="3000"
        >
            {{ snackbar.msg }}
        </v-snackbar>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useNuxtApp } from 'nuxt/app';
import { useThemeStore } from '@/stores/theme';

const { $backend } = useNuxtApp();
const { t } = useI18n();
const themeStore = useThemeStore();

const themes = ref([]);
const installUrl = ref('');
const installing = ref(false);
const activating = ref('');
const deleting = ref('');

const snackbar = ref({ show: false, msg: '', color: 'success' });

function showMsg(msg, color = 'success') {
    snackbar.value = { show: true, msg, color };
}

async function fetchThemes() {
    const res = await $backend('/themes');
    if (res.err === 'ok') {
        themes.value = res.themes;
    }
}

async function installTheme() {
    installing.value = true;
    try {
        const res = await $backend('/themes/install', {
            method: 'POST',
            body: JSON.stringify({ download_url: installUrl.value }),
            headers: { 'Content-Type': 'application/json' },
        });
        if (res.err === 'ok') {
            showMsg(res.msg || '安装成功');
            installUrl.value = '';
            await fetchThemes();
        } else {
            showMsg(res.msg || '安装失败', 'error');
        }
    } finally {
        installing.value = false;
    }
}

async function activateTheme(name) {
    activating.value = name;
    try {
        const res = await themeStore.activate(name);
        if (res.err === 'ok') {
            showMsg(res.msg || '已激活');
            await fetchThemes();
        } else {
            showMsg(res.msg || '激活失败', 'error');
        }
    } finally {
        activating.value = '';
    }
}

async function deactivateTheme() {
    activating.value = '__deactivate__';
    try {
        const res = await themeStore.deactivate();
        if (res.err === 'ok') {
            showMsg(res.msg || '已恢复默认主题');
            await fetchThemes();
        } else {
            showMsg(res.msg || '操作失败', 'error');
        }
    } finally {
        activating.value = '';
    }
}

async function deleteTheme(name) {
    if (!confirm(t('theme.deleteConfirm'))) return;
    deleting.value = name;
    try {
        const res = await $backend(`/themes/${encodeURIComponent(name)}`, { method: 'DELETE' });
        if (res.err === 'ok') {
            showMsg(res.msg || '已删除');
            if (themeStore.activeTheme?.name === name) {
                themeStore.activeTheme = null;
            }
            await fetchThemes();
        } else {
            showMsg(res.msg || '删除失败', 'error');
        }
    } finally {
        deleting.value = '';
    }
}

onMounted(fetchThemes);
</script>
