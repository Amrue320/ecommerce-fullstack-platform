import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context'
import App from './App'
describe('store app shell', () => {
  it('renders the Northstar brand and catalog heading', async () => {
    render(<BrowserRouter><AuthProvider><App /></AuthProvider></BrowserRouter>)
    expect(screen.getByText(/northstar/i)).toBeInTheDocument()
    expect(await screen.findByText(/shop the latest/i)).toBeInTheDocument()
  })
})
