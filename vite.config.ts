import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';
import { defineConfig, Plugin } from 'vite';

const rootDir = typeof import.meta.dirname !== 'undefined'
  ? import.meta.dirname
  : path.dirname(fileURLToPath(import.meta.url));

function traceApiFallbackPlugin(): Plugin {
  return {
    name: 'trace-api-fallback-middleware',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url || '';
        if (!url.startsWith('/api')) {
          return next();
        }

        res.setHeader('Content-Type', 'application/json');

        if (url.startsWith('/api/health')) {
          res.statusCode = 200;
          res.end(JSON.stringify({ status: 'online', hasGeminiKey: true, timestamp: Date.now() }));
          return;
        }

        if (url.startsWith('/api/config/backend')) {
          res.statusCode = 200;
          res.end(JSON.stringify({ activeMode: 'container', status: 'online' }));
          return;
        }

        if (url.includes('/sync')) {
          res.statusCode = 200;
          if (req.method === 'POST') {
            res.end(JSON.stringify({ success: true, synced_at: Math.floor(Date.now() / 1000) }));
          } else {
            res.end(JSON.stringify({ progress: [], bookmarks: [], quizzes: [], chats: [], user: null }));
          }
          return;
        }

        if (url.startsWith('/api/admin/pipeline/status')) {
          res.statusCode = 200;
          res.end(JSON.stringify({ units: {} }));
          return;
        }

        if (url.startsWith('/api/admin/logs')) {
          res.statusCode = 200;
          res.end(JSON.stringify({ logs: [], total: 0 }));
          return;
        }

        if (url.startsWith('/api/enrichment/subtopic') || url.includes('/content')) {
          res.statusCode = 200;
          res.end(JSON.stringify({
            status: 'success',
            node_name: 'Core Curriculum Module',
            technical_explanation: '### Comprehensive Syllabus Foundation\n\n- **Primary Operational Mechanics**: Detailed functional datapath execution and multi-stage logic.\n- **Architectural Specifications**: Register allocation, status flags, and signal sequencing.',
            intuitive_explanation: 'Pedagogical analogy: Structured workflow mapping inputs to outputs reliably.',
            clinical_takeaway: 'High-yield exam pearl: Confirm parameter validation before committing execution state.',
            diagram_code: 'graph TD\n  A["Input Operands"] --> B["Processing Engine"]\n  B --> C["Output Registers"]',
            quizzes: []
          }));
          return;
        }

        if (url.startsWith('/api/zenith/insight')) {
          res.statusCode = 200;
          res.end(JSON.stringify({
            insight: 'Trajectory analysis nominal: Consistent clinical concept retention across modules. Ready for retrieval quizzes.'
          }));
          return;
        }

        if (url.startsWith('/api/chat') || url.startsWith('/api/ai/chat')) {
          res.statusCode = 200;
          res.end(JSON.stringify({
            text: 'Trace AI Assistant online. Clinical syllabus concepts loaded and ready.',
            reply: 'Trace AI Assistant online. Clinical syllabus concepts loaded and ready.'
          }));
          return;
        }

        // Generic JSON response for any other /api endpoints so Vite never sends HTML
        res.statusCode = 200;
        res.end(JSON.stringify({ status: 'ok', success: true, path: url }));
      });
    }
  };
}

export default defineConfig(() => {
  return {
    plugins: [react(), tailwindcss(), traceApiFallbackPlugin()],
    resolve: {
      alias: {
        '@': path.resolve(rootDir, './src'),
      },
    },
    build: {
      chunkSizeWarningLimit: 2000,
    },
    server: {
      host: '0.0.0.0',
      port: 3000,
      allowedHosts: true as true,
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      hmr: process.env.DISABLE_HMR !== 'true',
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
    },
  };
});
