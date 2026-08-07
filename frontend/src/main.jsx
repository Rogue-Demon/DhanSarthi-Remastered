import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AppInitializer } from '@/app/index'
import './index.css'
import App from './App.jsx'

// Hydrate local theme and profile storage keys early to avoid flash of content
AppInitializer.init();

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
