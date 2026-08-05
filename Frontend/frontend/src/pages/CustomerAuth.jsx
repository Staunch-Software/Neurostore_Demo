import React, { useContext, useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ShopContext } from '../components/context/ShopContext';
import { auth, googleProvider } from '../firebase';
import { signInWithPopup } from 'firebase/auth';
import './CustomerAuth.css';

const API = 'https://www.neurostore.in';

// ── OtpScreen ─────────────────────────────────────────────────────────────────
const OtpScreen = ({
    email, otp, otpError, successMsg, resendSecs, isLoading,
    otpRefs, onOtpChange, onOtpKeyDown, onOtpPaste,
    onVerify, onResend, onBack
}) => (
    <div className="otp-overlay">
        <div className="otp-card">
            <div className="otp-icon">{successMsg ? '🎉' : '✉️'}</div>
            <h2 className="otp-title">
                {successMsg ? 'Account Created!' : 'Verify your email'}
            </h2>
            {successMsg
                ? <p className="otp-success-msg">{successMsg}</p>
                : <>
                    <p className="otp-subtitle">
                        We sent a 6-digit code to<br />
                        <strong>{email}</strong>
                    </p>
                    <form onSubmit={onVerify}>
                        <div className="otp-boxes" onPaste={onOtpPaste}>
                            {otp.map((digit, i) => (
                                <input
                                    key={i}
                                    ref={el => otpRefs.current[i] = el}
                                    type="text"
                                    inputMode="numeric"
                                    maxLength={1}
                                    value={digit}
                                    onChange={e => onOtpChange(i, e.target.value)}
                                    onKeyDown={e => onOtpKeyDown(i, e)}
                                    className={`otp-box ${digit ? 'filled' : ''} ${otpError ? 'error' : ''}`}
                                    autoComplete="one-time-code"
                                />
                            ))}
                        </div>
                        {otpError && <p className="otp-error-msg">{otpError}</p>}
                        <button type="submit" className="auth-btn otp-verify-btn" disabled={isLoading}>
                            {isLoading ? 'Verifying…' : 'Verify & Create Account'}
                        </button>
                    </form>
                    <div className="otp-resend">
                        {resendSecs > 0
                            ? <span>Resend code in <strong>{resendSecs}s</strong></span>
                            : <button type="button" className="otp-resend-btn" onClick={onResend} disabled={isLoading}>
                                Resend OTP
                              </button>
                        }
                    </div>
                    <button type="button" className="otp-back-btn" onClick={onBack}>
                        ← Change email
                    </button>
                </>
            }
        </div>
    </div>
);

