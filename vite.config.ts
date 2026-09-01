import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// https://vite.dev/config/
export default defineConfig({
  base: './',
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    host: true,
    port: 5173
  },
  build: {
    target: 'esnext',
    cssMinify: true,
    chunkSizeWarningLimit: 1500,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'i18next', 'react-i18next'],
          charts: ['recharts'],
          icons: ['lucide-react']
        }
      }
    }
  }
});
