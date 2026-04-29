import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { auth } from '../firebase';
import { signOut } from 'firebase/auth';
import { ShopContext } from '../components/context/ShopContext';
import {
    LayoutDashboard, Package, MapPin, Heart,
    Settings, LogOut, Search, Plus, CreditCard,
    RefreshCw, ShoppingBag, CheckCircle2, Truck,
    Clock, CircleDot, ChevronDown, ChevronUp
} from 'lucide-react';
import './Profile.css';

// ── Helpers ────────────────────────────────────────────────────────────────────
const payLabel = (m) => ({
    COD: 'Cash on Delivery', Online: 'Online',
    upi: 'UPI', card: 'Card', netbank: 'Net Banking', wallet: 'Wallet',
}[m] || m || 'Online');

const STATUS_CONFIG = {
    Confirmed:  { label: 'Confirmed',  color: '#818cf8', bg: 'rgba(129,140,248,0.1)', Icon: CircleDot,    step: 1 },
    Processing: { label: 'Processing', color: '#f59e0b', bg: 'rgba(245,158,11,0.1)',  Icon: Clock,        step: 2 },
    Shipped:    { label: 'Shipped',    color: '#3b82f6', bg: 'rgba(59,130,246,0.1)',   Icon: Truck,        step: 3 },
    Delivered:  { label: 'Delivered',  color: '#10b981', bg: 'rgba(16,185,129,0.1)',   Icon: CheckCircle2, step: 4 },
};

const STEPS = ['Confirmed', 'Processing', 'Shipped', 'Delivered'];

// ── Order Card ─────────────────────────────────────────────────────────────────
const OrderCard = ({ order, products, onNavigate }) => {
    const [expanded, setExpanded] = useState(false);
    const cfg = STATUS_CONFIG[order.status] || STATUS_CONFIG.Confirmed;
    const currentStep = cfg.step;

    let orderLines = [];
    try {
        const parsed = typeof order.items === 'string'
            ? JSON.parse(order.items.replace(/'/g, '"'))
            : order.items;
        orderLines = Object.entries(parsed).map(([id, qty]) => {
            const product = products?.find(p => String(p.id) === String(id));
            return {
                id,
                qty:   Number(qty),
                name:  product?.name  || `Product #${id}`,
                price: product?.price || 0,
                image: product?.image || null,
            };
        });
    } catch {}

    const fmt     = (v) => Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 });
    const visible = expanded ? orderLines : orderLines.slice(0, 2);

    return (
        <div className="oc">

            {/* ── Header row ── */}
            <div className="oc-head">
                <div className="oc-head-left">
                    <span className="oc-id">#{order.id}</span>
                    <span className="oc-chip">{order.created_at?.split(' ')[0] || '—'}</span>
                    <span className="oc-chip">{payLabel(order.payment)}</span>
                </div>
                <div className="oc-head-right">
                    <span className="oc-status" style={{ background: cfg.bg, color: cfg.color }}>
                        <cfg.Icon size={11} /> {cfg.label}
                    </span>
                    <span className="oc-total">₹{fmt(order.total)}</span>
                </div>
            </div>

            {/* ── Body: images + items ── */}
            <div className="oc-body">

                {/* Images column – primary product image fills left half */}
                <div className="oc-images">
                    {orderLines[0]?.image
                        ? <img src={orderLines[0].image} alt={orderLines[0].name}
                            className="oc-img-primary"
                            onError={e => { e.target.style.display = 'none'; }} />
                        : <div className="oc-img-placeholder"><Package size={44} color="hsl(240,20%,60%)" /></div>
                    }
                    {orderLines.length > 1 && (
                        <span className="oc-img-count">
                            +{orderLines.length - 1} item{orderLines.length > 2 ? 's' : ''}
                        </span>
                    )}
                </div>

                {/* Items + tracker column */}
                <div className="oc-details">

                    {/* Item rows */}
                    <div className="oc-items">
                        {visible.map(({ id, name, qty, price }) => (
                            <div key={id} className="oc-item">
                                <span className="oc-item-name">{name}</span>
                                <span className="oc-item-meta">×{qty} &nbsp;·&nbsp; ₹{fmt(price * qty)}</span>
                            </div>
                        ))}
                        {orderLines.length > 2 && (
                            <button className="oc-expand" onClick={() => setExpanded(e => !e)}>
                                {expanded
                                    ? <><ChevronUp size={12} /> less</>
                                    : <><ChevronDown size={12} /> +{orderLines.length - 2} more</>}
                            </button>
                        )}
                    </div>

                    {/* Compact tracker */}
                    <div className="oc-tracker">
                        {STEPS.map((step, i) => {
                            const done   = i + 1 <= currentStep;
                            const active = i + 1 === currentStep;
                            const c      = STATUS_CONFIG[step];
                            return (
                                <React.Fragment key={step}>
                                    <div className={`oc-t-step ${done ? 'done' : ''} ${active ? 'active' : ''}`}>
                                        <div className="oc-t-dot"
                                            style={done ? { background: c.color, borderColor: c.color } : {}}>
                                            {done && <c.Icon size={14} color="#fff" />}
                                        </div>
                                        <span className="oc-t-label">{step}</span>
                                    </div>
                                    {i < STEPS.length - 1 && (
                                        <div className={`oc-t-line ${i + 1 < currentStep ? 'done' : ''}`} />
                                    )}
                                </React.Fragment>
                            );
                        })}
                    </div>

                </div>
            </div>

            {/* ── Footer ── */}
            <div className="oc-foot">
                <span className="oc-address">📍 {order.address || '—'}</span>
                {order.status === 'Delivered'
                    ? <button className="oc-btn" onClick={() => onNavigate('/products')}>Buy Again</button>
                    : <button className="oc-btn">Track Order</button>
                }
            </div>

        </div>
    );
};

