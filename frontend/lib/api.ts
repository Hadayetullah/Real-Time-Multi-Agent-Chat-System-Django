/**
 * API Utility Module
 * Centralized API configuration and request handlers
 * Handles authentication, error handling, and API calls
 */

// Base API URL - configurable via environment variable
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Generic API request handler
 * Handles common API operations with error handling
 * 
 * @param {string} endpoint - API endpoint path
 * @param {Object} options - Fetch options (method, body, headers, etc.)
 * @returns {Promise<Object>} - API response data
 */
export async function apiRequest(endpoint: string, options: RequestInit = {}) {
  // Get auth token from cookies if available
  const token = getCookie('access_token');
  
  // Merge default headers with provided headers
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers,
  };

  try {
    // Make API request
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include', // Include cookies in requests
    });

    // Parse JSON response
    const data = await response.json();

    // Handle HTTP errors
    if (!response.ok) {
      throw new Error(data.detail || data.message || 'API request failed');
    }

    return data;
  } catch (error) {
    // Log error for debugging
    console.error('API Request Error:', error);
    throw error;
  }
}

/**
 * Agent Authentication API Calls
 */
export const authAPI = {
  /**
   * Agent signup - sends OTP to email
   * 
   * @param {string} email - User's email address
   * @param {string} password - User's password
   * @returns {Promise<Object>} - Signup response
   */
  signup: async (email: string, password: string) => {
    return apiRequest('/api/users/agent/signup/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  /**
   * Verify OTP and complete signup
   * 
   * @param {string} email - User's email address
   * @param {string} otp - 6-digit OTP code
   * @returns {Promise<Object>} - Authentication tokens and user data
   */
  verifyOTP: async (email: string, otp: string) => {
    return apiRequest('/api/users/agent/verify-otp/', {
      method: 'POST',
      body: JSON.stringify({ email, otp }),
    });
  },

  /**
   * Agent login
   * 
   * @param {string} email - User's email address
   * @param {string} password - User's password
   * @returns {Promise<Object>} - Authentication tokens and user data
   */
  login: async (email: string, password: string) => {
    return apiRequest('/api/users/agent/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  /**
   * Resend OTP to email
   * 
   * @param {string} email - User's email address
   * @param {string} purpose - Purpose of OTP (signup/login/reset)
   * @returns {Promise<Object>} - Resend confirmation
   */
  resendOTP: async (email: string, purpose: string = 'signup') => {
    return apiRequest('/api/users/agent/resend-otp/', {
      method: 'POST',
      body: JSON.stringify({ email, purpose }),
    });
  },
};

/**
 * Cookie Utility Functions
 * Secure cookie management for storing auth tokens
 */

/**
 * Set a cookie with security options
 * 
 * @param {string} name - Cookie name
 * @param {string} value - Cookie value
 * @param {number} days - Expiration days
 */
export function setCookie(name: string, value: string, days: number = 7) {
  // Calculate expiration date
  const expires = new Date();
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
  
  // Set cookie with security flags
  // HttpOnly cannot be set from JavaScript (only server-side)
  // But we can set Secure and SameSite
  const cookieString = `${name}=${value}; expires=${expires.toUTCString()}; path=/; SameSite=Lax${
    process.env.NODE_ENV === 'production' ? '; Secure' : ''
  }`;
  
  document.cookie = cookieString;
}

/**
 * Get cookie value by name
 * 
 * @param {string} name - Cookie name
 * @returns {string|null} - Cookie value or null
 */
export function getCookie(name: string): string | null {
  // Parse all cookies
  const cookies = document.cookie.split(';');
  
  // Find the requested cookie
  for (let cookie of cookies) {
    const [cookieName, cookieValue] = cookie.trim().split('=');
    if (cookieName === name) {
      return cookieValue;
    }
  }
  
  return null;
}

/**
 * Delete a cookie
 * 
 * @param {string} name - Cookie name
 */
export function deleteCookie(name: string) {
  // Set expiration to past date to delete
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
}

/**
 * Save authentication data to cookies
 * 
 * @param {Object} authData - Authentication data (access, refresh tokens, user)
 */
export function saveAuthData(authData: {
  access: string;
  refresh: string;
  user?: any;
}) {
  // Store tokens in cookies
  setCookie('access_token', authData.access, 7); // 7 days expiration
  setCookie('refresh_token', authData.refresh, 30); // 30 days expiration
  
  // Store user data in localStorage (not sensitive)
  if (authData.user) {
    localStorage.setItem('user', JSON.stringify(authData.user));
  }
}

/**
 * Get stored user data
 * 
 * @returns {Object|null} - User data or null
 */
export function getUserData() {
  const userData = localStorage.getItem('user');
  return userData ? JSON.parse(userData) : null;
}

/**
 * Clear all authentication data (logout)
 */
export function clearAuthData() {
  // Delete cookies
  deleteCookie('access_token');
  deleteCookie('refresh_token');
  
  // Clear localStorage
  localStorage.removeItem('user');
}

/**
 * Check if user is authenticated
 * 
 * @returns {boolean} - Authentication status
 */
export function isAuthenticated(): boolean {
  const token = getCookie('access_token');
  return !!token;
}