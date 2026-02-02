/**
 * Agent Dashboard Page
 * Protected page - requires authentication
 * Shows agent information and logout functionality
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, getUserData, clearAuthData } from '@/lib/api';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  /**
   * Check authentication on component mount
   * Redirect to login if not authenticated
   */
  useEffect(() => {
    // Check if user is authenticated
    if (!isAuthenticated()) {
      router.push('/auth/login');
      return;
    }

    // Get user data from localStorage
    const userData = getUserData();
    if (userData) {
      setUser(userData);
    }

    setLoading(false);
  }, [router]);

  /**
   * Handle user logout
   * Clears auth data and redirects to login
   */
  const handleLogout = () => {
    // Clear authentication data
    clearAuthData();
    
    // Redirect to login page
    router.push('/auth/login');
  };

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-800">
                Agent Dashboard
              </h1>
            </div>
            <div className="flex items-center">
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            Welcome back, {user?.username || 'Agent'}! 👋
          </h2>
          <p className="text-gray-600">
            You're successfully logged in to the Agent Dashboard.
          </p>
        </div>

        {/* User Info Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Account Information
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between border-b pb-2">
              <span className="text-gray-600">Email:</span>
              <span className="font-medium">{user?.email || 'N/A'}</span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-gray-600">Username:</span>
              <span className="font-medium">{user?.username || 'N/A'}</span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-gray-600">Role:</span>
              <span className="font-medium capitalize">{user?.role || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Status:</span>
              <span className={`font-medium ${user?.is_available ? 'text-green-600' : 'text-gray-600'}`}>
                {user?.is_available ? '🟢 Available' : '⚪ Unavailable'}
              </span>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Quick Actions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button className="p-4 border-2 border-indigo-200 rounded-lg hover:bg-indigo-50 transition">
              <div className="text-3xl mb-2">💬</div>
              <div className="font-medium text-gray-800">Start Chat</div>
              <div className="text-sm text-gray-600">Begin helping customers</div>
            </button>
            <button className="p-4 border-2 border-indigo-200 rounded-lg hover:bg-indigo-50 transition">
              <div className="text-3xl mb-2">📊</div>
              <div className="font-medium text-gray-800">View Analytics</div>
              <div className="text-sm text-gray-600">See your performance</div>
            </button>
            <button className="p-4 border-2 border-indigo-200 rounded-lg hover:bg-indigo-50 transition">
              <div className="text-3xl mb-2">⚙️</div>
              <div className="font-medium text-gray-800">Settings</div>
              <div className="text-sm text-gray-600">Manage your account</div>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}