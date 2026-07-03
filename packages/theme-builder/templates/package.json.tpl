{
  "name": "{{THEME_NAME}}",
  "version": "{{THEME_VERSION}}",
  "description": "{{THEME_DESCRIPTION}}",
  "type": "module",
  "scripts": {
    "build": "vite build",
    "dev": "vite build --watch",
    "pack": "theme-builder pack",
    "validate": "theme-builder validate"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0",
    "vue": "^3.5.0",
    "vuetify": "^3.0.0"
  }
}
