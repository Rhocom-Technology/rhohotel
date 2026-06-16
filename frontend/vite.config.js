// import { defineConfig } from 'vite'
// import vue from '@vitejs/plugin-vue'
// import path from 'path'

// export default defineConfig(({ command }) => {
//   return {
//     define: {
//       __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'false',
//     },
//     plugins: [vue()],
//     // base: command === 'build' ? '/assets/rhohotel/frontend/' : '/',
//     base: command === 'build' ? '/assets/rhohotel/frontend/' : '/frontdesk/',
//     server: {
//       port: 8080,
//       proxy: {
//         '/api': {
//           target: 'http://localhost:8000',
//           changeOrigin: true,
//           headers: { 'X-Frappe-Site-Name': 'hotel.local' },
//         },
//         '/assets': {
//           target: 'http://localhost:8000',
//           changeOrigin: true,
//           headers: { 'X-Frappe-Site-Name': 'hotel.local' },
//         },
//       },
//     },
//     resolve: {
//       alias: { '@': path.resolve(__dirname, 'src') },
//     },
//     build: {
//       outDir: '../rhohotel/public/frontend',
//       emptyOutDir: true,
//       target: 'es2018',
//       rollupOptions: {
//         output: {
//           entryFileNames: `[name].js`,
//           chunkFileNames: `[name].js`,
//           assetFileNames: `[name].[ext]`,
//         },
//       },
//     },
//     optimizeDeps: {
//       include: [
//         'frappe-ui > feather-icons',
//         'showdown',
//         'engine.io-client',
//         'debug',
//         'socket.io-client',
//       ],
//     },
//   }
// })


import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ command }) => {
  return {
    define: {
      __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'false',
    },
    plugins: [vue()],
    // base: command === 'build' ? '/assets/rhohotel/frontend/' : '/',
    base: command === 'build' ? '/assets/rhohotel/frontend/' : '/frontdesk/',
    server: {
      port: 8080,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          headers: { 'X-Frappe-Site-Name': 'hotel.local' },
        },
        '/assets': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          headers: { 'X-Frappe-Site-Name': 'hotel.local' },
        },
        '/files': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          headers: { 'X-Frappe-Site-Name': 'hotel.local' },
        },
        '/private': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          headers: { 'X-Frappe-Site-Name': 'hotel.local' },
        },
      },
    },
    resolve: {
      alias: { '@': path.resolve(__dirname, 'src') },
    },
    build: {
      outDir: '../rhohotel/public/frontend',
      emptyOutDir: true,
      target: 'es2018',
      rollupOptions: {
        output: {
          entryFileNames: `[name].js`,
          chunkFileNames: `[name].js`,
          assetFileNames: `[name].[ext]`,
        },
      },
    },
    optimizeDeps: {
      include: [
        'frappe-ui > feather-icons',
        'showdown',
        'engine.io-client',
        'debug',
        'socket.io-client',
      ],
    },
  }
})