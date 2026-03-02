import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import LoginPage from '../pages/LoginPage'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('LoginPage', () => {
  it('renders login form', () => {
    render(<LoginPage />, { wrapper: createWrapper() })
    
    expect(screen.getByText(/登录/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/用户名/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/密码/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument()
  })

  it('shows register link', () => {
    render(<LoginPage />, { wrapper: createWrapper() })
    
    expect(screen.getByText(/立即注册/i)).toBeInTheDocument()
  })

  it('has logo and title', () => {
    render(<LoginPage />, { wrapper: createWrapper() })
    
    expect(screen.getByText('Course AI Helper')).toBeInTheDocument()
    expect(screen.getByText('AI 课程学习助手')).toBeInTheDocument()
  })
})
