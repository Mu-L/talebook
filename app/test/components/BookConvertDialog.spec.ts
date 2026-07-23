import { describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';

vi.mock('vue-i18n', () => ({
    useI18n: () => ({ t: (key: string) => key }),
}));

const vuetify = createVuetify({ components, directives });
global.ResizeObserver = require('resize-observer-polyfill');
(globalThis as Record<string, unknown>).visualViewport = {
    addEventListener: () => {},
    removeEventListener: () => {},
    width: 1024,
    height: 768,
    scale: 1,
    offsetLeft: 0,
    offsetTop: 0,
};

import BookConvertDialog from '@/components/BookConvertDialog.vue';

const availableOption = {
    source_format: 'txt',
    target_format: 'epub',
    converter: 'txt2epub',
    available: true,
    reason: null,
};

const mountDialog = (options = [availableOption]) => mount(BookConvertDialog, {
    global: {
        plugins: [vuetify],
        mocks: { $t: (key: string) => key },
    },
    props: {
        modelValue: true,
        bookTitle: 'Test Book',
        files: [{ format: 'TXT' }],
        options,
    },
    attachTo: document.body,
});

describe('BookConvertDialog.vue', () => {
    it('shows formats and emits the selected conversion route', async () => {
        const wrapper = mountDialog();
        await wrapper.vm.$nextTick();

        expect(document.body.textContent).toContain('TXT');
        expect(document.body.textContent).toContain('EPUB');
        expect(document.body.textContent).toContain('book.conversionReady');

        await wrapper.get('[data-testid="conversion-confirm"]').trigger('click');
        expect(wrapper.emitted('confirm')?.[0]?.[0]).toEqual(availableOption);
        wrapper.unmount();
    });

    it('explains why conversion is unavailable', async () => {
        const wrapper = mountDialog([{
            ...availableOption,
            available: false,
            reason: 'source_missing',
        }]);
        await wrapper.vm.$nextTick();

        expect(document.body.textContent).toContain('book.conversionSourceMissing');
        expect(document.body.textContent).toContain('book.noAvailableConversions');
        expect(wrapper.get('[data-testid="conversion-confirm"]').attributes('disabled')).toBeDefined();
        wrapper.unmount();
    });
});
