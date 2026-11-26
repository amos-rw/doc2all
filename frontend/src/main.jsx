import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource-variable/nunito'
import './styles/design.css'
import './styles/cat.css'
import './styles/app.css'
import App from './App.jsx'
import { applyTheme, readTheme } from './lib/helpers.js'

if (readTheme() !== 'auto') applyTheme(readTheme())

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
