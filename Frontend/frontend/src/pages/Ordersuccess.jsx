import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
    CheckCircle, Package, ArrowRight, Home,
    Receipt, MapPinned, Clock, BadgeCheck,
    CreditCard, Smartphone, Building2, Wallet, ShieldCheck, LogIn, X
} from 'lucide-react';
import './Ordersuccess.css';

const METHOD_LABEL = {
    card:    'Credit / Debit Card',
    netbank: 'Net Banking',
    upi:     'UPI',
    wallet:  'Wallet',
    Online:  'Online Payment',
};

const METHOD_ICON = {
    card:    CreditCard,
    netbank: Building2,
    upi:     Smartphone,
    wallet:  Wallet,
};

const OrderSuccess = () => {
    const navigate  = useNavigate();
    const location  = useLocation();
    const state     = location.state || {};

    const [showLoginPrompt, setShowLoginPrompt] = useState(false);

    const {
        orderId,
        paymentId,
        method,
        orderItems = [],
        total      = 0,
        address    = '',
        date       = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }),
    } = state;

    const fmt        = (v) => Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 });
    const MethodIcon = METHOD_ICON[method] || CreditCard;
    const hasData    = orderItems.length > 0;

    const handleTrackOrder = () => {
        const user = JSON.parse(localStorage.getItem('neuroUser') || 'null'); // ← fixed key
        if (user) {
            navigate('/profile');
        } else {
            setShowLoginPrompt(true);
        }
    };

    return (
        <div className="os-wrapper">
            <div className="os-blob os-blob--green" />
            <div className="os-blob os-blob--purple" />

            {/* ── Login Prompt Modal ── */}
            {showLoginPrompt && (
                <div className="os-modal-overlay" onClick={() => setShowLoginPrompt(false)}>
                    <div className="os-modal" onClick={(e) => e.stopPropagation()}>
                        <button className="os-modal-close" onClick={() => setShowLoginPrompt(false)}>
                            <X size={18} />
                        </button>
                        <div className="os-modal-icon">
                            <LogIn size={36} color="#7c3aed" strokeWidth={1.8} />
                        </div>
                        <h2 className="os-modal-title">Login Required</h2>
                        <p className="os-modal-text">
                            You need to be logged in to track your order.<br />
                            Please sign in to view your order history.
                        </p>
                        <div className="os-modal-actions">
                            <button
                                className="os-btn os-btn--primary"
                                onClick={() => navigate('/login', { state: { redirect: '/profile' } })}
                            >
                                <LogIn size={15} /> Go to Login
                            </button>
                            <button
                                className="os-btn os-btn--ghost"
                                onClick={() => setShowLoginPrompt(false)}
                            >
                                Maybe Later
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className={`os-card ${hasData ? 'os-card--wide' : ''}`}>

                {/* ── Header ── */}
                <div className="os-icon-ring">
                    <CheckCircle size={56} color="#10b981" strokeWidth={1.8} />
                </div>
                <h1 className="os-title">Payment Successful!</h1>
                <p className="os-subtitle">
                    Thank you for shopping with <strong>NeuroStore</strong>.<br />
                    Your order has been confirmed and is being processed.
                </p>

                {orderId && (
                    <div className="os-order-id-row">
                        <span className="os-order-id">Order &nbsp;#<strong>{orderId}</strong></span>
                        {paymentId && (
                            <span className="os-payment-id">
                                <ShieldCheck size={12} /> Txn: {paymentId.slice(0, 18)}…
                            </span>
                        )}
                    </div>
                )}

                {/* ── Detail grid (only if state was passed) ── */}
                {hasData && (
                    <div className="os-detail-grid">

                        {/* Order summary */}
                        <div className="os-detail-card">
                            <div className="os-detail-title"><Receipt size={14} /> Order Summary</div>
                            <div className="os-items-list">
                                {orderItems.map((item, i) => (
                                    <div key={i} className="os-item-row">
                                        <span className="os-item-name">
                                            {item.name}
                                            <span className="os-item-qty"> ×{item.qty}</span>
                                        </span>
                                        <span className="os-item-price">₹{fmt(item.price * item.qty)}</span>
                                    </div>
                                ))}
                            </div>
                            <div className="os-total-row">
                                <span>Total paid (incl. 18% GST)</span>
                                <span className="os-total-amount">₹{fmt(total)}</span>
                            </div>
                            <div className="os-method-badge">
                                <MethodIcon size={13} />
                                {METHOD_LABEL[method] || 'Online Payment'} &nbsp;·&nbsp; Paid
                            </div>
                        </div>

                        {/* Delivery details */}
                        <div className="os-detail-card">
                            <div className="os-detail-title"><MapPinned size={14} /> Delivery Details</div>
                            <p className="os-address-text">{address}</p>
                            <div className="os-delivery-info">
                                <div className="os-delivery-row">
                                    <Clock size={13} />
                                    <span>Estimated delivery: <strong>3 – 7 business days</strong></span>
                                </div>
                                <div className="os-delivery-row">
                                    <BadgeCheck size={13} />
                                    <span>Order placed on <strong>{date}</strong></span>
                                </div>
                                <div className="os-delivery-row">
                                    <ShieldCheck size={13} />
                                    <span>Payment secured by Razorpay</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* ── Fallback info strip (no state) ── */}
                {!hasData && (
                    <div className="os-info-strip">
                        <Package size={16} />
                        <span>Your AI hardware will be dispatched within 3–5 business days.</span>
                    </div>
                )}

                {/* ── Actions ── */}
                <div className="os-actions">
                    <button className="os-btn os-btn--primary" onClick={handleTrackOrder}>
                        <Package size={16} /> Track My Order <ArrowRight size={15} />
                    </button>
                    <button className="os-btn os-btn--ghost" onClick={() => navigate('/')}>
                        <Home size={15} /> Back to Home
                    </button>
                </div>

            </div>
        </div>
    );
};

export default OrderSuccess;