// ── ForgotScreen ──────────────────────────────────────────────────────────────
const ForgotScreen = ({
    step, email, otp, newPassword, confirmPassword,
    error, resendSecs, isLoading, otpRefs,
    onEmailChange, onEmailSubmit,
    onOtpChange, onOtpKeyDown, onOtpPaste,
    onNewPasswordChange, onConfirmPasswordChange,
    onVerify, onResend, onClose,
}) => (
    <div className="otp-overlay">
        <div className="otp-card">
            {step === 'done' ? (
                <>
                    <div className="otp-icon">🔐</div>
                    <h2 className="otp-title">Password Reset!</h2>
                    <p className="otp-success-msg">✅ Your password has been updated. You can now sign in with your new password.</p>
                </>
            ) : step === 'email' ? (
                <>
                    <div className="otp-icon">🔑</div>
                    <h2 className="otp-title">Forgot Password?</h2>
                    <p className="otp-subtitle">Enter your registered email and we'll send you a 6-digit verification code.</p>
                    <form onSubmit={onEmailSubmit}>
                        <input
                            type="email"
                            className="forgot-input"
                            placeholder="Email Address"
                            required
                            value={email}
                            onChange={e => onEmailChange(e.target.value)}
                            autoFocus
                        />
                        {error && <p className="otp-error-msg">{error}</p>}
                        <button type="submit" className="auth-btn otp-verify-btn" disabled={isLoading}>
                            {isLoading ? 'Sending…' : 'Send OTP'}
                        </button>
                    </form>
                    <button type="button" className="otp-back-btn" onClick={onClose}>← Back to Sign In</button>
                </>
            ) : (
                <>
                    <div className="otp-icon">✉️</div>
                    <h2 className="otp-title">Reset Password</h2>
                    <p className="otp-subtitle">Code sent to <strong>{email}</strong></p>
                    <form onSubmit={onVerify}>
                        <div className="otp-boxes" onPaste={onOtpPaste}>
                            {otp.map((digit, i) => (
                                <input
                                    key={i}
                                    ref={el => otpRefs.current[i] = el}
                                    type="text"
                                    inputMode="numeric"
                                    maxLength={1}
                                    value={digit}
                                    onChange={e => onOtpChange(i, e.target.value)}
                                    onKeyDown={e => onOtpKeyDown(i, e)}
                                    className={`otp-box ${digit ? 'filled' : ''} ${error ? 'error' : ''}`}
                                    autoComplete="one-time-code"
                                />
                            ))}
                        </div>
                        <input type="password" className="forgot-input" placeholder="New Password"         required value={newPassword}      onChange={e => onNewPasswordChange(e.target.value)} />
                        <input type="password" className="forgot-input" placeholder="Confirm New Password" required value={confirmPassword} onChange={e => onConfirmPasswordChange(e.target.value)} />
                        {error && <p className="otp-error-msg">{error}</p>}
                        <button type="submit" className="auth-btn otp-verify-btn" disabled={isLoading}>
                            {isLoading ? 'Resetting…' : 'Reset Password'}
                        </button>
                    </form>
                    <div className="otp-resend">
                        {resendSecs > 0
                            ? <span>Resend code in <strong>{resendSecs}s</strong></span>
                            : <button type="button" className="otp-resend-btn" onClick={onResend} disabled={isLoading}>Resend OTP</button>
                        }
                    </div>
                    <button type="button" className="otp-back-btn" onClick={onClose}>← Cancel</button>
                </>
            )}
        </div>
    </div>
);

