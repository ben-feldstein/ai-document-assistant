import { describe, it, expect } from 'vitest'
import { render, screen } from './test-utils'
import App from '../App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(screen.getByText('Welcome back')).toBeInTheDocument()
  })
})
