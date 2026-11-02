import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import './index.css';

// Global API Interceptor for JWT Authorization Bearer Token
try {
  if (typeof window !== 'undefined' && window.fetch) {
    const originalFetch = window.fetch.bind(window);
    const customFetch: typeof window.fetch = async (input, init) => {
      try {
        const token = localStorage.getItem('trace_access_token');
        if (token && typeof input === 'string' && input.startsWith('/api')) {
          const headers = new Headers(init?.headers);
          if (!headers.has('Authorization')) {
            headers.set('Authorization', `Bearer ${token}`);
          }
          init = { ...init, headers };
        }
      } catch {
        // Ignore localStorage access issues in sandboxed environments
      }
      return originalFetch(input, init);
    };

    try {
      window.fetch = customFetch;
    } catch {
      try {
        Object.defineProperty(window, 'fetch', {
          value: customFetch,
          configurable: true,
          writable: true,
        });
      } catch {
        try {
          Object.defineProperty(Window.prototype, 'fetch', {
            value: customFetch,
            configurable: true,
            writable: true,
          });
        } catch {
          // Fall back gracefully if window.fetch cannot be overwritten in this sandbox
        }
      }
    }
  }
} catch (e) {
  console.warn('API interceptor initialization notice:', e);
}


ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