// ── Main component ─────────────────────────────────────────────────────────────
const CustomerAuth = () => {
    const { setUser } = useContext(ShopContext);

    // 'login' | 'register' | 'guest'
    const [activePanel, setActivePanel] = useState('login');

    const [formData, setFormData]   = useState({ name: '', email: '', phone: '', password: '' });
    const [error, setError]         = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [signInMethod, setSignInMethod] = useState('email');

    const navigate   = useNavigate();
    const location   = useLocation();
    const redirectTo = location.state?.from || '/';

    // ── OTP state ──────────────────────────────────────────────────────────────
    const [otpStep,    setOtpStep]    = useState(false);
    const [otp,        setOtp]        = useState(['', '', '', '', '', '']);
    const [otpError,   setOtpError]   = useState('');
    const [successMsg, setSuccessMsg] = useState('');
    const [resendSecs, setResendSecs] = useState(0);
    const otpRefs = useRef([]);

    useEffect(() => {
        if (resendSecs <= 0) return;
        const t = setTimeout(() => setResendSecs(s => s - 1), 1000);
        return () => clearTimeout(t);
    }, [resendSecs]);

    // ── Forgot password state ──────────────────────────────────────────────────
    const [forgotStep,       setForgotStep]       = useState(null);
    const [forgotEmail,      setForgotEmail]      = useState('');
    const [forgotOtp,        setForgotOtp]        = useState(['', '', '', '', '', '']);
    const [newPassword,      setNewPassword]      = useState('');
    const [confirmPassword,  setConfirmPassword]  = useState('');
    const [forgotError,      setForgotError]      = useState('');
    const [forgotLoading,    setForgotLoading]    = useState(false);
    const [forgotResendSecs, setForgotResendSecs] = useState(0);
    const forgotOtpRefs = useRef([]);

    useEffect(() => {
        if (forgotResendSecs <= 0) return;
        const t = setTimeout(() => setForgotResendSecs(s => s - 1), 1000);
        return () => clearTimeout(t);
    }, [forgotResendSecs]);

    const switchPanel = (panel) => {
        setActivePanel(panel);
        setError('');
        setFormData({ name: '', email: '', phone: '', password: '' });
        setOtpStep(false);
        setOtp(['', '', '', '', '', '']);
        setOtpError('');
        setSignInMethod('email');
    };

    const handleChange = (e) =>
        setFormData({ ...formData, [e.target.name]: e.target.value });

    const loginSuccess = (userData) => {
        localStorage.setItem('neuroUser', JSON.stringify(userData));
        setUser(userData);
        navigate(redirectTo, { replace: true });
    };

    // ── Guest checkout ─────────────────────────────────────────────────────────
    const handleGuestCheckout = () => {
        navigate('/checkout', { state: { guest: true } });
    };

    // ── OTP handlers ───────────────────────────────────────────────────────────
    const handleOtpChange = (index, value) => {
        if (!/^\d*$/.test(value)) return;
        const next = [...otp];
        next[index] = value.slice(-1);
        setOtp(next);
        setOtpError('');
        if (value && index < 5) otpRefs.current[index + 1]?.focus();
    };

    const handleOtpKeyDown = (index, e) => {
        if (e.key === 'Backspace' && !otp[index] && index > 0)
            otpRefs.current[index - 1]?.focus();
    };

    const handleOtpPaste = (e) => {
        e.preventDefault();
        const digits = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6).split('');
        const next   = [...otp];
        digits.forEach((d, i) => { next[i] = d; });
        setOtp(next);
        otpRefs.current[Math.min(digits.length, 5)]?.focus();
    };

    // ── Register ───────────────────────────────────────────────────────────────
    const handleRegisterSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        try {
            const res  = await fetch(`${API}/api/auth/send-otp`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ email: formData.email, name: formData.name }),
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                setResendSecs(60);
                setOtp(['', '', '', '', '', '']);
                setTimeout(() => {
                    setOtpStep(true);
                    setTimeout(() => otpRefs.current[0]?.focus(), 150);
                }, 400);
            } else {
                setError(data.message || 'Failed to send OTP.');
            }
        } catch {
            setError('Cannot connect to server.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleVerifyOtp = async (e) => {
        e.preventDefault();
        const code = otp.join('');
        if (code.length < 6) { setOtpError('Enter all 6 digits.'); return; }
        setIsLoading(true);
        setOtpError('');
        try {
            const res  = await fetch(`${API}/api/auth/verify-otp-register`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ ...formData, otp: code }),
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                setSuccessMsg('✅ Account created! Redirecting to sign in…');
                setTimeout(() => {
                    setSuccessMsg('');
                    setOtpStep(false);
                    setOtp(['', '', '', '', '', '']);
                    setFormData({ name: '', email: '', phone: '', password: '' });
                    setActivePanel('login');
                    setError('');
                }, 2000);
            } else {
                setOtpError(data.message || 'Invalid or expired OTP.');
                setOtp(['', '', '', '', '', '']);
                otpRefs.current[0]?.focus();
            }
        } catch {
            setOtpError('Cannot connect to server.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleResendOtp = async () => {
        if (resendSecs > 0) return;
        setOtpError('');
        setOtp(['', '', '', '', '', '']);
        setIsLoading(true);
        try {
            const res = await fetch(`${API}/api/auth/send-otp`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ email: formData.email, name: formData.name }),
            });
            if (res.ok) { setResendSecs(60); otpRefs.current[0]?.focus(); }
            else setOtpError('Failed to resend OTP.');
        } catch {
            setOtpError('Cannot connect to server.');
        } finally {
            setIsLoading(false);
        }
    };

    // ── Forgot password ────────────────────────────────────────────────────────
    const handleForgotSendOtp = async (e) => {
        e.preventDefault();
        setForgotLoading(true);
        setForgotError('');
        try {
            const res  = await fetch(`${API}/api/auth/forgot-password`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ email: forgotEmail }),
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                setForgotResendSecs(60);
                setForgotOtp(['', '', '', '', '', '']);
                setForgotStep('otp');
                setTimeout(() => forgotOtpRefs.current[0]?.focus(), 150);
            } else {
                setForgotError(data.message || 'Failed to send OTP.');
            }
        } catch {
            setForgotError('Cannot connect to server.');
        } finally {
            setForgotLoading(false);
        }
    };

    const handleForgotVerify = async (e) => {
        e.preventDefault();
        const code = forgotOtp.join('');
        if (code.length < 6)                 { setForgotError('Enter all 6 digits.');    return; }
        if (!newPassword)                    { setForgotError('Enter a new password.');   return; }
        if (newPassword !== confirmPassword) { setForgotError('Passwords do not match.'); return; }
        setForgotLoading(true);
        setForgotError('');
        try {
            const res  = await fetch(`${API}/api/auth/reset-password`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ email: forgotEmail, otp: code, new_password: newPassword }),
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                setForgotStep('done');
                setTimeout(() => {
                    setForgotStep(null);
                    setForgotEmail('');
                    setForgotOtp(['', '', '', '', '', '']);
                    setNewPassword('');
                    setConfirmPassword('');
                }, 2500);
            } else {
                setForgotError(data.message || 'Reset failed.');
                setForgotOtp(['', '', '', '', '', '']);
                forgotOtpRefs.current[0]?.focus();
            }
        } catch {
            setForgotError('Cannot connect to server.');
        } finally {
            setForgotLoading(false);
        }
    };

    const handleForgotResend = async () => {
        if (forgotResendSecs > 0) return;
        setForgotError('');
        setForgotOtp(['', '', '', '', '', '']);
        setForgotLoading(true);
        try {
            const res = await fetch(`${API}/api/auth/forgot-password`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ email: forgotEmail }),
            });
            if (res.ok) { setForgotResendSecs(60); forgotOtpRefs.current[0]?.focus(); }
            else { const data = await res.json(); setForgotError(data.message || 'Failed to resend OTP.'); }
        } catch {
            setForgotError('Cannot connect to server.');
        } finally {
            setForgotLoading(false);
        }
    };

    const handleForgotOtpChange = (index, value) => {
        if (!/^\d*$/.test(value)) return;
        const next = [...forgotOtp];
        next[index] = value.slice(-1);
        setForgotOtp(next);
        setForgotError('');
        if (value && index < 5) forgotOtpRefs.current[index + 1]?.focus();
    };

    const handleForgotOtpKeyDown = (index, e) => {
        if (e.key === 'Backspace' && !forgotOtp[index] && index > 0)
            forgotOtpRefs.current[index - 1]?.focus();
    };

    const handleForgotOtpPaste = (e) => {
        e.preventDefault();
        const digits = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6).split('');
        const next   = [...forgotOtp];
        digits.forEach((d, i) => { next[i] = d; });
        setForgotOtp(next);
        forgotOtpRefs.current[Math.min(digits.length, 5)]?.focus();
    };

    // ── Social login ───────────────────────────────────────────────────────────
    const handleRealSocialLogin = async (providerName) => {
        setIsLoading(true);
        setError('');
        let provider;
        if (providerName === 'Google')   provider = googleProvider;
        try {
            const result = await signInWithPopup(auth, provider);
            const user   = result.user;
            const res    = await fetch(`${API}/api/auth/social`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({
                    provider: providerName,
                    email:    user.email,
                    name:     user.displayName || 'NeuroStore User',
                    uid:      user.uid,
                }),
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                loginSuccess(data.user);
            } else {
                setError('Backend rejected the social login.');
            }
        } catch (err) {
            if (err.code === 'auth/popup-closed-by-user') {
                setError('Login canceled. Please complete the popup to sign in.');
            } else if (err.code === 'auth/unauthorized-domain') {
                setError('This domain is not authorized in Firebase Console.');
            } else {
                setError(`Failed to open ${providerName} login.`);
            }
        } finally {
            setIsLoading(false);
        }
    };

    // ── Standard login ─────────────────────────────────────────────────────────
    const handleLoginSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        const payload = signInMethod === 'email'
            ? { email: formData.email, password: formData.password }
            : { phone: formData.phone, password: formData.password };
        try {
            const res  = await fetch(`${API}/api/auth/login`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify(payload),
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                loginSuccess(data.user);
            } else {
                setError(data.message || 'Authentication failed.');
            }
        } catch {
            setError('Cannot connect to server. Ensure app.py is running.');
        } finally {
            setIsLoading(false);
        }
    };

    const SocialButtons = () => (
        <div className="auth-social-container">
            <button type="button" className="auth-social google"   onClick={() => handleRealSocialLogin('Google')}   aria-label="Login with Google">
                <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" alt="Google" />
            </button>
        </div>
    );

    return (
        <div className="auth-page-wrapper">

            {/* ── OTP / Forgot overlays ── */}
            {forgotStep && (
                <ForgotScreen
                    step={forgotStep}
                    email={forgotEmail}
                    otp={forgotOtp}
                    newPassword={newPassword}
                    confirmPassword={confirmPassword}
                    error={forgotError}
                    resendSecs={forgotResendSecs}
                    isLoading={forgotLoading}
                    otpRefs={forgotOtpRefs}
                    onEmailChange={setForgotEmail}
                    onEmailSubmit={handleForgotSendOtp}
                    onOtpChange={handleForgotOtpChange}
                    onOtpKeyDown={handleForgotOtpKeyDown}
                    onOtpPaste={handleForgotOtpPaste}
                    onNewPasswordChange={setNewPassword}
                    onConfirmPasswordChange={setConfirmPassword}
                    onVerify={handleForgotVerify}
                    onResend={handleForgotResend}
                    onClose={() => { setForgotStep(null); setForgotError(''); }}
                />
            )}

            {otpStep && (
                <OtpScreen
                    email={formData.email}
                    otp={otp}
                    otpError={otpError}
                    successMsg={successMsg}
                    resendSecs={resendSecs}
                    isLoading={isLoading}
                    otpRefs={otpRefs}
                    onOtpChange={handleOtpChange}
                    onOtpKeyDown={handleOtpKeyDown}
                    onOtpPaste={handleOtpPaste}
                    onVerify={handleVerifyOtp}
                    onResend={handleResendOtp}
                    onBack={() => { setOtpStep(false); setOtpError(''); setSuccessMsg(''); }}
                />
            )}

            {/* ── Main card ── */}
            <div className="auth-card">

                <p className="auth-breadcrumb">Home › Account</p>

                {/* ══════════════════════════════════════
                    LOGIN PANEL
                ══════════════════════════════════════ */}
                {activePanel === 'login' && (
                    <div className="auth-panel">
                        <h1 className="auth-page-title">Login</h1>

                        <SocialButtons />
                        <div className="auth-divider"><span>or</span></div>

                        {error && <div className="auth-error-msg">{error}</div>}

                        <div className="signin-method-toggle">
                            <button
                                type="button"
                                className={`toggle-btn ${signInMethod === 'email' ? 'active' : ''}`}
                                onClick={() => { setSignInMethod('email'); setError(''); setFormData(f => ({ ...f, email: '', phone: '' })); }}
                            >
                                ✉️ Email
                            </button>
                            <button
                                type="button"
                                className={`toggle-btn ${signInMethod === 'phone' ? 'active' : ''}`}
                                onClick={() => { setSignInMethod('phone'); setError(''); setFormData(f => ({ ...f, email: '', phone: '' })); }}
                            >
                                📱 Phone
                            </button>
                        </div>

                        <form onSubmit={handleLoginSubmit} className="auth-form">
                            <input
                                key={signInMethod}
                                type={signInMethod === 'email' ? 'email' : 'tel'}
                                name={signInMethod === 'email' ? 'email' : 'phone'}
                                placeholder={signInMethod === 'email' ? 'Email Address' : '+91 Phone Number'}
                                required
                                value={signInMethod === 'email' ? formData.email : formData.phone}
                                onChange={handleChange}
                                pattern={signInMethod === 'phone' ? '[+]?[0-9\\s\\-]{7,15}' : undefined}
                                autoFocus
                            />
                            <input
                                type="password"
                                name="password"
                                placeholder="Password"
                                required
                                value={formData.password}
                                onChange={handleChange}
                            />
                            <button className="auth-submit-btn" type="submit" disabled={isLoading}>
                                {isLoading ? 'Processing…' : 'Login'}
                            </button>
                        </form>

                        <button
                            type="button"
                            className="auth-text-link"
                            onClick={() => {
                                setForgotEmail(formData.email || '');
                                setForgotError('');
                                setForgotOtp(['', '', '', '', '', '']);
                                setNewPassword('');
                                setConfirmPassword('');
                                setForgotStep('email');
                            }}
                        >
                            Forgot your password?
                        </button>

                        <p className="auth-switch-text">
                            New Customer?{' '}
                            <button type="button" className="auth-link-btn" onClick={() => switchPanel('register')}>
                                Create account
                            </button>
                        </p>

                        <div className="guest-section">
                            <div className="guest-section-divider" />
                            <h2 className="guest-section-title">Continue as a guest</h2>
                            <button type="button" className="guest-continue-btn" onClick={() => switchPanel('guest')}>
                                Continue
                            </button>
                        </div>
                    </div>
                )}

                {/* ══════════════════════════════════════
                    REGISTER PANEL
                ══════════════════════════════════════ */}
                {activePanel === 'register' && (
                    <div className="auth-panel">
                        <h1 className="auth-page-title">Create Account</h1>

                        <SocialButtons />
                        <div className="auth-divider"><span>or use your email</span></div>

                        {error && <div className="auth-error-msg">{error}</div>}

                        <form onSubmit={handleRegisterSubmit} className="auth-form">
                            <input type="text"     name="name"     placeholder="Full Name"        required value={formData.name}     onChange={handleChange} />
                            <input type="email"    name="email"    placeholder="Email Address"    required value={formData.email}    onChange={handleChange} />
                            <input type="tel"      name="phone"    placeholder="+91 Phone Number"          value={formData.phone}    onChange={handleChange} pattern="[+]?[0-9\s\-]{7,15}" />
                            <input type="password" name="password" placeholder="Password"         required value={formData.password} onChange={handleChange} />
                            <button className="auth-submit-btn" type="submit" disabled={isLoading}>
                                {isLoading ? 'Sending OTP…' : 'Create Account'}
                            </button>
                        </form>

                        <p className="auth-switch-text">
                            Already have an account?{' '}
                            <button type="button" className="auth-link-btn" onClick={() => switchPanel('login')}>
                                Sign In
                            </button>
                        </p>

                        <div className="guest-section">
                            <div className="guest-section-divider" />
                            <h2 className="guest-section-title">Continue as a guest</h2>
                            <button type="button" className="guest-continue-btn" onClick={() => switchPanel('guest')}>
                                Continue
                            </button>
                        </div>
                    </div>
                )}

                {/* ══════════════════════════════════════
                    GUEST PANEL
                ══════════════════════════════════════ */}
                {activePanel === 'guest' && (
                    <div className="auth-panel auth-panel--guest">
                        <div className="guest-avatar">👤</div>
                        <h1 className="auth-page-title">Continue as Guest</h1>
                        <p className="guest-desc">
                            No account needed. Enter your email at checkout to
                            receive your order confirmation.
                        </p>

                        <button className="auth-submit-btn guest-checkout-btn" onClick={handleGuestCheckout}>
                            Continue to Checkout
                        </button>

                        <div className="guest-back-links">
                            <button type="button" className="auth-link-btn" onClick={() => switchPanel('login')}>
                                ← Back to Login
                            </button>
                            <span className="guest-or">or</span>
                            <button type="button" className="auth-link-btn" onClick={() => switchPanel('register')}>
                                Create an Account
                            </button>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
};

export default CustomerAuth;
