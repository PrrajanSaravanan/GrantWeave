import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <BrowserRouter>
            <Toaster position="top-right" toastOptions={{
                className: 'bg-surface-800 text-slate-100 border border-white/10',
                style: { background: '#1e293b', color: '#f1f5f9' },
            }} />
            <App />
        </BrowserRouter>
    </React.StrictMode>,
)
