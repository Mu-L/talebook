<template>
    <div :class="['tb-theme-header', `tb-theme-${variant}`, modeClass, { 'tb-theme-rail': miniVariant }]">
        <v-app-bar
            class="tb-theme-appbar"
            density="compact"
            :elevation="isHackerNews ? 0 : 1"
        >
            <v-btn
                icon
                class="tb-theme-nav-toggle"
                @click.stop="toggleDrawer"
            >
                <v-avatar
                    v-if="isMybooks"
                    class="tb-theme-avatar-toggle"
                    size="34"
                    :image="store.user.is_login ? store.user.avatar : ''"
                >
                    <v-icon v-if="!store.user.avatar">
                        mdi-account-circle
                    </v-icon>
                </v-avatar>
                <v-icon v-else>
                    mdi-menu
                </v-icon>
            </v-btn>

            <button
                class="tb-theme-brand"
                type="button"
                @click="router.push('/')"
            >
                <span class="tb-theme-brand-mark">{{ brandMark }}</span>
                <span class="tb-theme-brand-title">{{ store.sys.title }}</span>
            </button>

            <v-spacer />

            <div
                v-if="display.smAndUp.value"
                class="tb-theme-search"
            >
                <form
                    v-if="isHackerNews"
                    class="tb-theme-hn-search"
                    @submit.prevent="doSearch"
                >
                    <input
                        v-model="search"
                        type="search"
                        :aria-label="t('common.search')"
                    >
                    <button type="submit">
                        {{ t('common.search') }}
                    </button>
                </form>
                <v-text-field
                    v-else
                    v-model="search"
                    class="tb-theme-search-field"
                    density="compact"
                    hide-details
                    :label="t('common.search')"
                    :prepend-inner-icon="isMybooks ? undefined : 'mdi-magnify'"
                    :variant="isMybooks ? 'solo-inverted' : 'solo'"
                    @keyup.enter="doSearch"
                >
                    <template
                        v-if="isMybooks"
                        #prepend-inner
                    >
                        <v-menu>
                            <template #activator="{ props: menuProps }">
                                <v-btn
                                    v-bind="menuProps"
                                    class="tb-theme-search-category"
                                    size="x-small"
                                    variant="text"
                                >
                                    {{ activeSearchCategoryLabel }}
                                </v-btn>
                            </template>
                            <v-list density="compact">
                                <v-list-item
                                    v-for="category in searchCategories"
                                    :key="category.value"
                                    :active="category.value === searchCategory"
                                    @click="searchCategory = category.value"
                                >
                                    <v-list-item-title>{{ category.label }}</v-list-item-title>
                                </v-list-item>
                            </v-list>
                        </v-menu>
                    </template>
                </v-text-field>
            </div>

            <v-btn
                v-if="!display.smAndUp.value"
                icon
                class="tb-theme-icon"
                @click="mobileSearch = !mobileSearch"
            >
                <v-icon>mdi-magnify</v-icon>
            </v-btn>
            <v-btn
                icon
                class="tb-theme-icon"
                @click="store.toggleTheme"
            >
                <v-icon>{{ store.theme === 'light' ? 'mdi-weather-night' : 'mdi-weather-sunny' }}</v-icon>
            </v-btn>
            <v-menu>
                <template #activator="{ props }">
                    <v-btn
                        v-bind="props"
                        icon
                        class="tb-theme-icon"
                    >
                        <v-icon>mdi-translate</v-icon>
                    </v-btn>
                </template>
                <v-list density="compact">
                    <v-list-item
                        v-for="localeItem in locales"
                        :key="localeItem.code"
                        :active="localeItem.code === locale"
                        @click="setLocale(localeItem.code)"
                    >
                        <template #prepend>
                            <v-icon>{{ localeItem.code === locale ? 'mdi-check' : 'mdi-translate' }}</v-icon>
                        </template>
                        <v-list-item-title>{{ localeItem.name }}</v-list-item-title>
                    </v-list-item>
                </v-list>
            </v-menu>
            <v-menu v-if="store.user.is_login">
                <template #activator="{ props }">
                    <v-btn
                        v-bind="props"
                        class="tb-theme-user"
                        variant="text"
                    >
                        <v-avatar
                            size="28"
                            :image="store.user.avatar"
                        />
                        <span v-if="display.mdAndUp.value">{{ store.user.nickname }}</span>
                    </v-btn>
                </template>
                <v-list density="compact">
                    <v-list-item
                        to="/user/detail"
                        :title="t('messages.userCenter')"
                        prepend-icon="mdi-account-box"
                    />
                    <v-list-item
                        to="/user/history"
                        :title="t('messages.readingHistory')"
                        prepend-icon="mdi-history"
                    />
                    <v-list-item
                        v-if="store.user.is_admin"
                        to="/admin/settings"
                        :title="t('messages.adminEntry')"
                        prepend-icon="mdi-console"
                    />
                    <v-divider />
                    <v-list-item
                        to="/logout"
                        :title="t('messages.logout')"
                        prepend-icon="mdi-exit-to-app"
                    />
                </v-list>
            </v-menu>
            <v-btn
                v-else
                class="tb-theme-login"
                to="/login"
                variant="flat"
            >
                {{ t('messages.pleaseLogin') }}
            </v-btn>

            <template
                v-if="mobileSearch"
                #extension
            >
                <v-form
                    class="tb-theme-mobile-search"
                    @submit.prevent="doSearch"
                >
                    <v-text-field
                        v-model="search"
                        density="compact"
                        hide-details
                        prepend-inner-icon="mdi-magnify"
                        :label="t('common.search')"
                        variant="solo"
                    />
                </v-form>
            </template>
        </v-app-bar>

        <v-navigation-drawer
            v-model="sidebar"
            class="tb-theme-drawer"
            :rail="isMybooks && miniVariant"
            :rail-width="64"
            :width="drawerWidth"
        >
            <v-list density="compact">
                <template
                    v-for="item in navItems"
                    :key="item.key"
                >
                    <v-list-subheader v-if="item.heading">
                        {{ item.heading }}
                    </v-list-subheader>
                    <v-list-group
                        v-else-if="item.groups"
                        :value="item.text"
                    >
                        <template #activator="{ props }">
                            <v-list-item
                                v-bind="props"
                                :prepend-icon="isHackerNews ? undefined : item.icon"
                                :title="item.text"
                            />
                        </template>
                        <v-list-item
                            v-for="link in item.groups"
                            :key="link.href"
                            :to="link.href"
                            :title="link.text"
                            :prepend-icon="isHackerNews ? undefined : link.icon"
                        />
                    </v-list-group>
                    <div
                        v-else-if="item.links"
                        class="tb-theme-link-grid"
                    >
                        <v-list-item
                            v-for="link in item.links"
                            :key="link.href || link.text"
                            :to="item.target ? undefined : link.href"
                            :href="item.target ? link.href : undefined"
                            :target="item.target"
                            :title="link.text"
                            :prepend-icon="isHackerNews ? undefined : link.icon"
                        />
                    </div>
                    <v-list-item
                        v-else
                        :to="item.href || undefined"
                        :title="item.text"
                        :prepend-icon="isHackerNews ? undefined : item.icon"
                    >
                        <template
                            v-if="item.count"
                            #append
                        >
                            <v-chip
                                size="x-small"
                                variant="outlined"
                            >
                                {{ item.count }}
                            </v-chip>
                        </template>
                    </v-list-item>
                </template>
            </v-list>
        </v-navigation-drawer>
    </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useDisplay } from 'vuetify';
