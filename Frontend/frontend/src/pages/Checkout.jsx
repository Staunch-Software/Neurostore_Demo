import React, { useState, useEffect, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShopContext } from '../components/context/ShopContext';
import {
    ArrowLeft, CreditCard, Truck, ShieldCheck,
    CheckCircle, Package, Smartphone, Building2,
    Wallet, Lock, ChevronDown, ChevronUp, MapPin, BookMarked,
    BadgeCheck, Clock, MapPinned, Receipt
} from 'lucide-react';
import './Checkout.css';

const PAYMENT_OPTIONS = [
    {
        id:      'card',
        label:   'Card',
        sub:     'Credit / Debit / Prepaid',
        Icon:    CreditCard,
        type:    'secure',
        MsgIcon: Lock,
        title:   'Secure Card Payment',
        message: 'Your card number, CVV and expiry are entered directly inside the Razorpay secure popup. We never see or store any card details — this is required by PCI DSS compliance.',
    },
    {
        id:      'netbank',
        label:   'Net Banking',
        sub:     'All major banks supported',
        Icon:    Building2,
        type:    'info',
        MsgIcon: Building2,
        title:   'Pay via Net Banking',
        message: 'Click "Proceed to Pay" — the Razorpay popup will open where you can choose from all major banks including SBI, HDFC, ICICI, Axis, Kotak and more.',
    },
    {
        id:      'upi',
        label:   'UPI',
        sub:     'Google Pay, PhonePe, BHIM & more',
        Icon:    Smartphone,
        type:    'info',
        MsgIcon: Smartphone,
        title:   'Pay via UPI',
        message: 'Click "Proceed to Pay" — the Razorpay popup will open where you can select Google Pay, PhonePe, BHIM, Paytm, or enter any UPI ID directly.',
    },
    {
        id:      'wallet',
        label:   'Wallet',
        sub:     'Paytm, Mobikwik, Amazon Pay & more',
        Icon:    Wallet,
        type:    'info',
        MsgIcon: Wallet,
        title:   'Pay via Wallet',
        message: 'Click "Proceed to Pay" — the Razorpay popup will open where you can choose from Paytm, Mobikwik, Amazon Pay, Freecharge, Ola Money and more.',
    },
];

const COD_OPTION = {
    id:      'cod',
    label:   'Cash on Delivery',
    sub:     'Pay when your order arrives',
    Icon:    Truck,
    type:    'warning',
    MsgIcon: Truck,
    title:   'Cash on Delivery',
    message: 'Your order will be placed immediately. Please keep exact change ready when the delivery arrives.',
};

