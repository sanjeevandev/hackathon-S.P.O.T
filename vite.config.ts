import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// https://vite.dev/config/
export default defineConfig({
  base: '/',
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      }
    },
    watch: {
      ignored: ['**/artifacts/**', '**/backend/**', '**/.git/**']
    }
  },
  build: {
    target: 'esnext',
    cssMinify: true,
    chunkSizeWarningLimit: 1500,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('lucide-react')) {
              return 'icons';
            }
            if (
              id.includes('html2pdf') ||
              id.includes('jspdf') ||
              id.includes('html2canvas') ||
              id.includes('qrcode.react')
            ) {
              return 'export-utils';
            }
            // Keep React, Recharts, i18n in unified vendor chunk to avoid circular module initialization
            return 'vendor';
          }
        }
      }
    }
  }
});