import { useMainStore } from '@/stores/main';
import { useI18n } from '#i18n';

const props = defineProps({
    variant: {
        type: String,
        required: true,
        validator: value => ['cloudflare-radar', 'mybooks-midnight', 'hacker-news-compact'].includes(value),
    },
});

const store = useMainStore();
const router = useRouter();
const display = useDisplay();
const { locale, locales, setLocale, t } = useI18n();

const sidebar = ref(true);
const miniVariant = ref(false);
const mobileSearch = ref(false);
const search = ref('');
const searchCategory = ref('all');

const isMybooks = computed(() => props.variant === 'mybooks-midnight');
const isHackerNews = computed(() => props.variant === 'hacker-news-compact');
const modeClass = computed(() => `tb-theme-mode-${store.theme}`);
const drawerWidth = computed(() => {
    if (props.variant === 'cloudflare-radar') return 228;
    if (props.variant === 'mybooks-midnight') return 240;
    if (props.variant === 'hacker-news-compact') return 190;
    return 236;
});

const searchCategories = computed(() => [
    { value: 'all', label: t('common.search') },
    { value: 'title', label: t('book.title') },
    { value: 'author', label: t('book.author') },
    { value: 'isbn', label: 'ISBN' },
    { value: 'tag', label: t('navigation.tags') },
]);

const activeSearchCategoryLabel = computed(() => {
    return searchCategories.value.find(category => category.value === searchCategory.value)?.label || t('common.search');
});

const brandMark = computed(() => {
    return '书';
});

