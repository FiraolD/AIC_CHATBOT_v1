import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// Add error boundary for better debugging
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-4">
          <h1 className="text-2xl font-bold text-red-600 mb-2">Application Error</h1>
          <p className="text-gray-700 mb-4">Something went wrong. Please check the console for details.</p>
          <pre className="text-left bg-gray-100 p-4 rounded max-w-full overflow-auto max-h-60">
            {this.state.error?.toString()}
          </pre>
          <button 
            className="mt-4 px-4 py-2 bg-[#004d99] text-white rounded"
            onClick={() => window.location.reload()}
          >
            Refresh Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)