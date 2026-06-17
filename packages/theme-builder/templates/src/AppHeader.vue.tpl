<template>
    <header :style="headerStyle">
        <div :style="innerStyle">
            <a :style="titleStyle" href="/">{{ title }}</a>
            <nav :style="navStyle">
                <a :style="linkStyle" href="/">首页</a>
                <a :style="linkStyle" href="/search">搜索</a>
            </nav>
        </div>
    </header>
</template>

<script setup>
import { ref } from 'vue';

const title = ref('{{THEME_NAME}}');

const headerStyle = {
    background: '#1a73e8',
    color: '#fff',
    padding: '0 16px',
    height: '56px',
    display: 'flex',
    alignItems: 'center',
};
const innerStyle = { display: 'flex', alignItems: 'center', width: '100%', gap: '16px' };
const titleStyle = { fontSize: '1.1rem', fontWeight: '600', color: '#fff', textDecoration: 'none', flex: '1' };
const navStyle = { display: 'flex', gap: '12px' };
const linkStyle = { color: 'rgba(255,255,255,0.85)', textDecoration: 'none', fontSize: '0.9rem' };
</script>
