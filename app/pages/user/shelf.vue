<template>
    <div>
        <BookCoverGrid
            :books="books"
            :empty-text="t('shelf.empty')"
            key-prefix="shelf"
            sm="3"
            md="2"
            show-title
        />
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import BookCoverGrid from '@/components/BookCoverGrid.vue';
import { useMainStore } from '@/stores/main';
import { useI18n } from 'vue-i18n';

const { $backend } = useNuxtApp();
const mainStore = useMainStore();
const { t } = useI18n();

const books = ref([]);

useHead({
    title: () => t('shelf.pageTitle'),
});

onMounted(() => {
    mainStore.setNavbar(true);
    $backend('/shelf').then(rsp => {
        if (rsp.err === 'ok') {
            books.value = rsp.books || [];
        }
    });
});
</script>
