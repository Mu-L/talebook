<template>
    <footer :style="footerStyle">
        <p :style="textStyle">
            Powered by
            <a
                :style="linkStyle"
                href="https://github.com/talebook/talebook"
                target="_blank"
                rel="noopener noreferrer"
            >Talebook</a>
            &bull; Theme: {{THEME_NAME}}
        </p>
    </footer>
</template>

<script setup>
const footerStyle = {
    borderTop: '1px solid rgba(0,0,0,0.12)',
    padding: '12px 16px',
    textAlign: 'center',
};
const textStyle = { margin: '0', fontSize: '0.8rem', color: 'rgba(0,0,0,0.54)' };
const linkStyle = { color: '#1a73e8', textDecoration: 'none' };
</script>
