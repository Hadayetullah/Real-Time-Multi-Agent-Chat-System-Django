/**
 * OTP Verification Modal Component
 * Reusable modal for OTP input and verification
 * Includes resend functionality and countdown timer
 */

'use client';

import { useState, useEffect } from 'react';
import { authAPI } from '@/lib/api';

interface OTPModalProps {
  isOpen: boolean;              // Controls modal visibility
  onClose: () => void;          // Callback to close modal
  onVerify: (otp: string) => Promise<void>;  // Callback when OTP is verified
  email: string;                // User's email for OTP resend
  purpose?: string;             // Purpose of OTP (signup/login/reset)
}

export default function OTPModal({
  isOpen,
  onClose,
  onVerify,
  email,
  purpose = 'signup'
}: OTPModalProps) {
  // State management
  const [otp, setOtp] = useState('');                    // OTP input value
  const [loading, setLoading] = useState(false);         // Loading state during verification
  const [error, setError] = useState('');                // Error message
  const [countdown, setCountdown] = useState(60);        // Resend countdown timer
  const [canResend, setCanResend] = useState(false);     // Enable/disable resend button

  /**
   * Countdown timer effect
   * Counts down from 60 seconds before allowing resend
   */
  useEffect(() => {
    if (!isOpen) {
      // Reset countdown when modal closes
      setCountdown(60);
      setCanResend(false);
      return;
    }

    // Start countdown
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      // Enable resend when countdown reaches 0
      setCanResend(true);
    }
  }, [countdown, isOpen]);

  /**
   * Handle OTP input change
   * Restricts input to 6 digits
   */
  const handleOTPChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, ''); // Remove non-digits
    if (value.length <= 6) {
      setOtp(value);
      setError(''); // Clear error on input
    }
  };

  /**
   * Handle OTP verification
   * Validates and submits OTP
   */
  const handleVerify = async () => {
    // Validate OTP length
    if (otp.length !== 6) {
      setError('Please enter a 6-digit OTP');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Call parent's verify function
      await onVerify(otp);
      // Success - modal will be closed by parent
    } catch (err: any) {
      // Handle verification error
      setError(err.message || 'Invalid OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle OTP resend
   * Requests a new OTP and restarts countdown
   */
  const handleResend = async () => {
    setLoading(true);
    setError('');

    try {
      // Call API to resend OTP
      await authAPI.resendOTP(email, purpose);
      
      // Reset countdown and OTP input
      setCountdown(60);
      setCanResend(false);
      setOtp('');
      
      // Show success message
      setError(''); // Clear any previous errors
    } catch (err: any) {
      setError(err.message || 'Failed to resend OTP');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Enter key press for quick submission
   */
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && otp.length === 6) {
      handleVerify();
    }
  };

  // Don't render if modal is not open
  if (!isOpen) return null;

  return (
    <>
      {/* Modal Backdrop - semi-transparent overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />

      {/* Modal Container */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          {/* Modal Header */}
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-800">
              Verify OTP
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
              aria-label="Close modal"
            >
              ×
            </button>
          </div>

          {/* Instructions */}
          <p className="text-gray-600 mb-6">
            Enter the 6-digit code sent to <strong>{email}</strong>
          </p>

          {/* OTP Input Field */}
          <div className="mb-4">
            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={otp}
              onChange={handleOTPChange}
              onKeyPress={handleKeyPress}
              placeholder="000000"
              maxLength={6}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-center text-2xl tracking-widest focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={loading}
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {/* Verify Button */}
          <button
            onClick={handleVerify}
            disabled={loading || otp.length !== 6}
            className={`w-full py-3 rounded-lg font-semibold text-white mb-4 ${
              loading || otp.length !== 6
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700'
            }`}
          >
            {loading ? 'Verifying...' : 'Verify OTP'}
          </button>

          {/* Resend OTP Section */}
          <div className="text-center">
            {canResend ? (
              <button
                onClick={handleResend}
                disabled={loading}
                className="text-indigo-600 hover:text-indigo-700 font-medium"
              >
                Resend OTP
              </button>
            ) : (
              <p className="text-gray-500 text-sm">
                Resend OTP in {countdown}s
              </p>
            )}
          </div>
        </div>
      </div>
    </>
  );
}