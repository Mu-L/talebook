// @vitest-environment nuxt
import { ref } from 'vue';
import { mount } from '@vue/test-utils';
import { mockNuxtImport } from '@nuxt/test-utils/runtime';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';
import { describe, expect, it, vi } from 'vitest';

const { storeState, cookieRef } = vi.hoisted(() => ({
    storeState: { theme: 'light', sys: { header: '' as string | undefined } },
    cookieRef: { value: 'none' as string | number },
}));

vi.mock('@/stores/main', () => ({
    useMainStore: () => storeState,
}));

mockNuxtImport('useCookie', () => {
    return () => cookieRef;
});

const vuetify = createVuetify({ components, directives });
global.ResizeObserver = require('resize-observer-polyfill');

import AppPress from '@/components/AppPress.vue';

// v-app-bar 需要 Vuetify 布局上下文，故包一层 v-app
function mountPress() {
    return mount(
        { components: { AppPress }, template: '<v-app><AppPress /></v-app>' },
        { global: { plugins: [vuetify] } },
    );
}

describe('AppPress.vue', () => {
    it('renders the announcement when a header is present and not dismissed', () => {
        storeState.sys.header = '欢迎光临本站';
        cookieRef.value = 'none';

        const wrapper = mountPress();

        expect(wrapper.find('.app-press').exists()).toBe(true);
        expect(wrapper.html()).toContain('欢迎光临本站');
        wrapper.unmount();
    });

    it('hides the announcement when the current message was already dismissed', () => {
        storeState.sys.header = '欢迎光临本站';
        // hashCode('欢迎光临本站') 存入 cookie，模拟用户已关闭
        const wrapper = mountPress();
        (wrapper.findComponent(AppPress).vm as unknown as { close: () => void }).close();
        wrapper.unmount();

        const reopened = mountPress();
        expect(reopened.find('.app-press').exists()).toBe(false);
        reopened.unmount();
    });

    it('hides the announcement when no header is configured', () => {
        storeState.sys.header = undefined;
        cookieRef.value = 'none';

        const wrapper = mountPress();
        expect(wrapper.find('.app-press').exists()).toBe(false);
        wrapper.unmount();
    });
});