const Checkout = () => {
    const { cartItems, products, getTotalCartAmount, user, clearCart } = useContext(ShopContext);
    const totalAmount = getTotalCartAmount();
    const navigate    = useNavigate();

    const [loading,      setLoading]      = useState(false);
    const [orderSuccess, setOrderSuccess] = useState(false);
    const [orderData,    setOrderData]    = useState(null);
    const [activeTab,    setActiveTab]    = useState('card');
    const [sameAddress,  setSameAddress]  = useState(false);

    const [currentAddr, setCurrentAddr] = useState({
        address: '',
        city:    '',
        state:   '',
        zip:     '',
    });

    const [formData, setFormData] = useState({
        address: '',
        city:    '',
        state:   '',
        zip:     '',
        phone:   user?.phone || '',
    });

    // Load saved addresses → auto-fill current address from default
    React.useEffect(() => {
        if (!user?.email) return;
        fetch('http://localhost:5000/api/addresses', { headers: { 'User-Email': user.email } })
            .then(r => r.json())
            .then(data => {
                const def = data.find(a => a.is_default) || data[0];
                if (def) {
                    const filled = { address: def.street, city: def.city, state: def.state, zip: def.zip };
                    setCurrentAddr(filled);
                    // also pre-fill shipping with the same
                    setFormData(prev => ({ ...prev, ...filled }));
                    setSameAddress(true);
                }
            })
            .catch(() => {});
    }, [user]);

    const handleCurrentAddrChange = (e) => {
        const updated = { ...currentAddr, [e.target.name]: e.target.value };
        setCurrentAddr(updated);
        if (sameAddress) {
            setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
        }
    };

    const handleSameAddressToggle = (e) => {
        const checked = e.target.checked;
        setSameAddress(checked);
        if (checked) {
            setFormData(prev => ({
                ...prev,
                address: currentAddr.address,
                city:    currentAddr.city,
                state:   currentAddr.state,
                zip:     currentAddr.zip,
            }));
        } else {
            // Clear shipping fields when unchecked
            setFormData(prev => ({
                ...prev,
                address: '',
                city:    '',
                state:   '',
                zip:     '',
            }));
        }
    };

    if (totalAmount <= 0 && !orderSuccess) {
        return (
            <div className="checkout-empty">
                <Package size={64} color="#ccc" />
                <h2>Your cart is empty</h2>
                <Link to="/products" className="back-btn">Return to Shop</Link>
            </div>
        );
    }
    if (!user) {
        return (
            <div className="checkout-empty">
                <Package size={64} color="#ccc" />
                <h2>Please log in to continue</h2>
                <Link to="/login" className="back-btn">Login</Link>
            </div>
        );
    }

    const handleInputChange = (e) =>
        setFormData({ ...formData, [e.target.name]: e.target.value });

    const finalAmount = totalAmount * 1.18;
    const fullAddress = `${formData.address}, ${formData.city}, ${formData.state} - ${formData.zip}`;
    const orderItems  = {};
    products.forEach(p => { if (cartItems[p.id] > 0) orderItems[p.id] = cartItems[p.id]; });

    const autoSaveAddress = async () => {
        if (!currentAddr.address || !currentAddr.city || !currentAddr.state || !currentAddr.zip) return;
        try {
            await fetch('http://localhost:5000/api/addresses', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json', 'User-Email': user.email },
                body: JSON.stringify({
                    label:      'Home',
                    name:       user.name || '',
                    street:     currentAddr.address,
                    city:       currentAddr.city,
                    state:      currentAddr.state,
                    zip:        currentAddr.zip,
                    country:    'India',
                    is_default: true,
                }),
            });
        } catch {}
    };

    const handlePlaceOrder = async (e) => {
        e.preventDefault();
        setLoading(true);
        await autoSaveAddress();

        if (activeTab === 'cod') {
            try {
                const res  = await fetch('http://localhost:5000/api/orders', {
                    method:  'POST',
                    headers: { 'Content-Type': 'application/json', 'User-Email': user.email },
                    body:    JSON.stringify({
                        items: orderItems, total: finalAmount, address: fullAddress, payment: 'COD',
                    }),
                });
                const data = await res.json();
                if (res.ok && data.status === 'success') {
                    const orderedItems = products
                        .filter(p => cartItems[p.id] > 0)
                        .map(p => ({ name: p.name, qty: cartItems[p.id], price: p.price }));
                    setOrderData({
                        id:      data.order_id,
                        items:   orderedItems,
                        total:   finalAmount,
                        address: fullAddress,
                        date:    new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }),
                    });
                    clearCart();
                    setOrderSuccess(true);
                } else {
                    alert(data.message || 'Failed to place order. Please try again.');
                }
            } catch {
                alert('Failed to place order. Please try again.');
            } finally {
                setLoading(false);
            }
            return;
        }

        navigate('/payment', {
            state: {
                amount:       finalAmount,
                address:      fullAddress,
                items:        orderItems,
                phone:        formData.phone,
                activeMethod: activeTab,
            },
        });
        setLoading(false);
    };

    if (orderSuccess && orderData) {
        const fmt = (v) => Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 });
        return (
            <div className="checkout-page-wrapper">
                <div className="cod-success-wrapper">
                    <div className="cod-success-header">
                        <div className="cod-success-icon-ring">
                            <BadgeCheck size={40} color="#10b981" />
                        </div>
                        <h1>Order Confirmed!</h1>
                        <p>Thank you, <strong>{user.name}</strong>. Your order has been placed successfully.</p>
                        <div className="cod-order-id">Order ID &nbsp;#<strong>{orderData.id}</strong></div>
                    </div>
                    <div className="cod-success-grid">
                        <div className="cod-success-card">
                            <div className="cod-card-title"><Receipt size={15} /> Order Summary</div>
                            <div className="cod-items-list">
                                {orderData.items.map((item, i) => (
                                    <div key={i} className="cod-item-row">
                                        <span className="cod-item-name">{item.name} <span className="cod-item-qty">×{item.qty}</span></span>
                                        <span className="cod-item-price">₹{fmt(item.price * item.qty)}</span>
                                    </div>
                                ))}
                            </div>
                            <div className="cod-total-row">
                                <span>Total (incl. 18% GST)</span>
                                <span className="cod-total-amount">₹{fmt(orderData.total)}</span>
                            </div>
                            <div className="cod-payment-badge">
                                <Truck size={13} /> Cash on Delivery &nbsp;·&nbsp; Pay when delivered
                            </div>
                        </div>
                        <div className="cod-success-card">
                            <div className="cod-card-title"><MapPinned size={15} /> Delivery Details</div>
                            <p className="cod-address-text">{orderData.address}</p>
                            <div className="cod-delivery-info">
                                <div className="cod-delivery-row">
                                    <Clock size={14} />
                                    <span>Estimated delivery: <strong>3 – 7 business days</strong></span>
                                </div>
                                <div className="cod-delivery-row">
                                    <BadgeCheck size={14} />
                                    <span>Order placed on <strong>{orderData.date}</strong></span>
                                </div>
                                <div className="cod-delivery-row">
                                    <ShieldCheck size={14} />
                                    <span>Keep exact change ready at the time of delivery</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="cod-success-actions">
                        <button className="cod-btn-primary" onClick={() => navigate('/profile')}>
                            <Package size={16} /> Track My Order
                        </button>
                        <button className="cod-btn-secondary" onClick={() => navigate('/products')}>
                            Continue Shopping
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    const allOptions = [...PAYMENT_OPTIONS, COD_OPTION];

    const btnLabel = loading
        ? 'Processing...'
        : activeTab === 'cod'
            ? 'Place Order (Cash on Delivery)'
            : `Proceed to Pay ₹${finalAmount.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

    const PayOption = ({ opt }) => {
        const isActive = activeTab === opt.id;
        return (
            <div className={`pay-option ${isActive ? 'pay-option--open' : ''}`}>
                <button
                    type="button"
                    className="pay-option-header"
                    onClick={() => setActiveTab(opt.id)}
                >
                    <div className="pay-option-left">
                        <div className={`pay-option-radio ${isActive ? 'sel' : ''}`} />
                        <opt.Icon size={18} className="pay-option-icon" />
                        <div className="pay-option-text">
                            <span className="pay-option-label">{opt.label}</span>
                            <span className="pay-option-sub">{opt.sub}</span>
                        </div>
                    </div>
                    {isActive
                        ? <ChevronUp size={16} className="pay-option-chevron" />
                        : <ChevronDown size={16} className="pay-option-chevron" />}
                </button>

                {isActive && (
                    <div className={`pm-message pm-message--${opt.type}`}>
                        <opt.MsgIcon size={13} className="pm-message-icon" />
                        <span className="pm-message-text">{opt.message}</span>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="checkout-page-wrapper">
            <div className="checkout-container">
                <button onClick={() => navigate(-1)} className="back-link">
                    <ArrowLeft size={16} /> Back to Cart
                </button>
                <h1 className="checkout-title">Checkout</h1>

                <div className="checkout-grid">
                    <div className="checkout-form-side">
                        <form onSubmit={handlePlaceOrder}>

                            {/* ── Current Address ── */}
                            <section className="form-section">
                                <div className="section-header">
                                    <MapPin size={20} />
                                    <h2>Current Address</h2>
                                </div>
                                <div className="input-group">
                                    <label>Street Address</label>
                                    <input name="address" value={currentAddr.address}
                                        onChange={handleCurrentAddrChange} placeholder="Door No, Street name" />
                                </div>
                                <div className="input-row">
                                    <div className="input-group">
                                        <label>City</label>
                                        <input name="city" value={currentAddr.city}
                                            onChange={handleCurrentAddrChange} placeholder="e.g. Chennai" />
                                    </div>
                                    <div className="input-group">
                                        <label>State</label>
                                        <input name="state" value={currentAddr.state}
                                            onChange={handleCurrentAddrChange} placeholder="Tamil Nadu" />
                                    </div>
                                </div>
                                <div className="input-group">
                                    <label>ZIP / Postal Code</label>
                                    <input name="zip" value={currentAddr.zip}
                                        onChange={handleCurrentAddrChange} placeholder="600001" />
                                </div>
                            </section>

                            {/* ── Same as current address checkbox ── */}
                            <div className="same-address-row">
                                <label className="same-address-label">
                                    <input
                                        type="checkbox"
                                        className="same-address-checkbox"
                                        checked={sameAddress}
                                        onChange={handleSameAddressToggle}
                                    />
                                    <span className="same-address-text">Shipping address is same as current address</span>
                                </label>
                            </div>

                            {/* ── Shipping ── */}
                            <section className="form-section">
                                <div className="section-header">
                                    <Truck size={20} />
                                    <h2>Shipping Address</h2>
                                </div>
                                <div className="input-group">
                                    <label>Street Address</label>
                                    <input name="address" required value={formData.address}
                                        onChange={handleInputChange} placeholder="Door No, Street name"
                                        readOnly={sameAddress} className={sameAddress ? 'input-readonly' : ''} />
                                </div>
                                <div className="input-row">
                                    <div className="input-group">
                                        <label>City</label>
                                        <input name="city" required value={formData.city}
                                            onChange={handleInputChange} placeholder="e.g. Chennai"
                                            readOnly={sameAddress} className={sameAddress ? 'input-readonly' : ''} />
                                    </div>
                                    <div className="input-group">
                                        <label>State</label>
                                        <input name="state" required value={formData.state}
                                            onChange={handleInputChange} placeholder="Tamil Nadu"
                                            readOnly={sameAddress} className={sameAddress ? 'input-readonly' : ''} />
                                    </div>
                                </div>
                                <div className="input-row">
                                    <div className="input-group">
                                        <label>ZIP / Postal Code</label>
                                        <input name="zip" required value={formData.zip}
                                            onChange={handleInputChange} placeholder="600001"
                                            readOnly={sameAddress} className={sameAddress ? 'input-readonly' : ''} />
                                    </div>
                                    <div className="input-group">
                                        <label>Phone Number</label>
                                        <input name="phone" required value={formData.phone}
                                            onChange={handleInputChange} placeholder="+91 00000 00000" />
                                    </div>
                                </div>
                            </section>

                            {/* ── Payment accordion ── */}
                            <section className="form-section">
                                <div className="section-header">
                                    <CreditCard size={20} />
                                    <h2>Payment Method</h2>
                                </div>
                                <div className="pay-options-list">
                                    {allOptions.map(opt => (
                                        <PayOption key={opt.id} opt={opt} />
                                    ))}
                                </div>
                            </section>

                            <button type="submit" className="place-order-btn" disabled={loading}>
                                {btnLabel}
                            </button>
                        </form>
                    </div>

                    {/* ── Summary Side ── */}
                    <div className="checkout-summary-side">
                        <div className="summary-card">
                            <h3>Order Summary</h3>
                            <div className="summary-items">
                                {products.map(p => cartItems[p.id] > 0 && (
                                    <div key={p.id} className="summary-item-row">
                                        <span>{p.name} (x{cartItems[p.id]})</span>
                                        <span>₹{(p.price * cartItems[p.id]).toLocaleString()}</span>
                                    </div>
                                ))}
                            </div>
                            <div className="summary-divider" />
                            <div className="summary-sub">
                                <span>Subtotal</span>
                                <span>₹{totalAmount.toLocaleString()}</span>
                            </div>
                            <div className="summary-sub">
                                <span>Tax (18%)</span>
                                <span>₹{(totalAmount * 0.18).toLocaleString()}</span>
                            </div>
                            <div className="summary-total">
                                <span>Estimated Total</span>
                                <span>₹{finalAmount.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                            </div>
                            <div className="selected-method-preview">
                                {allOptions.find(o => o.id === activeTab)?.label}
                            </div>
                            <div className="secure-badge">
                                <ShieldCheck size={14} /> Encrypted Secure Checkout
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Checkout;