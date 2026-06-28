<template>
    <div>
        <div v-if="books.length === 0" class="text-center py-8 text-grey">
            {{ t('shelf.empty') }}
        </div>
        <v-row v-else>
            <v-col
                v-for="book in books"
                :key="'shelf-' + book.id"
                cols="4"
                sm="3"
                md="2"
            >
                <v-card
                    :to="'/book/' + book.id"
                    class="ma-1"
                >
                    <v-img
                        :src="book.img"
                        :aspect-ratio="11 / 15"
                    />
                    <v-card-subtitle class="text-truncate px-1">
                        {{ book.title }}
                    </v-card-subtitle>
                </v-card>
            </v-col>
        </v-row>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
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
    $backend('/case').then(rsp => {
        if (rsp.err === 'ok') {
            books.value = rsp.books || [];
        }
    });
});
</script>
