import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist_uxp',
    minify: false, // 方便调试，关闭压缩
    sourcemap: true,
    rollupOptions: {
      external: ['uxp', 'photoshop'], // 将 uxp 和 photoshop 声明为外部依赖，防止打包时尝试 bundle 它们
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
