import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  base: '/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'), // Alias for src imports
    },
  },
  build: {
    outDir: 'dist', // Output directory for the build
  },
  server: {
    port: 3000, // Explicitly set port to 3000 as per your earlier config
    open: true, // Automatically open the browser
  },
});