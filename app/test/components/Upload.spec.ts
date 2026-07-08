// @vitest-environment nuxt
import { flushPromises, mount } from '@vue/test-utils';
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
    ebooks: File | null;
};

function makeFakeFile(name: string, size: number): File {
    const file = new File([new Blob([''])], name);
    Object.defineProperty(file, 'size', { value: size });
    // avoid allocating `size` real bytes in tests; chunk contents are irrelevant since $backend is mocked
    file.slice = () => new Blob(['x']);
    return file;
}

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

    it('uploads small files directly without chunking', async () => {
        const wrapper = mountUpload();
        backendMock.mockResolvedValue({ err: 'ok', book_id: 42 });

        (wrapper.vm as unknown as UploadVm).ebooks = makeFakeFile('small.epub', 1024);
        (wrapper.vm as unknown as UploadVm).do_upload();
        await flushPromises();

        expect(backendMock).toHaveBeenCalledTimes(1);
        expect(backendMock).toHaveBeenCalledWith('/book/upload', expect.objectContaining({ method: 'POST' }));
        expect(pushMock).toHaveBeenCalledWith('/book/42');
        wrapper.unmount();
    });

    it('uploads large files in chunks and completes the upload', async () => {
        const wrapper = mountUpload();
        backendMock.mockImplementation((url: string) => {
            if (url === '/book/upload/chunk') {
                return Promise.resolve({ err: 'ok' });
            }
            if (url === '/book/upload/complete') {
                return Promise.resolve({ err: 'ok', book_id: 77 });
            }
            return Promise.reject(new Error('unexpected url: ' + url));
        });

        // 9MB file with a 4MB chunk size should be split into 3 chunks
        (wrapper.vm as unknown as UploadVm).ebooks = makeFakeFile('big.epub', 9 * 1024 * 1024);
        (wrapper.vm as unknown as UploadVm).do_upload();
        await flushPromises();

        const chunkCalls = backendMock.mock.calls.filter(([url]) => url === '/book/upload/chunk');
        const completeCalls = backendMock.mock.calls.filter(([url]) => url === '/book/upload/complete');
        expect(chunkCalls.length).toBe(3);
        expect(completeCalls.length).toBe(1);
        expect(pushMock).toHaveBeenCalledWith('/book/77');
        wrapper.unmount();
    });

    it('surfaces the backend error when a chunk upload fails', async () => {
        const wrapper = mountUpload();
        backendMock.mockResolvedValue({ err: 'params.chunk', msg: 'chunk too large' });

        (wrapper.vm as unknown as UploadVm).ebooks = makeFakeFile('big.epub', 9 * 1024 * 1024);
        (wrapper.vm as unknown as UploadVm).do_upload();
        await flushPromises();

        expect(alertMock).toHaveBeenCalledWith('error', 'chunk too large');
        wrapper.unmount();
    });
});
