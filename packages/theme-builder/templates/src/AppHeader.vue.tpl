<template>
    <header :style="headerStyle">
        <nav :style="navStyle">
            <a href="/" :style="logoStyle">{{ title }}</a>
            <div :style="linksStyle">
                <a href="/" :style="linkStyle">首页</a>
                <a href="/library" :style="linkStyle">书库</a>
                <a href="/network" :style="linkStyle">网络书库</a>
                <a href="/nav" :style="linkStyle">分类</a>
            </div>
        </nav>
    </header>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const title = ref('Talebook');

onMounted(() => {
    if (document.title) {
        title.value = document.title.split(' - ')[0] || 'Talebook';
    }
});

const headerStyle = {
    background: 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)',
    color: '#ffffff',
    padding: '0',
    height: '48px',
    display: 'flex',
    alignItems: 'center',
    position: 'sticky',
    top: '0',
    zIndex: '100',
    boxShadow: '0 2px 8px rgba(0,0,0,0.25)',
    boxSizing: 'border-box',
};

const navStyle = {
    display: 'flex',
    alignItems: 'center',
    width: '100%',
    padding: '0 16px',
    gap: '8px',
};

const logoStyle = {
    fontSize: '20px',
    fontWeight: 'bold',
    color: '#ffffff',
    textDecoration: 'none',
    marginRight: '24px',
    flexShrink: '0',
};

const linksStyle = {
    display: 'flex',
    gap: '4px',
};

const linkStyle = {
    color: 'rgba(255,255,255,0.9)',
    textDecoration: 'none',
    fontSize: '14px',
    padding: '6px 10px',
    borderRadius: '4px',
};
</script>
