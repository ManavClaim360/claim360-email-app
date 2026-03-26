import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

// Debug startup
console.log('🚀 React app starting...', import.meta.env.MODE, import.meta.env.VITE_API_URL)

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30000 },
    mutations: { retry: 0 },
  },
})

// Global error boundary to show actual error instead of white screen
class ErrorBoundary extends React.Component {
  constructor(props) { 
    super(props)
    this.state = { error: null }
    console.log('✓ ErrorBoundary ready')
  }
  static getDerivedStateFromError(error) { 
    console.error('❌ React Error Boundary caught:', error)
    return { error } 
  }
  componentDidCatch(error, info) {
    console.error('Error stack:', info.componentStack)
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 40, fontFamily: 'monospace', background: '#0D1117', color: '#f85149', minHeight: '100vh' }}>
          <h2 style={{ marginBottom: 16, color: '#f0f6fc' }}>⚠ Application Error</h2>
          <p style={{ marginBottom: 12, color: '#8b949e', fontFamily: 'sans-serif' }}>
            Something crashed on startup. Open browser DevTools (F12) → Console for the full error.
          </p>
          <pre style={{ background: '#161B22', padding: 20, borderRadius: 8, border: '1px solid #30363D', fontSize: 13, overflow: 'auto', color: '#f85149' }}>
            {this.state.error?.message}
            {'\n\n'}
            {this.state.error?.stack}
          </pre>
          <button onClick={() => window.location.reload()}
            style={{ marginTop: 20, padding: '10px 20px', background: '#1C305E', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 14 }}>
            Reload App
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

console.log('📍 Mounting React app...')
const rootElement = document.getElementById('root')
console.log('Root element found:', rootElement)

ReactDOM.createRoot(rootElement).render(
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#1C2333',
              color: '#E6EDF3',
              border: '1px solid #30363D',
              borderRadius: '8px',
              fontSize: '13px',
            },
            success: { iconTheme: { primary: '#3fb950', secondary: '#0D1117' } },
            error:   { iconTheme: { primary: '#f85149', secondary: '#0D1117' } },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  </ErrorBoundary>
)
