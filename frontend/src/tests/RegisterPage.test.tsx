import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import RegisterPage from '../pages/RegisterPage'

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

describe('RegisterPage', () => {
  it('renders registration form', () => {
    render(<RegisterPage />, { wrapper: createWrapper() })
    
    expect(screen.getByText(/注册账号/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/邮箱/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/用户名/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/密码/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/确认密码/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /注册/i })).toBeInTheDocument()
  })

  it('shows login link', () => {
    render(<RegisterPage />, { wrapper: createWrapper() })
    
    expect(screen.getByText(/立即登录/i)).toBeInTheDocument()
  })

  it('validates password mismatch', () => {
    render(<RegisterPage />, { wrapper: createWrapper() })
    
    fireEvent.change(screen.getByLabelText(/密码/i), {
      target: { value: 'password123' }
    })
    fireEvent.change(screen.getByLabelText(/确认密码/i), {
      target: { value: 'password456' }
    })
    fireEvent.click(screen.getByRole('button', { name: /注册/i }))
    
    // 应该显示错误信息
    expect(screen.getByText(/两次输入的密码不一致/i)).toBeInTheDocument()
  })

  it('validates password length', () => {
    render(<RegisterPage />, { wrapper: createWrapper() })
    
    fireEvent.change(screen.getByLabelText(/密码/i), {
      target: { value: '123' }
    })
    fireEvent.change(screen.getByLabelText(/确认密码/i), {
      target: { value: '123' }
    })
    fireEvent.click(screen.getByRole('button', { name: /注册/i }))
    
    expect(screen.getByText(/密码长度至少为/i)).toBeInTheDocument()
  })
})
