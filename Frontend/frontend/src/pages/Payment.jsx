import React, { useEffect, useState, useContext } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ShopContext } from '../components/context/ShopContext';
import {
    ShieldCheck, CreditCard, Smartphone,
    Building2, Wallet, ArrowLeft
} from 'lucide-react';
import './Payment.css';

const loadRazorpay = () =>
    new Promise((resolve) => {
        if (window.Razorpay) return resolve(true);
        const s = document.createElement('script');
        s.src = 'https://checkout.razorpay.com/v1/checkout.js';
        s.onload = () => resolve(true);
        s.onerror = () => resolve(false);
        document.body.appendChild(s);
    });

const METHOD_META = {
    card:    { label: 'Card Payment',   Icon: CreditCard  },
    netbank: { label: 'Net Banking',    Icon: Building2   },
    upi:     { label: 'UPI Payment',    Icon: Smartphone  },
    wallet:  { label: 'Wallet Payment', Icon: Wallet      },
};

const Payment = () => {
    const location = useLocation();
    const navigate  = useNavigate();
    const { user, clearCart, products } = useContext(ShopContext);

    const {
        amount,
        address,
        items,
        phone,
        activeMethod,
    } = location.state || {};

    const [sdkReady, setSdkReady] = useState(false);
    const [loading,  setLoading]  = useState(false);
    const [payError, setPayError] = useState('');

    useEffect(() => { if (!amount) navigate('/'); }, [amount, navigate]);
    useEffect(() => { loadRazorpay().then(setSdkReady); }, []);

    const verifyPayment = async (resp) => {
        try {
            const res = await fetch('http://localhost:5000/api/razorpay/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'User-Email': user.email,
                },
                body: JSON.stringify({
                    ...resp,
                    items,
                    total:  amount,
                    address,
                    method: activeMethod,
                }),
            });
            const data = await res.json();
            if (data.success) {
                clearCart();
                const orderedItems = products
                    .filter(p => items[p.id] > 0)
                    .map(p => ({ name: p.name, qty: items[p.id], price: p.price }));
                navigate('/order-success', {
                    state: {
                        orderId:    data.order_id,
                        paymentId:  resp.razorpay_payment_id,
                        method:     activeMethod,
                        orderItems: orderedItems,
                        total:      amount,
                        address,
                        date: new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }),
                    },
                });
            } else {
                setPayError('Payment verification failed');
                setLoading(false);
            }
        } catch {
            setPayError('Server error during verification');
            setLoading(false);
        }
    };

    const handlePayment = async () => {
        if (!sdkReady) return alert('Razorpay not loaded');

        setLoading(true);
        setPayError('');

        try {
            const res = await fetch('http://localhost:5000/api/razorpay/create-order', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ amount }),
            });

            const data = await res.json();

            if (!data.id) {
                setPayError(data.error || JSON.stringify(data));
                setLoading(false);
                return;
            }

            const options = {
                key:         'rzp_test_Se6aZrTcr0K9vV',
                amount:      amount * 100,
                currency:    'INR',
                name:        'NeuroStore',
                description: 'Purchase',
                order_id:    data.id,
                prefill: {
                    name:    user?.name  || '',
                    email:   user?.email || '',
                    contact: phone       || '',
                },
                handler: (resp) => verifyPayment(resp),
                theme:   { color: '#6366f1', backdrop_color: 'rgba(15, 10, 45, 0.88)' },
                modal:   { ondismiss: () => setLoading(false) },
            };

            const rzp = new window.Razorpay(options);
            rzp.on('payment.failed', (resp) => {
                setPayError(resp.error?.description || 'Payment failed');
                setLoading(false);
            });
            rzp.open();

        } catch (err) {
            setPayError('Something went wrong: ' + err.message);
            setLoading(false);
        }
    };

    const meta   = METHOD_META[activeMethod] || METHOD_META.card;
    const { Icon } = meta;
    const fmt    = (v) => v?.toLocaleString('en-IN', { maximumFractionDigits: 0 });

    return (
        <div className="payment-page-wrapper">
            <div className="payment-card">

                {/* ── Header ── */}
                <div className="payment-header">
                    <div className="payment-header-icon">
                        <Icon size={32} color="#818cf8" />
                    </div>
                    <h1>Complete Payment</h1>
                    <p>Review your order and confirm</p>
                </div>

                {/* ── Method badge ── */}
                <div className="payment-method-badge">
                    <Icon size={14} />
                    {meta.label}
                </div>

                {/* ── Summary ── */}
                <div className="payment-summary">
                    <div className="payment-row">
                        <span>Customer</span>
                        <span>{user?.name}</span>
                    </div>
                    <div className="payment-row">
                        <span>Address</span>
                        <span style={{ fontSize: '0.85rem', fontWeight: 400, lineHeight: 1.5 }}>
                            {address}
                        </span>
                    </div>
                    <div className="pay-divider" />
                    <div className="payment-row payment-row--total">
                        <span>Total Payable</span>
                        <span>₹{fmt(amount)}</span>
                    </div>
                </div>

                {/* ── Error ── */}
                {payError && (
                    <div className="sdk-error">{payError}</div>
                )}

                {/* ── Pay button ── */}
                <button
                    className="pay-now-btn"
                    onClick={handlePayment}
                    disabled={loading || !sdkReady}
                >
                    {loading ? 'Processing...' : `Pay ₹${fmt(amount)}`}
                </button>

                {/* ── Secure badge ── */}
                <div className="secure-badge">
                    <ShieldCheck size={14} />
                    Secure Payment powered by Razorpay
                </div>

                {/* ── Back ── */}
                <button className="back-btn-pay" onClick={() => navigate(-1)}>
                    <ArrowLeft size={14} /> Back to Checkout
                </button>

            </div>
        </div>
    );
};

export default Payment;