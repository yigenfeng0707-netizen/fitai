import { defineConfig } from '@tarojs/cli'

export default defineConfig({
  projectName: 'fitai-miniapp',
  date: '2024-01-01',
  designWidth: 750,
  deviceRatio: { 640: 2.34 / 2, 750: 1, 828: 1.81 / 2 },
  sourceRoot: 'src',
  outputRoot: 'dist',
  plugins: ['@tarojs/plugin-platform-weapp', '@tarojs/plugin-framework-react'],
  defineConstants: {},
  copy: { patterns: [], options: {} },
  framework: 'react',
  compiler: { type: 'webpack5', prebundle: { enable: false } },
  sass: { resource: [], projectDirectory: '' },
  miniapp: {
    postcss: {
      pxtransform: { enable: true, config: {} },
      cssModules: { enable: false }
    }
  }
})
