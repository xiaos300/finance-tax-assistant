import { createApp } from 'vue'
import { describe, expect, it } from 'vitest'
import { createPinia } from 'pinia'
import App from '../src/App.vue'

describe('TC061 D0 baseline', () => {
  it('shows the actual preparation status', () => {
    const container = document.createElement('div')
    const app = createApp(App).use(createPinia())
    app.mount(container)
    try {
      expect(container.textContent).toContain('数据库尚未准备')
      expect(container.querySelector('h1')?.textContent).toBe('工程与配置基线')
    } finally {
      app.unmount()
    }
  })
})
