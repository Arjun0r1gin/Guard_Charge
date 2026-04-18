import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import EVProfile from './pages/EVProfile'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/ev/:id" element={<EVProfile />} />
      </Routes>
    </BrowserRouter>
  )
}
