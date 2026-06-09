import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const AdminLogin = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setError('');

        try {
            const response = await fetch("https://www.neurostore.in/api/admin/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                // Save the "VIP Pass" to the browser's local storage
                localStorage.setItem('adminToken', data.token);
                // Teleport the admin into the hidden dashboard
                navigate('/admin/dashboard');
            } else {
                setError(data.message || "Invalid credentials");
            }
        } catch (err) {
            setError("Cannot connect to backend server.");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a', fontFamily: 'Inter, sans-serif' }}>
            <div style={{ background: '#1e293b', padding: '40px', borderRadius: '15px', width: '100%', maxWidth: '400px', boxShadow: '0 20px 40px rgba(0,0,0,0.4)' }}>
                <div style={{ textAlign: 'center', marginBottom: '30px' }}>
                    <h2 style={{ color: 'white', margin: 0, fontSize: '24px' }}>NeuroStore Admin</h2>
                    <p style={{ color: '#94a3b8', fontSize: '14px', marginTop: '5px' }}>Authorized Personnel Only</p>
                </div>

                <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    <div>
                        <label style={{ color: '#cbd5e1', fontSize: '13px', fontWeight: '600', marginBottom: '5px', display: 'block' }}>Username</label>
                        <input
                            type="text"
                            required
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid #334155', background: '#0f172a', color: 'white', outline: 'none' }}
                        />
                    </div>
                    <div>
                        <label style={{ color: '#cbd5e1', fontSize: '13px', fontWeight: '600', marginBottom: '5px', display: 'block' }}>Password</label>
                        <input
                            type="password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid #334155', background: '#0f172a', color: 'white', outline: 'none' }}
                        />
                    </div>

                    {error && <div style={{ color: '#ef4444', fontSize: '13px', textAlign: 'center', background: 'rgba(239, 68, 68, 0.1)', padding: '10px', borderRadius: '8px' }}>{error}</div>}

                    <button
                        type="submit"
                        disabled={isSubmitting}
                        style={{ background: '#3b82f6', color: 'white', padding: '12px', borderRadius: '8px', border: 'none', fontWeight: 'bold', cursor: 'pointer', marginTop: '10px' }}
                    >
                        {isSubmitting ? 'Verifying...' : 'Access Terminal'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default AdminLogin;