// ── Main Profile ───────────────────────────────────────────────────────────────
const Profile = () => {
    const navigate = useNavigate();
    const { products, wishlistItems, addToCart, removeFromWishlist } = useContext(ShopContext);

    const [user,          setUser]          = useState(null);
    const [activeTab,     setActiveTab]     = useState('dashboard');
    const [orders,        setOrders]        = useState([]);
    const [ordersLoading, setOrdersLoading] = useState(false);
    const [ordersError,   setOrdersError]   = useState('');

    // ── Addresses state ────────────────────────────────────────────────────────
    const [addresses,      setAddresses]      = useState([]);
    const [addrLoading,    setAddrLoading]    = useState(false);
    const [showAddrModal,  setShowAddrModal]  = useState(false);
    const [editingAddr,    setEditingAddr]    = useState(null);
    const [addrForm,       setAddrForm]       = useState({ label: '', name: '', street: '', city: '', state: '', zip: '', country: 'India', is_default: false });

    useEffect(() => {
        const stored = localStorage.getItem('neuroUser');
        if (stored) setUser(JSON.parse(stored));
        else navigate('/login');
    }, [navigate]);

    useEffect(() => {
        if (user?.email) { fetchOrders(user.email); fetchAddresses(user.email); }
    }, [user]);

    const fetchAddresses = async (email) => {
        setAddrLoading(true);
        try {
            const res  = await fetch('http://localhost:5000/api/addresses', { headers: { 'User-Email': email } });
            const data = await res.json();
            setAddresses(data);
        } catch {}
        finally { setAddrLoading(false); }
    };

    const openAddAddr = () => {
        setEditingAddr(null);
        setAddrForm({ label: '', name: user?.name || '', street: '', city: '', state: '', zip: '', country: 'India', is_default: addresses.length === 0 });
        setShowAddrModal(true);
    };

    const openEditAddr = (addr) => {
        setEditingAddr(addr);
        setAddrForm({ label: addr.label, name: addr.name, street: addr.street, city: addr.city, state: addr.state, zip: addr.zip, country: addr.country || 'India', is_default: !!addr.is_default });
        setShowAddrModal(true);
    };

    const saveAddr = async () => {
        const url    = editingAddr ? `http://localhost:5000/api/addresses/${editingAddr.id}` : 'http://localhost:5000/api/addresses';
        const method = editingAddr ? 'PUT' : 'POST';
        await fetch(url, { method, headers: { 'Content-Type': 'application/json', 'User-Email': user.email }, body: JSON.stringify(addrForm) });
        setShowAddrModal(false);
        fetchAddresses(user.email);
    };

    const deleteAddr = async (id) => {
        await fetch(`http://localhost:5000/api/addresses/${id}`, { method: 'DELETE', headers: { 'User-Email': user.email } });
        fetchAddresses(user.email);
    };

    const setDefaultAddr = async (id) => {
        await fetch(`http://localhost:5000/api/addresses/${id}/default`, { method: 'PATCH', headers: { 'User-Email': user.email } });
        fetchAddresses(user.email);
    };

    const fetchOrders = async (email) => {
        setOrdersLoading(true);
        setOrdersError('');
        try {
            const res  = await fetch('http://localhost:5000/api/orders/user', {
                headers: { 'User-Email': email },
            });
            const data = await res.json();
            if (data.orders) setOrders(data.orders);
            else setOrdersError('Could not load orders.');
        } catch {
            setOrdersError('Failed to connect to server.');
        } finally {
            setOrdersLoading(false);
        }
    };

    const handleSignOut = async () => {
        try { await signOut(auth); } catch {}
        localStorage.removeItem('neuroUser');
        navigate('/login');
        window.location.reload();
    };

    if (!user) return null;

    const activeOrders    = orders.filter(o => o.status !== 'Delivered');
    const deliveredOrders = orders.filter(o => o.status === 'Delivered');
    const totalSpent      = orders.reduce((s, o) => s + Number(o.total || 0), 0);
    const fmt             = (v) => Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 });


    // ── Orders content ─────────────────────────────────────────────────────────
    const OrdersContent = ({ limit }) => {
        if (ordersLoading) return (
            <div className="empty-state">
                <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite', color: 'hsl(240,20%,42%)' }} />
                <p style={{ marginTop: 14 }}>Loading orders…</p>
            </div>
        );
        if (ordersError) return (
            <div className="empty-state">
                <Package size={40} />
                <h3>Could not load orders</h3>
                <p>{ordersError}</p>
                <button className="btn-solid" style={{ marginTop: 16 }} onClick={() => fetchOrders(user.email)}>Retry</button>
            </div>
        );
        const list = limit ? orders.slice(0, limit) : orders;
        if (list.length === 0) return (
            <div className="empty-state">
                <ShoppingBag size={48} />
                <h3>No orders yet</h3>
                <p>Your purchased items will appear here.</p>
                <button className="btn-solid" style={{ marginTop: 20 }} onClick={() => navigate('/products')}>Start Shopping</button>
            </div>
        );
        return list.map(o => <OrderCard key={o.id} order={o} products={products} onNavigate={navigate} />);
    };

    return (
        <div className="profile-wrapper">
            <div className="profile-container">

                {/* ── Hero ── */}
                <div className="profile-hero">
                    <div className="hero-user-info">
                        <div className="hero-avatar">{user.name.charAt(0).toUpperCase()}</div>
                        <div className="hero-text">
                            <h1>{user.name}</h1>
                            <p>{user.email} <span className="member-badge">Neural Pro</span></p>
                        </div>
                    </div>
                    <div className="hero-stats">
                        <div className="hero-stat-box">
                            <div className="hero-stat-value">{ordersLoading ? '…' : orders.length}</div>
                            <div className="hero-stat-label">Total Orders</div>
                        </div>
                        <div className="hero-stat-box">
                            <div className="hero-stat-value">{ordersLoading ? '…' : activeOrders.length}</div>
                            <div className="hero-stat-label">Active</div>
                        </div>
                        <div className="hero-stat-box">
                            <div className="hero-stat-value">{ordersLoading ? '…' : deliveredOrders.length}</div>
                            <div className="hero-stat-label">Delivered</div>
                        </div>
                    </div>
                </div>

                <div className="profile-grid">
                    {/* ── Sidebar ── */}
                    <div className="profile-sidebar">
                        {[
                            { id: 'dashboard', label: 'Dashboard', Icon: LayoutDashboard },
                            { id: 'orders',    label: 'My Orders', Icon: Package        },
                            { id: 'wishlist',  label: 'Wishlist',  Icon: Heart          },
                            { id: 'addresses', label: 'Addresses', Icon: MapPin         },
                        ].map(({ id, label, Icon }) => (
                            <button key={id}
                                className={`profile-nav-btn ${activeTab === id ? 'active' : ''}`}
                                onClick={() => setActiveTab(id)}>
                                <Icon size={18} /> {label}
                            </button>
                        ))}
                        <div className="profile-sidebar-divider" />
                        <button className={`profile-nav-btn ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>
                            <Settings size={18} /> Settings
                        </button>
                        <div className="profile-sidebar-divider" />
                        <button className="profile-signout-btn" onClick={handleSignOut}>
                            <LogOut size={18} /> Sign Out
                        </button>
                    </div>

                    {/* ── Content ── */}
                    <div className="profile-content">

                        {/* Dashboard */}
                        {activeTab === 'dashboard' && (
                            <div className="animate-on-scroll in-view">
                                <h2 className="section-title">Account Overview</h2>
                                <div className="dashboard-highlights">
                                    <div className="highlight-card">
                                        <div className="highlight-icon icon-purple"><Package size={24} /></div>
                                        <div className="highlight-info">
                                            <p>Active Orders</p>
                                            <h3>{ordersLoading ? '…' : `${activeOrders.length} Active`}</h3>
                                        </div>
                                    </div>
                                    <div className="highlight-card">
                                        <div className="highlight-icon icon-orange"><CreditCard size={24} /></div>
                                        <div className="highlight-info">
                                            <p>Total Spent</p>
                                            <h3>{ordersLoading ? '…' : `₹${fmt(totalSpent)}`}</h3>
                                        </div>
                                    </div>
                                    <div className="highlight-card">
                                        <div className="highlight-icon icon-green"><Heart size={24} /></div>
                                        <div className="highlight-info">
                                            <p>Delivered</p>
                                            <h3>{ordersLoading ? '…' : `${deliveredOrders.length} Orders`}</h3>
                                        </div>
                                    </div>
                                </div>
                                <div className="orders-section">
                                    <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1.3rem', marginBottom: 20 }}>Recent Activity</h3>
                                    <OrdersContent limit={2} />
                                </div>
                            </div>
                        )}

                        {/* Orders */}
                        {activeTab === 'orders' && (
                            <div className="animate-on-scroll in-view">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                                    <h2 className="section-title" style={{ marginBottom: 0 }}>Order History</h2>
                                    <button className="btn-primary-outline"
                                        style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                                        onClick={() => fetchOrders(user.email)}>
                                        <RefreshCw size={13} /> Refresh
                                    </button>
                                </div>
                                <OrdersContent />
                            </div>
                        )}

                        {/* Wishlist */}
                        {activeTab === 'wishlist' && (() => {
                            const wishlistProducts = products.filter(p => wishlistItems[p.id] > 0);
                            return (
                                <div className="animate-on-scroll in-view">
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32, borderBottom: '1px solid hsl(240,10%,90%)', paddingBottom: 16 }}>
                                        <h2 className="section-title" style={{ borderBottom: 'none', marginBottom: 0, paddingBottom: 0 }}>
                                            My Wishlist {wishlistProducts.length > 0 && <span style={{ fontSize: '1rem', color: 'hsl(240,20%,55%)', fontWeight: 500 }}>({wishlistProducts.length})</span>}
                                        </h2>
                                        <button className="btn-primary-outline" onClick={() => navigate('/wishlist')} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                            Full Wishlist <Search size={15} />
                                        </button>
                                    </div>
                                    {wishlistProducts.length === 0 ? (
                                        <div className="empty-state">
                                            <Heart size={48} />
                                            <h3>Your wishlist awaits!</h3>
                                            <p>Browse our catalog and save your favorite AI gear.</p>
                                            <button className="btn-solid" style={{ marginTop: 20 }} onClick={() => navigate('/products')}>Explore Products</button>
                                        </div>
                                    ) : (
                                        <div className="profile-wishlist-grid">
                                            {wishlistProducts.map(product => (
                                                <div className="profile-wishlist-card" key={product.id}>
                                                    <img src={product.image} alt={product.name}
                                                        className="profile-wishlist-img"
                                                        onError={e => { e.target.style.display = 'none'; }} />
                                                    <div className="profile-wishlist-info">
                                                        <p className="profile-wishlist-name">{product.name}</p>
                                                        <p className="profile-wishlist-cat">{product.category}</p>
                                                        <p className="profile-wishlist-price">₹{product.price.toLocaleString()}</p>
                                                    </div>
                                                    <div className="profile-wishlist-actions">
                                                        <button className="btn-solid" style={{ fontSize: '0.82rem', padding: '8px 14px' }}
                                                            onClick={() => addToCart(product.id)}>
                                                            Add to Cart
                                                        </button>
                                                        <button className="btn-primary-outline" style={{ fontSize: '0.82rem', padding: '8px 14px', color: '#ef4444', borderColor: '#ef4444' }}
                                                            onClick={() => removeFromWishlist(product.id)}>
                                                            Remove
                                                        </button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            );
                        })()}

                        {/* Addresses */}
                        {activeTab === 'addresses' && (
                            <div className="animate-on-scroll in-view">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                                    <h2 className="section-title" style={{ marginBottom: 0 }}>Saved Addresses</h2>
                                    <button className="btn-solid" onClick={openAddAddr} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem' }}>
                                        <Plus size={15} /> Add New
                                    </button>
                                </div>

                                {addrLoading ? (
                                    <div className="empty-state"><RefreshCw size={28} style={{ animation: 'spin 1s linear infinite', color: 'hsl(240,20%,42%)' }} /></div>
                                ) : addresses.length === 0 ? (
                                    <div className="empty-state">
                                        <MapPin size={48} />
                                        <h3>No saved addresses</h3>
                                        <p>Add an address to use it quickly at checkout.</p>
                                        <button className="btn-solid" style={{ marginTop: 16 }} onClick={openAddAddr}>Add Address</button>
                                    </div>
                                ) : (
                                    <div className="address-grid">
                                        {addresses.map(addr => (
                                            <div className="address-card" key={addr.id}>
                                                {!!addr.is_default && <div className="address-badge">Default</div>}
                                                <h4>{addr.label || 'Address'}</h4>
                                                <p>{addr.name}<br />{addr.street}<br />{addr.city}, {addr.state} {addr.zip}<br />{addr.country}</p>
                                                <div className="address-actions">
                                                    <button className="address-action-btn" onClick={() => openEditAddr(addr)}>Edit</button>
                                                    {!addr.is_default && (
                                                        <button className="address-action-btn" style={{ color: '#6366f1' }} onClick={() => setDefaultAddr(addr.id)}>Set Default</button>
                                                    )}
                                                    <button className="address-action-btn" style={{ color: '#ef4444' }} onClick={() => deleteAddr(addr.id)}>Remove</button>
                                                </div>
                                            </div>
                                        ))}
                                        <div className="address-card-new" onClick={openAddAddr} style={{ cursor: 'pointer' }}>
                                            <Plus size={32} /><h4>Add New Address</h4>
                                        </div>
                                    </div>
                                )}

                                {/* ── Add / Edit Modal ── */}
                                {showAddrModal && (
                                    <div className="wl-popup-overlay" onClick={() => setShowAddrModal(false)}>
                                        <div onClick={e => e.stopPropagation()} style={{ background: '#fff', borderRadius: 20, padding: '32px 28px', width: '100%', maxWidth: 460, boxShadow: '0 24px 60px rgba(0,0,0,0.15)', position: 'relative' }}>
                                            <button onClick={() => setShowAddrModal(false)} style={{ position: 'absolute', top: 14, right: 14, background: '#f1f5f9', border: 'none', borderRadius: '50%', width: 30, height: 30, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16 }}>✕</button>
                                            <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1.2rem', marginBottom: 20 }}>{editingAddr ? 'Edit Address' : 'Add New Address'}</h3>

                                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                                                {[
                                                    { key: 'label',  label: 'Label (Home / Work)', full: false },
                                                    { key: 'name',   label: 'Full Name',           full: false },
                                                    { key: 'street', label: 'Street Address',      full: true  },
                                                    { key: 'city',   label: 'City',                full: false },
                                                    { key: 'state',  label: 'State',               full: false },
                                                    { key: 'zip',    label: 'ZIP / Postal Code',   full: false },
                                                    { key: 'country',label: 'Country',             full: false },
                                                ].map(({ key, label, full }) => (
                                                    <div key={key} style={{ gridColumn: full ? '1 / -1' : 'auto', display: 'flex', flexDirection: 'column', gap: 4 }}>
                                                        <label style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b' }}>{label}</label>
                                                        <input
                                                            value={addrForm[key]}
                                                            onChange={e => setAddrForm(f => ({ ...f, [key]: e.target.value }))}
                                                            placeholder={label}
                                                            style={{ padding: '9px 12px', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: '0.88rem', outline: 'none' }}
                                                        />
                                                    </div>
                                                ))}
                                            </div>

                                            <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 14, fontSize: '0.88rem', cursor: 'pointer' }}>
                                                <input type="checkbox" checked={addrForm.is_default} onChange={e => setAddrForm(f => ({ ...f, is_default: e.target.checked }))} />
                                                Set as default address
                                            </label>

                                            <button onClick={saveAddr} className="btn-solid" style={{ marginTop: 20, width: '100%', padding: '12px' }}>
                                                {editingAddr ? 'Save Changes' : 'Add Address'}
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Settings */}
                        {activeTab === 'settings' && (
                            <div className="animate-on-scroll in-view">
                                <h2 className="section-title">Account Settings</h2>
                                <div className="dashboard-highlights" style={{ gridTemplateColumns: '1fr' }}>
                                    <div className="highlight-card" style={{ justifyContent: 'space-between' }}>
                                        <div>
                                            <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1.2rem', marginBottom: 4 }}>Login & Security</h3>
                                            <p style={{ color: 'hsl(240,10%,45%)' }}>Update your password and secure your account</p>
                                        </div>
                                        <button className="btn-primary-outline">Manage</button>
                                    </div>
                                    <div className="highlight-card" style={{ justifyContent: 'space-between' }}>
                                        <div>
                                            <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1.2rem', marginBottom: 4 }}>Payment Methods</h3>
                                            <p style={{ color: 'hsl(240,10%,45%)' }}>Manage your saved cards and wallets</p>
                                        </div>
                                        <button className="btn-primary-outline">Manage</button>
                                    </div>
                                </div>
                            </div>
                        )}

                    </div>
                </div>
            </div>
        </div>
    );
};

export default Profile;