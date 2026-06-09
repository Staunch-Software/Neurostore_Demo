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
        userEmail,
    } = location.state || {};

    const [sdkReady, setSdkReady] = useState(false);
    const [loading,  setLoading]  = useState(false);
    const [payError, setPayError] = useState('');

    useEffect(() => { if (!amount) navigate('/'); }, [amount, navigate]);
    useEffect(() => { loadRazorpay().then(setSdkReady); }, []);

    const resolvedEmail = user?.email || userEmail || '';
    const resolvedName  = user?.name  || 'Customer';

    const verifyPayment = async (resp) => {
        try {
            const headers = { 'Content-Type': 'application/json' };
            if (resolvedEmail) {
                headers['User-Email'] = resolvedEmail;
            }

            const res = await fetch('https://www.neurostore.in/api/razorpay/verify', {
                method: 'POST',
                headers,
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
                        date: new Date().toLocaleDateString('en-IN', {
                            day: 'numeric', month: 'long', year: 'numeric'
                        }),
                    },
                });
            } else {
                setPayError(data.error || 'Payment verification failed');
                setLoading(false);
            }
        } catch (err) {
            console.error('Verify error:', err);
            setPayError('Server error during verification. Please contact support.');
            setLoading(false);
        }
    };

    const handlePayment = async () => {
        if (!sdkReady) return alert('Razorpay not loaded. Please refresh the page.');

        // Razorpay limit: ₹5,00,000 in test mode, ₹10,00,000 in live mode
        const MAX_AMOUNT = 500000;
        if (amount > MAX_AMOUNT) {
            setPayError(
                `Amount ₹${fmt(amount)} exceeds the maximum allowed limit of ₹${fmt(MAX_AMOUNT)}. ` +
                `Please contact us at info@neurostore.ai to complete this order manually.`
            );
            return;
        }

        setLoading(true);
        setPayError('');

        try {
            const res = await fetch('https://www.neurostore.in/api/razorpay/create-order', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ amount }),
            });

            if (!res.ok) {
                const errData = await res.json();
                setPayError(errData.error || `Server error: ${res.status}`);
                setLoading(false);
                return;
            }

            const data = await res.json();

            if (!data.id) {
                setPayError(data.error || 'Could not create payment order. Check Razorpay keys.');
                setLoading(false);
                return;
            }

            const options = {
                key:         'rzp_test_Se6aZrTcr0K9vV',
                amount:      data.amount,
                currency:    data.currency,
                name:        'NeuroStore',
                description: 'Purchase',
                order_id:    data.id,
                prefill: {
                    name:    resolvedName,
                    email:   resolvedEmail,
                    contact: phone || '',
                },
                handler: (resp) => verifyPayment(resp),
                theme:   { color: '#7c3aed', backdrop_color: 'rgba(30, 10, 60, 0.90)' }, // ← updated
                modal:   { ondismiss: () => setLoading(false) },
            };

            const rzp = new window.Razorpay(options);
            rzp.on('payment.failed', (resp) => {
                setPayError(resp.error?.description || 'Payment failed. Please try again.');
                setLoading(false);
            });
            rzp.open();

        } catch (err) {
            console.error('Payment error:', err);
            setPayError('Could not connect to payment server. Is backend running?');
            setLoading(false);
        }
    };

    const meta     = METHOD_META[activeMethod] || METHOD_META.card;
    const { Icon } = meta;
    const fmt      = (v) => v?.toLocaleString('en-IN', { maximumFractionDigits: 0 });

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
                        <span>{resolvedName}</span>
                    </div>
                    {resolvedEmail && (
                        <div className="payment-row">
                            <span>Email</span>
                            <span style={{ fontSize: '0.85rem', fontWeight: 400 }}>
                                {resolvedEmail}
                            </span>
                        </div>
                    )}
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
