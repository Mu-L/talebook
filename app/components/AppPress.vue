<!-- 网站公告：紧接 appbar 下方的通栏，与 appbar 同宽，navbar 排在其下方不被遮挡 -->
<template>
    <v-app-bar
        v-if="show_press"
        class="app-press"
        :order="1"
        :height="barHeight"
        :elevation="0"
        color="transparent"
        :theme="store.theme"
    >
        <div
            ref="innerEl"
            class="app-press__inner"
        >
            <v-icon
                class="app-press__icon"
                size="20"
            >
                mdi-bullhorn-variant
            </v-icon>
            <div
                class="app-press__content press-content"
                v-html="press_message"
            />
            <v-btn
                class="app-press__close"
                icon
                variant="text"
                size="small"
                density="comfortable"
                @click="close"
            >
                <v-icon size="20">
                    mdi-close
                </v-icon>
            </v-btn>
        </div>
    </v-app-bar>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue';
import { useMainStore } from '@/stores/main';

const store = useMainStore();
const cookie = useCookie('close_press', { default: () => 'none' });

const has_press = computed(() => store.sys.header != undefined);
const press_message = computed(() => {
    if ( store.sys.header != undefined ) {
        return store.sys.header;
    }
    return '';
});

function hashCode(s) {
    var hash = 0, i, chr;
    if (s.length === 0) return hash;
    for (i = 0; i < s.length; i++) {
        chr   = s.charCodeAt(i);
        hash  = ((hash << 5) - hash) + chr;
        hash |= 0; // Convert to 32bit integer
    }
    return hash;
}

const show_press = computed(() => {
    if (!has_press.value) {
        return false;
    }
    var msg = press_message.value;
    var hash = hashCode(press_message.value);

    if ( msg == '' || hash == cookie.value ) {
        return false;
    }

    return true;
});

function close() {
    var hash = hashCode(press_message.value);
    cookie.value = hash;
}

// app-bar 高度固定，需随内容（可能多行）自适应，否则会裁切或错位
const innerEl = ref(null);
const barHeight = ref(48);
let ro = null;

function measure() {
    if (innerEl.value) {
        // 高度完全由内容决定，各主题可通过内边距/字号自定紧凑程度
        barHeight.value = Math.max(1, Math.ceil(innerEl.value.scrollHeight));
    }
}

watch(show_press, async (visible) => {
    if (visible && typeof ResizeObserver !== 'undefined') {
        await nextTick();
        measure();
        ro?.disconnect();
        ro = new ResizeObserver(measure);
        if (innerEl.value) ro.observe(innerEl.value);
    } else {
        ro?.disconnect();
        ro = null;
    }
}, { immediate: true });

onBeforeUnmount(() => {
    ro?.disconnect();
    ro = null;
});
</script>

<style scoped>
/* 默认主题：跟随 Vuetify 主题变量，自动适配明/暗 */
.app-press {
    --press-bg: rgb(var(--v-theme-surface));
    --press-fg: rgb(var(--v-theme-on-surface));
    --press-accent: rgb(var(--v-theme-primary));
    --press-border: rgba(var(--v-border-color), var(--v-border-opacity));

    background: var(--press-bg) !important;
    color: var(--press-fg) !important;
    border-bottom: 1px solid var(--press-border) !important;
}

/* 让内容撑满整条，去掉 toolbar 默认内边距 */
.app-press :deep(.v-toolbar__content) {
    padding: 0 !important;
    width: 100%;
}

.app-press__inner {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    padding: 8px 16px;
    box-sizing: border-box;
}

.app-press__icon {
    flex: 0 0 auto;
    color: var(--press-accent);
}

.app-press__content {
    flex: 1 1 auto;
    min-width: 0;
    font-size: 14px;
    line-height: 1.5;
    word-break: break-word;
}

.app-press__content :deep(a) {
    color: var(--press-accent);
}

.app-press__close {
    flex: 0 0 auto;
    color: var(--press-fg);
    opacity: 0.7;
}

.app-press__close:hover {
    opacity: 1;
}

/* 各内置主题：仅覆盖 4 个变量，与该主题的 appbar 融为一体 */
body.tb-current-builtin-theme-light-gray.tb-current-builtin-theme-mode-light .app-press {
    --press-bg: #f7f8f8;
    --press-fg: #2b2f33;
    --press-accent: #555c64;
    --press-border: #d0d3d6;
}
body.tb-current-builtin-theme-light-gray.tb-current-builtin-theme-mode-dark .app-press {
    --press-bg: #202326;
    --press-fg: #eceff1;
    --press-accent: #9aa0a8;
    --press-border: #33383d;
}

body.tb-current-builtin-theme-minimal.tb-current-builtin-theme-mode-light .app-press {
    --press-bg: #fff3df;
    --press-fg: #000000;
    --press-accent: #ff6600;
    --press-border: #e6e1c8;
}
body.tb-current-builtin-theme-minimal.tb-current-builtin-theme-mode-dark .app-press {
    --press-bg: #2b2d22;
    --press-fg: #d8d2b8;
    --press-accent: #ff8a2a;
    --press-border: #3b382a;
}
/* 极简主题：紧凑排版，与 28px 的 appbar 风格一致 */
body.tb-current-builtin-theme-minimal .app-press__inner {
    padding: 1px 6px;
    gap: 6px;
}
body.tb-current-builtin-theme-minimal .app-press__content {
    font-family: Verdana, Geneva, sans-serif;
    font-size: 11px;
    line-height: 1.35;
}
body.tb-current-builtin-theme-minimal .app-press__icon {
    font-size: 13px !important;
    width: 13px !important;
    height: 13px !important;
}
body.tb-current-builtin-theme-minimal .app-press__close {
    width: 18px !important;
    height: 18px !important;
}
body.tb-current-builtin-theme-minimal .app-press__close :deep(.v-icon) {
    font-size: 14px !important;
}

body.tb-current-builtin-theme-graphite.tb-current-builtin-theme-mode-light .app-press {
    --press-bg: #ffffff;
    --press-fg: #1b1f24;
    --press-accent: #3f6da3;
    --press-border: #dde2e8;
}
body.tb-current-builtin-theme-graphite.tb-current-builtin-theme-mode-dark .app-press {
    --press-bg: #191d21;
    --press-fg: #e7eaed;
    --press-accent: #6f9dd6;
    --press-border: #262b31;
}

body.tb-current-builtin-theme-brass.tb-current-builtin-theme-mode-light .app-press {
    --press-bg: #fbf9f4;
    --press-fg: #2a251d;
    --press-accent: #a9773a;
    --press-border: rgba(169, 119, 58, 0.5);
}
body.tb-current-builtin-theme-brass.tb-current-builtin-theme-mode-dark .app-press {
    --press-bg: #1f1c17;
    --press-fg: #ece7dd;
    --press-accent: #c99a5b;
    --press-border: rgba(201, 154, 91, 0.45);
}

body.tb-current-builtin-theme-warm-red.tb-current-builtin-theme-mode-light .app-press {
    --press-bg: #fbfaf6;
    --press-fg: #2a2622;
    --press-accent: #8f3a34;
    --press-border: #ddd8cc;
}
body.tb-current-builtin-theme-warm-red.tb-current-builtin-theme-mode-dark .app-press {
    --press-bg: #262019;
    --press-fg: #ece7dd;
    --press-accent: #e0938c;
    --press-border: #3a342b;
}
</style>
