<template>
    <div>
        <v-btn
            class="upload-btn"
            color="pink"
            icon="mdi-upload"
            size="large"
            elevation="4"
            @click="dialog = !dialog"
        />
        <v-dialog
            v-model="dialog"
            persistent
            transition="dialog-bottom-transition"
            width="300"
        >
            <v-card>
                <v-toolbar
                    flat
                    density="compact"
                    color="primary"
                >
                    <v-toolbar-title>{{ $t('messages.uploadBooks') }}</v-toolbar-title>
                    <v-spacer />
                    <v-btn
                        variant="text"
                        @click="dialog = false"
                    >
                        {{ $t('messages.dialogClose') }}
                    </v-btn>
                </v-toolbar>
                <v-card-text>
                    <p>{{ $t('messages.uploadNotice') }}</p>
                    <v-form
                        ref="form"
                        @submit.prevent="do_upload"
                    >
                        <v-file-input
                            v-model="ebooks"
                            :label="$t('messages.selectEbook')"
                        />
                    </v-form>
                    <v-progress-linear
                        v-if="loading && progress > 0"
                        :model-value="progress"
                        color="primary"
                        height="18"
                    >
                        <template #default>
                            {{ $t('messages.uploadProgress', { percent: progress }) }}
                        </template>
                    </v-progress-linear>
                </v-card-text>
                <v-card-actions>
                    <v-spacer />
                    <v-btn
                        :loading="loading"
                        color="primary"
                        @click="do_upload"
                    >
                        {{ $t('actions.upload') }}
                    </v-btn>
                    <v-spacer />
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';

const { $backend, $alert } = useNuxtApp();
const { t } = useI18n();
const router = useRouter();

const loading = ref(false);
const dialog = ref(false);
const ebooks = ref(null);
const progress = ref(0);

// 单个分片大小，需小于反代（如 Cloudflare 免费版）100MB 的单请求体积限制
const CHUNK_SIZE = 4 * 1024 * 1024;
// 超过该大小的文件才走分片上传，避免小文件多一次网络往返
const CHUNK_THRESHOLD = 8 * 1024 * 1024;

function generateUploadId() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID().replace(/-/g, '');
    }
    return Date.now().toString(36) + Math.random().toString(36).slice(2);
}

function uploadWhole(file) {
    const data = new FormData();
    data.append('ebook', file, encodeURIComponent(file.name || 'upload.bin'));
    return $backend('/book/upload', {
        method: 'POST',
        body: data,
    });
}

async function uploadInChunks(file) {
    const uploadId = generateUploadId();
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

    for (let index = 0; index < totalChunks; index++) {
        const start = index * CHUNK_SIZE;
        const chunk = file.slice(start, Math.min(start + CHUNK_SIZE, file.size));
        const data = new FormData();
        data.append('chunk', chunk);
        data.append('upload_id', uploadId);
        data.append('chunk_index', index);
        data.append('total_chunks', totalChunks);

        const rsp = await $backend('/book/upload/chunk', {
            method: 'POST',
            body: data,
        });
        if (rsp.err !== 'ok') {
            return rsp;
        }
        progress.value = Math.round(((index + 1) / totalChunks) * 100);
    }

    const data = new FormData();
    data.append('upload_id', uploadId);
    data.append('filename', encodeURIComponent(file.name || 'upload.bin'));
    data.append('total_chunks', totalChunks);
    return $backend('/book/upload/complete', {
        method: 'POST',
        body: data,
    });
}

function do_upload() {
    let file = null;
    if (ebooks.value) {
        file = Array.isArray(ebooks.value) ? ebooks.value[0] : ebooks.value;
    }

    if (!file) {
        $alert('error', t('messages.selectFileToUpload'));
        return;
    }

    loading.value = true;
    progress.value = 0;
    const uploadPromise = file.size > CHUNK_THRESHOLD ? uploadInChunks(file) : uploadWhole(file);

    uploadPromise
        .then(rsp => {
            dialog.value = false;
            if (rsp.err === 'ok') {
                $alert('success', t('messages.uploadSuccess'), '/book/' + rsp.book_id);
                router.push('/book/' + rsp.book_id);
            } else if (rsp.err === 'samebook') {
                $alert('error', rsp.msg, '/book/' + rsp.book_id);
                router.push('/book/' + rsp.book_id);
            } else {
                $alert('error', rsp.msg);
            }
        })
        .catch(() => {
            // $backend 已在网络/HTTP异常场景下弹出提示，这里仅需终止流程
        })
        .finally(() => {
            loading.value = false;
            progress.value = 0;
        });
}
</script>

<style scoped>
.upload-btn {
    position: fixed;
    bottom: 16px;
    right: 16px;
    z-index: 100;
}
</style>