const navItems = computed(() => {
    const items = [
        { key: 'home', icon: 'mdi-home', href: '/', text: t('navigation.home') },
        { key: 'library', icon: 'mdi-book', href: '/library', text: t('navigation.localLibrary') },
        { key: 'network', icon: 'mdi-cloud-search', href: '/network', text: t('navigation.networkLibrary') },
    ];
    if (store.user.is_admin) {
        items.push({
            key: 'admin',
            icon: 'mdi-cog',
            text: t('navigation.admin'),
            groups: [
                { icon: 'mdi-cog', href: '/admin/settings', text: t('navigation.settings') },
                { icon: 'mdi-human-greeting', href: '/admin/users', text: t('navigation.users') },
                { icon: 'mdi-library-shelves', href: '/admin/books', text: t('navigation.books') },
                { icon: 'mdi-import', href: '/admin/imports', text: t('navigation.import') },
                { icon: 'mdi-book-cog', href: '/admin/booksources', text: t('navigation.bookSources') },
                { icon: 'mdi-palette', href: '/admin/themes', text: t('navigation.themes') },
                { icon: 'mdi-text-box-outline', href: '/admin/logs', text: t('navigation.systemLogs') },
            ],
        });
    }
    items.push(
        { key: 'categories', heading: t('navigation.categories') },
        { key: 'nav', icon: 'mdi-widgets', href: '/nav', text: t('navigation.browse'), count: store.sys.books },
        { key: 'publisher', icon: 'mdi-home-group', href: '/publisher', text: t('navigation.publishers'), count: store.sys.publishers },
        { key: 'author', icon: 'mdi-human-greeting', href: '/author', text: t('navigation.authors'), count: store.sys.authors },
        { key: 'tag', icon: 'mdi-tag-heart', href: '/tag', text: t('navigation.tags'), count: store.sys.tags },
        { key: 'format', icon: 'mdi-file', href: '/format', text: t('navigation.formats'), count: store.sys.formats },
        { key: 'series', icon: 'mdi-library-shelves', href: '/series', text: t('navigation.series'), count: store.sys.series },
        { key: 'rating', icon: 'mdi-star-half', href: '/rating', text: t('navigation.ratings') },
        { key: 'hot', icon: 'mdi-trending-up', href: '/hot', text: t('navigation.hot') },
        { key: 'recent', icon: 'mdi-history', href: '/recent', text: t('navigation.recent') },
    );
    if (store.sys.friends?.length > 0) {
        items.push(
            { key: 'friends', heading: t('messages.friendshipLinks') },
            {
                key: 'friend-links',
                target: '_blank',
                links: store.sys.friends.map(friend => ({
                    icon: 'mdi-open-in-new',
                    href: friend.href,
                    text: friend.text,
                })),
            },
        );
    }
    if (store.sys.show_sidebar_sys !== false) {
        items.push(
            { key: 'system', heading: t('messages.system') },
            { key: 'version', icon: 'mdi-history', href: '', text: t('messages.systemVersion'), count: store.sys.version },
            { key: 'users', icon: 'mdi-human', href: '', text: t('messages.userCount'), count: store.sys.users },
            { key: 'opds', icon: 'mdi-cellphone', href: '/opds-readme', text: t('messages.opdsIntroduction'), count: 'OPDS' },
        );
    }
    return items;
});

function toggleDrawer() {
    if (isMybooks.value && sidebar.value) {
        miniVariant.value = !miniVariant.value;
        return;
    }
    sidebar.value = !sidebar.value;
}

function doSearch() {
    let keyword = search.value.trim();
    if (!keyword) return;
    if (isMybooks.value && searchCategory.value !== 'all') {
        keyword = `${searchCategory.value}:${keyword.replace(/^(title:|author:|isbn:|tag:)/i, '').trim()}`;
    }
    router.push({ path: '/search', query: { keyword } });
}

let injectedStyle = null;
let stopBodyClassWatch = null;

const BODY_THEME_CLASS_PREFIX = 'tb-current-builtin-theme-';
const BODY_MODE_CLASS_PREFIX = 'tb-current-builtin-theme-mode-';

function injectThemeStyles() {
    injectedStyle?.remove();
    const style = document.createElement('style');
    style.setAttribute('data-talebook-theme', props.variant);
    style.textContent = themeCss[props.variant];
    document.head.appendChild(style);
    injectedStyle = style;
}

function clearThemeBodyClasses() {
    Array.from(document.body.classList).forEach((className) => {
        if (className.startsWith(BODY_THEME_CLASS_PREFIX) || className.startsWith(BODY_MODE_CLASS_PREFIX)) {
            document.body.classList.remove(className);
        }
    });
}

function syncThemeBodyClasses() {
    clearThemeBodyClasses();
    document.body.classList.add(`${BODY_THEME_CLASS_PREFIX}${props.variant}`);
    document.body.classList.add(`${BODY_MODE_CLASS_PREFIX}${store.theme}`);
}

onMounted(() => {
    injectThemeStyles();
    stopBodyClassWatch = watch(
        [() => props.variant, () => store.theme],
        syncThemeBodyClasses,
        { immediate: true },
    );
});

onUnmounted(() => {
    stopBodyClassWatch?.();
    clearThemeBodyClasses();
    injectedStyle?.remove();
});

