// @vitest-environment nuxt
import { mount } from '@vue/test-utils';
import { mockNuxtImport } from '@nuxt/test-utils/runtime';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';
import { describe, expect, it, vi } from 'vitest';

vi.mock('vue-i18n', () => ({
    useI18n: () => ({ t: (key: string) => key }),
}));

const { alertMock, backendMock, pushMock } = vi.hoisted(() => ({
    alertMock: vi.fn(),
    backendMock: vi.fn(),
    pushMock: vi.fn(),
}));

mockNuxtImport('useNuxtApp', () => {
    return () => ({ $backend: backendMock, $alert: alertMock });
});

mockNuxtImport('useRouter', () => {
    return () => ({ push: pushMock });
});

const vuetify = createVuetify({ components, directives });
global.ResizeObserver = require('resize-observer-polyfill');

import Upload from '@/components/Upload.vue';

type UploadVm = {
    do_upload: () => void;
};

function mountUpload() {
    alertMock.mockReset();
    backendMock.mockReset();
    pushMock.mockReset();
    return mount(Upload, {
        global: {
            plugins: [vuetify],
            mocks: { $t: (key: string) => key },
        },
    });
}

describe('Upload.vue', () => {
    it('does not post an empty upload when no ebook is selected', () => {
        const wrapper = mountUpload();

        (wrapper.vm as unknown as UploadVm).do_upload();

        expect(backendMock).not.toHaveBeenCalled();
        expect(alertMock).toHaveBeenCalledWith('error', 'messages.selectFileToUpload');
        wrapper.unmount();
    });
});
