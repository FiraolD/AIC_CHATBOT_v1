// Resolve the API base URL at runtime so the app works from any machine:
// the browser targets the same host it loaded the frontend from.
// VITE_API_URL (or VITE_API_HOST/VITE_API_PORT) still override when set.
const browserHost =
  typeof window !== 'undefined' && window.location.hostname
    ? window.location.hostname
    : 'localhost';
const apiHost = import.meta.env.VITE_API_HOST || browserHost;
const apiPort = import.meta.env.VITE_API_PORT || '8000';

export default {
  api: {
    baseUrl: import.meta.env.VITE_API_URL || `http://${apiHost}:${apiPort}/api/v1`,
    key: import.meta.env.VITE_API_KEY || 'awash-insurance-2024-secure-key'
  },
  colors: {
    primary: '#004d99',
    secondary: '#c8102e'
  },
  support: {
    phone: '+251-11-6185000',
    email: 'info@awashinsurance.com',
    address: 'Churchill Road, Addis Ababa'
  }
};