const themeCss = {
    'cloudflare-radar': `
        .v-application { background: #f3f4f7 !important; color: #202124; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
        .v-main { background: #f3f4f7 !important; }
        .v-main .v-container { padding: 20px 24px !important; }
        .v-main .v-row { margin: -10px !important; }
        .v-main .v-col { padding: 10px !important; }
        .v-main .v-card { background: #fff !important; border: 1px solid #d8e0ea !important; box-shadow: 0 1px 2px rgba(15,23,42,.05) !important; border-radius: 8px !important; }
        .v-main .v-card-title { color: #202124; font-size: 17px !important; font-weight: 700; letter-spacing: 0; padding: 18px 20px 10px !important; }
        .v-main .v-card-subtitle { color: #6b7280 !important; padding-inline: 20px !important; }
        .v-main .v-card-text { color: #2f3b4a; padding: 14px 20px 20px !important; }
        .v-main .v-btn { border-radius: 6px !important; text-transform: none !important; }
        .v-main .v-btn.bg-primary { background: #1d4ed8 !important; color: #fff !important; }
        .v-main .v-btn.v-btn--variant-tonal { background: #eaf2ff !important; color: #0f56c9 !important; }
        .v-main .v-btn.v-btn--variant-outlined { border-color: #93c5fd !important; color: #0f56c9 !important; }
        .v-main .v-btn.v-btn--variant-text { color: #0f56c9 !important; }
        .v-main .v-btn.v-btn--disabled { color: #94a3b8 !important; opacity: .72; }
        .v-main .v-btn.text-primary, .v-main .text-primary { color: #0f56c9 !important; }
        .v-main .v-field { border-radius: 7px !important; }
        .v-main .v-table { border: 1px solid #d8e0ea !important; border-radius: 8px !important; }
        .v-main .v-chip { border-radius: 5px !important; }
        .v-main .v-chip.text-primary,
        .v-main .v-chip.v-chip--variant-tonal { background: #dbeafe !important; color: #0f56c9 !important; }
        .v-main a { color: #0f56c9 !important; }
        .upload-btn { background: #1d4ed8 !important; color: #fff !important; box-shadow: 0 10px 24px rgba(29,78,216,.28) !important; }
        * { scrollbar-width: thin; scrollbar-color: #94a3b8 #f8fafc; }
        ::-webkit-scrollbar { height: 10px; width: 10px; }
        ::-webkit-scrollbar-track { background: #f8fafc; }
        ::-webkit-scrollbar-thumb { background: #94a3b8; border: 2px solid #f8fafc; border-radius: 999px; }
        .tb-theme-cloudflare-radar .tb-theme-appbar { background: rgba(255,255,255,.98) !important; color: #202124 !important; border-bottom: 1px solid #d8e0ea; box-shadow: 0 1px 2px rgba(15,23,42,.04) !important; }
        .tb-theme-cloudflare-radar .tb-theme-drawer { background: #ffffff !important; border-right: 1px solid #d8e0ea; }
        .tb-theme-cloudflare-radar .tb-theme-brand-mark { background: #1d4ed8; color: #fff; }
        .tb-theme-cloudflare-radar .tb-theme-brand-title { color: #202124; }
        .tb-theme-cloudflare-radar .tb-theme-search-field .v-field { background: #f8fafc !important; border: 1px solid #d8e0ea; box-shadow: none !important; color: #202124 !important; }
        .tb-theme-cloudflare-radar .tb-theme-search-field .v-field__input { color: #202124 !important; min-height: 34px !important; padding-bottom: 4px !important; padding-top: 4px !important; }
        .tb-theme-cloudflare-radar .tb-theme-search-field .v-field__input::placeholder { color: #64748b !important; opacity: 1; }
        .tb-theme-cloudflare-radar .tb-theme-search-field .v-label { color: #64748b !important; opacity: 1; }
        .tb-theme-cloudflare-radar .tb-theme-search-field .v-icon { color: #64748b !important; opacity: 1; }
        .tb-theme-cloudflare-radar .v-list { padding: 12px 0 !important; }
        .tb-theme-cloudflare-radar .v-list-item { border-radius: 0 !important; min-height: 44px !important; padding-inline: 18px 14px !important; }
        .tb-theme-cloudflare-radar .v-list-item-title { color: #183b71 !important; font-size: 14px !important; font-weight: 600; letter-spacing: 0; }
        .tb-theme-cloudflare-radar .v-list-item--active { background: #eaf2ff !important; color: #0f56c9 !important; }
        .tb-theme-cloudflare-radar .v-list-item--active .v-list-item-title { color: #0f56c9 !important; }
        .tb-theme-cloudflare-radar .v-list-item__prepend { width: 34px !important; }
        .tb-theme-cloudflare-radar .v-list-item__prepend > .v-icon { color: #1d4ed8; font-size: 22px !important; margin-inline-end: 12px !important; }
        .tb-theme-cloudflare-radar .v-list-group__items .v-list-item { padding-inline-start: 28px !important; }
        .tb-theme-cloudflare-radar .v-list-group__items .v-list-item__prepend { width: 32px !important; }
        .tb-theme-cloudflare-radar .v-list-item__append { color: #5f6b7a; }
        .tb-theme-cloudflare-radar .v-list-subheader { color: #6b7280 !important; font-size: 11px !important; font-weight: 700; letter-spacing: .08em; min-height: 28px !important; padding-inline: 18px !important; text-transform: uppercase; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-application { background: #0b1220 !important; color: #dbeafe; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-main { background: #0b1220 !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-main .v-card { background: #111a2e !important; border-color: #243756 !important; box-shadow: 0 1px 2px rgba(0,0,0,.34) !important; color: #dbeafe !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-main .v-card-title { color: #eff6ff !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-main .v-card-text { color: #cbd5e1 !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-main .text-medium-emphasis { color: #94a3b8 !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-main .v-field { background: #0f172a !important; color: #e2e8f0 !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-main .v-btn.bg-primary { background: #2563eb !important; color: #eff6ff !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-main .v-btn.v-btn--variant-tonal { background: #172554 !important; color: #bfdbfe !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-main .v-btn.v-btn--variant-outlined { border-color: #3b82f6 !important; color: #93c5fd !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-main .v-btn.v-btn--variant-text,
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-main .text-primary,
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-main a { color: #93c5fd !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-main .v-chip.text-primary,
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .v-main .v-chip.v-chip--variant-tonal { background: #172554 !important; color: #bfdbfe !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .upload-btn { background: #2563eb !important; color: #eff6ff !important; box-shadow: 0 10px 24px rgba(37,99,235,.32) !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .tb-theme-cloudflare-radar .tb-theme-appbar { background: rgba(15,23,42,.98) !important; color: #e2e8f0 !important; border-bottom-color: #243756; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .tb-theme-cloudflare-radar .tb-theme-drawer { background: #0f172a !important; border-right-color: #243756; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .tb-theme-cloudflare-radar .tb-theme-brand-title { color: #eff6ff; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .tb-theme-cloudflare-radar .tb-theme-search-field .v-field { background: #111827 !important; border-color: #334155; color: #e2e8f0 !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .tb-theme-cloudflare-radar .tb-theme-search-field .v-field__input { color: #e2e8f0 !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .tb-theme-cloudflare-radar .tb-theme-search-field .v-label,
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .tb-theme-cloudflare-radar .tb-theme-search-field .v-icon { color: #93c5fd !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .tb-theme-cloudflare-radar .v-list-item-title { color: #bfdbfe !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .tb-theme-cloudflare-radar .v-list-item--active { background: #172554 !important; color: #93c5fd !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .tb-theme-cloudflare-radar .v-list-item--active .v-list-item-title { color: #bfdbfe !important; }
        body.tb-current-builtin-theme-cloudflare-radar.tb-current-builtin-theme-mode-dark .tb-theme-cloudflare-radar .v-list-subheader { color: #7dd3fc !important; }
    `,
    'mybooks-midnight': `
        .v-application { background: #111315 !important; color: #e8eaed; font-family: Poppins, Roboto, "Noto Sans SC", system-ui, sans-serif; }
        .v-main { background: #111315 !important; }
        .v-main .v-container { padding: 18px !important; }
        .v-main .v-card { background: #1b1d20 !important; color: #e8eaed !important; border: 1px solid #34383d !important; box-shadow: 0 12px 30px rgba(0,0,0,.28) !important; border-radius: 8px !important; }
        .v-main .text-medium-emphasis { color: #a1a7ae !important; }
        .v-main .v-btn { border-radius: 7px !important; text-transform: none !important; }
        .v-main .v-btn.bg-primary { background: #747b84 !important; color: #fff !important; }
        .v-main .v-btn.v-btn--variant-tonal { background: #2f3338 !important; color: #eceff1 !important; }
        .v-main .v-btn.v-btn--variant-outlined { border-color: #555b63 !important; color: #c4c8ce !important; }
        .v-main .v-btn.v-btn--variant-text { color: #c4c8ce !important; }
        .v-main .v-btn.v-btn--disabled { color: #737a82 !important; opacity: .7; }
        .v-main .text-primary,
        .v-main a { color: #c4c8ce !important; }
        .v-main .v-field { border-radius: 7px !important; }
        .v-main .v-chip.text-primary,
        .v-main .v-chip.v-chip--variant-tonal { background: #2f3338 !important; color: #e5e7eb !important; }
        .upload-btn { background: #747b84 !important; color: #fff !important; box-shadow: 0 10px 24px rgba(0,0,0,.28) !important; }
        .tb-theme-mybooks-midnight .tb-theme-appbar { background: #202326 !important; color: #eceff1 !important; border-bottom: 1px solid #33383d; box-shadow: 0 1px 0 rgba(255,255,255,.03) inset !important; }
        .tb-theme-mybooks-midnight .tb-theme-drawer { background: #17191c !important; color: #d7dadd !important; border-right: 1px solid #30343a; }
        .tb-theme-mybooks-midnight .tb-theme-brand-mark { background: #747b84; color: #fff; box-shadow: none; }
        .tb-theme-mybooks-midnight .tb-theme-brand-title { color: #eceff1; }
        .tb-theme-mybooks-midnight .tb-theme-icon,
        .tb-theme-mybooks-midnight .tb-theme-nav-toggle { color: #d2d6da !important; }
        .tb-theme-mybooks-midnight .tb-theme-search-field .v-field { background: #2b2f33 !important; color: #f3f4f6 !important; border: 1px solid #444a50; box-shadow: none !important; }
        .tb-theme-mybooks-midnight .tb-theme-search-field .v-field__input { color: #f3f4f6 !important; }
        .tb-theme-mybooks-midnight .tb-theme-search-category { color: #e5e7eb !important; margin-right: 6px; }
        .tb-theme-mybooks-midnight .v-list { padding-top: 6px !important; }
        .tb-theme-mybooks-midnight .v-list-item { min-height: 34px !important; padding-inline: 10px !important; }
        .tb-theme-mybooks-midnight .v-list-item__prepend { width: 30px !important; }
        .tb-theme-mybooks-midnight .v-list-item__prepend > .v-icon { color: #aeb4bc; font-size: 20px !important; margin-inline-end: 10px !important; }
        .tb-theme-mybooks-midnight .v-list-group__items .v-list-item { padding-inline-start: 22px !important; }
        .tb-theme-mybooks-midnight .v-list-group__items .v-list-item__prepend { width: 28px !important; }
        .tb-theme-mybooks-midnight .v-list-item-title { font-size: 13px !important; font-weight: 500; }
        .tb-theme-mybooks-midnight .v-list-item--active { color: #fff; background: #2f3338; }
        .tb-theme-mybooks-midnight .v-list-subheader { color: #8f969e !important; font-size: 11px !important; font-weight: 700; letter-spacing: .06em; }
        .tb-theme-mybooks-midnight * { scrollbar-width: thin; scrollbar-color: #555b63 #17191c; }
        .tb-theme-mybooks-midnight ::-webkit-scrollbar { width: 8px; height: 8px; }
        .tb-theme-mybooks-midnight ::-webkit-scrollbar-thumb { background: #555b63; border-radius: 6px; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .v-application { background: #f2f3f3 !important; color: #2b2f33; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .v-main { background: #f2f3f3 !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .v-main .v-card { background: #ffffff !important; color: #2b2f33 !important; border-color: #d7dadd !important; box-shadow: 0 8px 22px rgba(39,43,48,.08) !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .v-main .text-medium-emphasis { color: #697079 !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .v-main .v-btn.bg-primary { background: #555c64 !important; color: #fff !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .v-main .v-btn.v-btn--variant-tonal { background: #e2e5e8 !important; color: #34383d !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .v-main .v-btn.v-btn--variant-outlined { border-color: #b9bec4 !important; color: #41474e !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .v-main .v-btn.v-btn--variant-text,
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .v-main .text-primary,
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .v-main a { color: #41474e !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .v-main .v-chip.text-primary,
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .v-main .v-chip.v-chip--variant-tonal { background: #e6e8ea !important; color: #34383d !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .upload-btn { background: #555c64 !important; color: #fff !important; box-shadow: 0 10px 22px rgba(85,92,100,.22) !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .tb-theme-appbar { background: #f7f8f8 !important; color: #2b2f33 !important; border-bottom-color: #d0d3d6; box-shadow: 0 1px 8px rgba(39,43,48,.06) !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .tb-theme-drawer { background: #eceeef !important; color: #34383d !important; border-right-color: #d0d3d6; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .tb-theme-brand-mark { background: #555c64; color: #fff; box-shadow: none; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .tb-theme-brand-title { color: #24282d; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .tb-theme-icon,
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .tb-theme-nav-toggle { color: #555c64 !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .tb-theme-search-field .v-field { background: #ffffff !important; border: 1px solid #cfd3d7; color: #2b2f33 !important; box-shadow: 0 1px 2px rgba(39,43,48,.04) !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .tb-theme-search-field .v-field__input { color: #2b2f33 !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .tb-theme-search-field .v-label,
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .tb-theme-search-field .v-icon { color: #697079 !important; opacity: 1; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .tb-theme-search-category { color: #555c64 !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .v-list-item-title { color: #34383d !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .v-list-item__prepend > .v-icon { color: #6f757d; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .v-list-item--active { background: #dfe2e5 !important; color: #2b2f33 !important; }
        body.tb-current-builtin-theme-mybooks-midnight.tb-current-builtin-theme-mode-light .tb-theme-mybooks-midnight .v-list-subheader { color: #737a82 !important; }
    `,
    'hacker-news-compact': `
        .v-application { background: #f6f6ef !important; color: #000; font-family: Verdana, Geneva, sans-serif; font-size: 12px; }
        .v-main { background: #f6f6ef !important; }
        .v-main .v-container { padding: 4px 6px !important; }
        .v-main .v-card { background: #f6f6ef !important; color: #000 !important; border: 0 !important; border-radius: 0 !important; box-shadow: none !important; }
        .v-main .v-card-title { font-size: 13px !important; line-height: 18px !important; padding: 4px 6px !important; }
        .v-main .v-card-text { font-size: 12px !important; line-height: 16px !important; padding: 4px 6px !important; }
        .v-main .v-row { margin: 0 !important; }
        .v-main .v-col { padding: 3px !important; }
        .v-main .v-btn { border-radius: 0 !important; font-family: Verdana, Geneva, sans-serif !important; font-size: 11px !important; min-height: 22px !important; padding: 0 5px !important; text-transform: none !important; }
        .v-main .v-btn.bg-primary { background: #ff6600 !important; color: #000 !important; }
        .v-main .v-btn.v-btn--variant-tonal { background: #fff3df !important; color: #000 !important; }
        .v-main .v-btn.v-btn--variant-outlined { border-color: #ff6600 !important; color: #ff6600 !important; }
        .v-main .v-btn.v-btn--variant-text,
        .v-main .text-primary,
        .v-main a { color: #ff6600 !important; }
        .v-main .v-btn.v-btn--disabled { color: #828282 !important; opacity: .75; }
        .v-main .v-chip { border-radius: 0 !important; font-size: 10px !important; height: 18px !important; padding-inline: 4px !important; }
        .v-main .v-chip.text-primary,
        .v-main .v-chip.v-chip--variant-tonal { background: #fff3df !important; color: #ff6600 !important; }
        .v-main .v-field { border-radius: 0 !important; font-size: 12px !important; min-height: 28px !important; }
        .upload-btn { background: #ff6600 !important; color: #000 !important; box-shadow: none !important; }
        .tb-theme-hacker-news-compact .tb-theme-appbar { background: #ff6600 !important; color: #000 !important; min-height: 28px !important; }
        .tb-theme-hacker-news-compact .tb-theme-drawer { background: #f6f6ef !important; color: #000 !important; border-right: 1px solid #e6e1c8; font-size: 11px; }
        .tb-theme-hacker-news-compact .tb-theme-brand-mark { background: #fff; border: 1px solid #fff; border-radius: 0; color: #ff6600; height: 18px; width: 18px; }
        .tb-theme-hacker-news-compact .tb-theme-brand-title { color: #000; font-size: 13px; font-weight: 700; }
        .tb-theme-hacker-news-compact .v-list { background: #f6f6ef !important; padding: 2px 0 !important; }
        .tb-theme-hacker-news-compact .v-list-item { min-height: 20px !important; padding: 0 5px !important; }
        .tb-theme-hacker-news-compact .v-list-item__content { align-self: center !important; }
        .tb-theme-hacker-news-compact .v-list-item-title { color: #000 !important; font-family: Verdana, Geneva, sans-serif !important; font-size: 11px !important; line-height: 16px !important; }
        .tb-theme-hacker-news-compact .v-list-item__prepend { display: none !important; }
        .tb-theme-hacker-news-compact .v-list-group__items .v-list-item { padding-inline-start: 14px !important; }
        .tb-theme-hacker-news-compact .v-list-item__append { margin-left: 3px !important; }
        .tb-theme-hacker-news-compact .v-list-item--active { background: #fff3df !important; color: #000 !important; }
        .tb-theme-hacker-news-compact .v-list-subheader { color: #828282 !important; font-family: Verdana, Geneva, sans-serif !important; font-size: 10px !important; font-weight: 400 !important; min-height: 18px !important; padding: 0 5px !important; text-transform: lowercase; }
        .tb-theme-hacker-news-compact .v-chip { border: 0 !important; color: #828282 !important; font-size: 10px !important; height: 14px !important; padding: 0 !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .v-application { background: #1f2118 !important; color: #d8d2b8; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .v-main { background: #1f2118 !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .v-main .v-card { background: #1f2118 !important; color: #d8d2b8 !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .v-main .v-card-title,
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .v-main .v-card-text { color: #d8d2b8 !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .v-main .text-medium-emphasis { color: #9c967d !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .v-main .v-btn.bg-primary { background: #d35400 !important; color: #111 !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .v-main .v-btn.v-btn--variant-tonal { background: #3a2a18 !important; color: #ffd0a3 !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .v-main .v-btn.v-btn--variant-outlined { border-color: #ff8a2a !important; color: #ff8a2a !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .v-main .v-btn.v-btn--variant-text,
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .v-main .text-primary,
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .v-main a { color: #ff8a2a !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .v-main .v-chip.text-primary,
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .v-main .v-chip.v-chip--variant-tonal { background: #3a2a18 !important; color: #ffd0a3 !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .upload-btn { background: #d35400 !important; color: #111 !important; box-shadow: none !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .tb-theme-hacker-news-compact .tb-theme-appbar { background: #d35400 !important; color: #111 !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .tb-theme-hacker-news-compact .tb-theme-drawer { background: #181a13 !important; color: #d8d2b8 !important; border-right-color: #3b382a; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .tb-theme-hacker-news-compact .tb-theme-brand-mark { background: #1f2118; border-color: #1f2118; color: #ff8a2a; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .tb-theme-hacker-news-compact .tb-theme-brand-title { color: #111; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .tb-theme-hacker-news-compact .v-list { background: #181a13 !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .tb-theme-hacker-news-compact .v-list-item-title { color: #d8d2b8 !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .tb-theme-hacker-news-compact .v-list-item--active { background: #3a2a18 !important; color: #ffd0a3 !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .tb-theme-hacker-news-compact .v-list-subheader,
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .tb-theme-hacker-news-compact .v-chip { color: #9c967d !important; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .tb-theme-hn-search input { background: #2b2d22; border-color: #8b7b56; color: #f4ecd1; }
        body.tb-current-builtin-theme-hacker-news-compact.tb-current-builtin-theme-mode-dark .tb-theme-hn-search button { background: #181a13; border-color: #8b7b56; color: #f4ecd1; }
    `,
};
</script>

