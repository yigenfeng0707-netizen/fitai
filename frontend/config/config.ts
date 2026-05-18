export default {
  title: 'FitAI - 智能健身管理系统',
  favicon: '/favicon.ico',
  layout: {},
  routes: require('./routes').default,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
  nodeModulesTransform: {
    type: 'none',
  },
  fastRefresh: {},
};