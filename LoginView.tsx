import React, { useState } from 'react';
import { LogIn, Mail, Lock, Eye, EyeOff, AlertCircle, Loader2, ShieldCheck } from 'lucide-react';
import { loginUser } from '../api/client';
import type { AuthUser } from '../types';

interface LoginViewProps {
  onLoginSuccess: (user: AuthUser, token: string) => void;
  onNavigateToRegister: () => void;
}

export const LoginView: React.FC<LoginViewProps> = ({
  onLoginSuccess,
  onNavigateToRegister,
}) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setErrorMessage('Please enter your email address.');
      return;
    }
    if (!password) {
      setErrorMessage('Please enter your password.');
      return;
    }

    try {
      setIsLoading(true);
      const res = await loginUser({
        email: cleanEmail,
        password,
      });
      onLoginSuccess(res.user, res.access_token);
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-page-container">
      <div className="auth-card">
        {/* Branding Header */}
        <div className="auth-header">
          <div className="auth-logo-badge">P</div>
          <h2>SmartPark</h2>
          <span className="auth-tagline">Queue & Slot Allocation System</span>
          <p className="auth-desc">Sign in to access real-time slot telemetry & manage queues</p>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="auth-alert error">
            <AlertCircle size={18} className="shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          <div className="form-group">
            <label htmlFor="login-email">Email Address</label>
            <div className="input-with-icon">
              <Mail size={16} className="input-icon" />
              <input
                id="login-email"
                type="email"
                className="form-control"
                placeholder="operator@smartpark.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                autoFocus
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="login-password">Password</label>
            <div className="input-with-icon">
              <Lock size={16} className="input-icon" />
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                className="form-control"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                disabled={isLoading}
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            id="login-submit-btn"
            type="submit"
            className="btn-primary auth-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="spin-icon" />
                <span>Authenticating...</span>
              </>
            ) : (
              <>
                <LogIn size={16} />
                <span>Sign In to SmartPark</span>
              </>
            )}
          </button>
        </form>

        {/* Footer Navigation */}
        <div className="auth-footer">
          <p>
            Don't have an operator account?{' '}
            <button
              id="switch-to-register-btn"
              type="button"
              className="auth-link-btn"
              onClick={onNavigateToRegister}
              disabled={isLoading}
            >
              Create Account
            </button>
          </p>
          <div className="auth-security-badge">
            <ShieldCheck size={13} />
            <span>Secure 256-bit JWT & bcrypt protected</span>
          </div>
        </div>
      </div>
    </div>
  );
};