<style scoped>
.tb-theme-brand {
    align-items: center;
    background: transparent;
    border: 0;
    cursor: pointer;
    display: inline-flex;
    gap: 8px;
    min-width: 0;
    padding: 0 10px 0 2px;
}

.tb-theme-brand-mark {
    align-items: center;
    border-radius: 5px;
    display: inline-flex;
    font-size: 12px;
    font-weight: 800;
    height: 24px;
    justify-content: center;
    width: 24px;
}

.tb-theme-brand-title {
    font-size: 15px;
    font-weight: 700;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.tb-theme-search {
    flex: 0 1 560px;
    margin-left: auto;
    margin-right: 12px;
    max-width: 560px;
    min-width: 240px;
    width: 40vw;
}

.tb-theme-nav-toggle,
.tb-theme-icon {
    flex: 0 0 auto;
}

.tb-theme-user {
    display: inline-flex;
    gap: 6px;
    min-width: 0;
    padding-inline: 6px;
}

.tb-theme-login {
    margin-right: 8px;
}

.tb-theme-mobile-search {
    padding: 8px 12px;
    width: 100%;
}

.tb-theme-hn-search {
    align-items: center;
    display: flex;
    gap: 3px;
}

.tb-theme-hn-search input {
    background: #fff;
    border: 1px solid #000;
    border-radius: 0;
    color: #000;
    font-family: Verdana, Geneva, sans-serif;
    font-size: 11px;
    height: 19px;
    max-width: 220px;
    padding: 1px 3px;
    width: 24vw;
}

.tb-theme-hn-search button {
    background: #f6f6ef;
    border: 1px solid #000;
    border-radius: 0;
    color: #000;
    font-family: Verdana, Geneva, sans-serif;
    font-size: 11px;
    height: 19px;
    line-height: 16px;
    padding: 0 5px;
}

.tb-theme-hacker-news-compact :deep(.v-toolbar__content) {
    height: 28px !important;
    padding-inline: 2px !important;
}

.tb-theme-hacker-news-compact .tb-theme-brand,
.tb-theme-hacker-news-compact .tb-theme-icon,
.tb-theme-hacker-news-compact .tb-theme-nav-toggle {
    height: 24px !important;
    min-height: 24px !important;
    width: 24px;
}

.tb-theme-hacker-news-compact .tb-theme-brand {
    width: auto;
}

.tb-theme-hacker-news-compact :deep(.v-btn__content .v-icon) {
    font-size: 16px;
}

.tb-theme-mybooks-midnight :deep(.v-toolbar__content) {
    min-height: 48px;
}

.tb-theme-mybooks-midnight.tb-theme-rail :deep(.v-list-subheader),
.tb-theme-mybooks-midnight.tb-theme-rail :deep(.v-list-item-title),
.tb-theme-mybooks-midnight.tb-theme-rail :deep(.v-list-item__append),
.tb-theme-mybooks-midnight.tb-theme-rail :deep(.v-list-group__items) {
    display: none !important;
}

.tb-theme-mybooks-midnight.tb-theme-rail :deep(.v-list-item) {
    justify-content: center;
    padding-inline: 0 !important;
}

.tb-theme-mybooks-midnight.tb-theme-rail :deep(.v-list-item__prepend) {
    justify-content: center;
    width: 64px !important;
}

.tb-theme-mybooks-midnight.tb-theme-rail :deep(.v-list-item__prepend > .v-icon) {
    margin-inline-end: 0 !important;
}
</style>
