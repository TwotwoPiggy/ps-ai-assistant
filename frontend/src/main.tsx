import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// 尝试获取 UXP 入口设置
let entrypoints: any = null;
try {
  // @ts-ignore
  entrypoints = require('uxp').entrypoints;
} catch (e) {
  // 忽略非 UXP 环境下的加载报错
}

if (entrypoints) {
  let root: any = null;
  entrypoints.setup({
    plugin: {
      create() {
        console.log("UXP Plugin created");
      },
      destroy() {
        console.log("UXP Plugin destroyed");
      }
    },
    panels: {
      assistantPanel: {
        show(event: any) {
          if (!root) {
            root = createRoot(event.node);
            root.render(
              <StrictMode>
                <App />
              </StrictMode>
            );
          }
        },
        hide() {
          console.log("UXP Panel hidden");
        }
      }
    }
  });
} else {
  // 浏览器开发调试环境正常挂载
  const container = document.getElementById('root');
  if (container) {
    const root = createRoot(container);
    root.render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
  }
}

