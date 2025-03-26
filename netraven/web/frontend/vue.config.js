module.exports = {
  lintOnSave: false,
  devServer: {
    client: {
      overlay: false,
    },
    proxy: {
      '/api': {
        target: process.env.VUE_APP_API_URL || 'http://localhost',
        changeOrigin: true,
        secure: false
      }
    }
  },
}