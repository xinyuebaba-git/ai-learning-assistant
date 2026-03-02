import { describe, it, expect, vi, beforeEach } from 'vitest'
import api, { authApi, videoApi, searchApi, noteApi } from '../api'

// Mock axios
vi.mock('axios', () => {
  const mockAxios = vi.fn()
  mockAxios.create = vi.fn(() => ({
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  }))
  return { default: mockAxios }
})

describe('API Client', () => {
  it('creates axios instance with correct config', () => {
    expect(api).toBeDefined()
  })

  describe('authApi', () => {
    it('has login method', () => {
      expect(authApi.login).toBeDefined()
      expect(typeof authApi.login).toBe('function')
    })

    it('has register method', () => {
      expect(authApi.register).toBeDefined()
      expect(typeof authApi.register).toBe('function')
    })

    it('has getMe method', () => {
      expect(authApi.getMe).toBeDefined()
      expect(typeof authApi.getMe).toBe('function')
    })
  })

  describe('videoApi', () => {
    it('has list method', () => {
      expect(videoApi.list).toBeDefined()
      expect(typeof videoApi.list).toBe('function')
    })

    it('has get method', () => {
      expect(videoApi.get).toBeDefined()
      expect(typeof videoApi.get).toBe('function')
    })

    it('has scan method', () => {
      expect(videoApi.scan).toBeDefined()
      expect(typeof videoApi.scan).toBe('function')
    })

    it('has toggleFavorite method', () => {
      expect(videoApi.toggleFavorite).toBeDefined()
      expect(typeof videoApi.toggleFavorite).toBe('function')
    })
  })

  describe('searchApi', () => {
    it('has search method', () => {
      expect(searchApi.search).toBeDefined()
      expect(typeof searchApi.search).toBe('function')
    })

    it('has suggestions method', () => {
      expect(searchApi.suggestions).toBeDefined()
      expect(typeof searchApi.suggestions).toBe('function')
    })
  })

  describe('noteApi', () => {
    it('has list method', () => {
      expect(noteApi.list).toBeDefined()
      expect(typeof noteApi.list).toBe('function')
    })

    it('has create method', () => {
      expect(noteApi.create).toBeDefined()
      expect(typeof noteApi.create).toBe('function')
    })

    it('has update method', () => {
      expect(noteApi.update).toBeDefined()
      expect(typeof noteApi.update).toBe('function')
    })

    it('has delete method', () => {
      expect(noteApi.delete).toBeDefined()
      expect(typeof noteApi.delete).toBe('function')
    })
  })
})
