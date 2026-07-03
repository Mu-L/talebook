<template>
    <footer :class="['tb-theme-footer', `tb-theme-footer-${variant}`]">
        <div
            v-if="footerExtraHtml"
            class="press-content"
            v-html="footerExtraHtml"
        />
        <div
            v-if="footerText"
            class="press-content"
            v-html="footerText"
        />
        <nav class="tb-theme-footer-links">
            <a
                href="https://github.com/talebook/talebook"
                target="_blank"
            >Github</a>
            <a
                href="https://hub.docker.com/r/talebook/talebook"
                target="_blank"
            >Docker</a>
            <a
                href="http://talebook.org"
                target="_blank"
            >Project</a>
        </nav>
    </footer>
</template>

<script setup>
import { computed } from 'vue';
import { useMainStore } from '@/stores/main';

defineProps({
    variant: {
        type: String,
        required: true,
        validator: (value) => ['cloudflare-radar', 'mybooks-midnight', 'hacker-news-compact'].includes(value),
    },
});

const store = useMainStore();
const footerText = computed(() => store.sys.footer || '');
const footerExtraHtml = computed(() => store.sys.footer_extra_html || '');
</script>

<style scoped>
.tb-theme-footer {
    border-top: 1px solid rgba(120, 130, 150, .24);
    font-size: 12px;
    margin-top: 32px;
    padding: 16px 12px 24px;
    text-align: center;
}

.tb-theme-footer-links {
    display: inline-flex;
    gap: 14px;
    margin-top: 6px;
}

.tb-theme-footer a {
    color: inherit;
    text-decoration: none;
}

.tb-theme-footer-cloudflare-radar {
    color: #526172;
}

.tb-theme-footer-mybooks-midnight {
    color: #9fb1c8;
}

.tb-theme-footer-hacker-news-compact {
    border-top-color: #e6e1c8;
    color: #828282;
    font-family: Verdana, Geneva, sans-serif;
    margin-top: 12px;
    padding: 8px 12px 18px;
}
</style>
