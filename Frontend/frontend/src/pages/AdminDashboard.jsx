import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    LayoutDashboard, Package, ShoppingCart, Users,
    ShieldCheck, LogOut, Plus, Search, Trash2,
    Eye, RefreshCw, CheckCircle, AlertTriangle, Cpu,
    DollarSign, Activity, Server, FileText, CheckCircle2,
    Clock, Truck, XCircle, Info, BarChart2, Heart, TrendingUp,
    UserCheck, X, Phone, Mail, MapPin, ShoppingBag
} from 'lucide-react';
import './AdminDashboard.css';

const AdminDashboard = () => {
    const navigate = useNavigate();
    const [products, setProducts]       = useState([]);
    const [orders, setOrders]           = useState([]);
    const [users, setUsers]             = useState([]);
    const [isLoading, setIsLoading]     = useState(true);
    const [activeTab, setActiveTab]     = useState('overview');

    // Search and filter states
    const [productSearch, setProductSearch]   = useState('');
    const [categoryFilter, setCategoryFilter] = useState('All');
    const [orderStatusFilter, setOrderStatusFilter] = useState('All');
    const [userSearch, setUserSearch]         = useState('');

    // Analytics state
    const [analytics, setAnalytics]         = useState({ user_wishlists: [], top_wishlisted: [], top_viewed: [] });
    const [analyticsLoading, setAnalyticsLoading] = useState(false);

    // Modals state
    const [showAddModal, setShowAddModal]           = useState(false);
    const [selectedOrder, setSelectedOrder]         = useState(null);
    const [selectedProduct, setSelectedProduct]     = useState(null);
    const [selectedUserProfile, setSelectedUserProfile] = useState(null);  // {loading, data}

    // Add Product Form State
    const [newProduct, setNewProduct] = useState({
        name: '',
        category: 'AI Software',
        brand: 'NeuroStore',
        price: '',
        shortDescription: '',
        moq: '1 License'
    });
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem('adminToken');
        if (!token) {
            navigate('/admin');
        } else {
            fetchAllData();
        }
    }, [navigate]);

    const fetchAllData = async () => {
        setIsLoading(true);
        const token = localStorage.getItem('adminToken');
        const headers = { 'Authorization': `Basic ${token}` };

        try {
            // Fetch Products
            const resProd = await fetch('/api/products');
            const dataProd = await resProd.json();

            // Filter for Software & AI Software only (matching storefront requirement for now)
            // Note for future: To show all hardware products when uncommented, change below to `dataProd`
            const activeSoftwareProducts = Array.isArray(dataProd)
                ? dataProd.filter(p => p.category === 'Software' || p.category === 'AI Software')
                : [];
            setProducts(activeSoftwareProducts);

            // Fetch Orders (Admin Route)
            const resOrd = await fetch('/api/admin/orders', { headers });
            if (resOrd.ok) {
                const dataOrd = await resOrd.json();
                setOrders(dataOrd.orders || []);
            }

            // Fetch Users (Admin Route)
            const resUser = await fetch('/api/admin/users', { headers });
            if (resUser.ok) {
                const dataUser = await resUser.json();
                setUsers(dataUser.users || []);
            }

        } catch (err) {
            console.error("Error loading admin terminal data:", err);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchAnalytics = async () => {
        setAnalyticsLoading(true);
        const token = localStorage.getItem('adminToken');
        const headers = { 'Authorization': `Basic ${token}` };
        try {
            const [wishRes, viewRes] = await Promise.all([
                fetch('/api/admin/analytics/wishlists', { headers }),
                fetch('/api/admin/analytics/views', { headers }),
            ]);
            const wishData = wishRes.ok ? await wishRes.json() : {};
            const viewData = viewRes.ok ? await viewRes.json() : {};
            setAnalytics({
                user_wishlists:  wishData.user_wishlists  || [],
                top_wishlisted:  wishData.top_wishlisted  || [],
                top_viewed:      viewData.top_viewed      || [],
            });
        } catch (err) {
            console.error('Analytics fetch error:', err);
        } finally {
            setAnalyticsLoading(false);
        }
    };

    const loadUserProfile = async (email) => {
        setSelectedUserProfile({ loading: true, data: null });
        const token = localStorage.getItem('adminToken');
        try {
            const res = await fetch(`/api/admin/user-profile/${encodeURIComponent(email)}`, {
                headers: { 'Authorization': `Basic ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setSelectedUserProfile({ loading: false, data });
            } else {
                setSelectedUserProfile({ loading: false, data: null });
            }
        } catch (err) {
            console.error('User profile fetch error:', err);
            setSelectedUserProfile({ loading: false, data: null });
        }
    };


    const handleLogout = () => {
        localStorage.removeItem('adminToken');
        navigate('/admin');
    };

    const handleDeleteProduct = async (id) => {
        if (!window.confirm("Are you sure you want to remove this software product from catalog?")) return;

        try {
            const token = localStorage.getItem('adminToken');
            const res = await fetch(`/api/admin/product/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Basic ${token}` }
            });
            if (res.ok) {
                setProducts(prev => prev.filter(p => p.id !== id));
            } else {
                alert("Could not delete product.");
            }
        } catch (err) {
            alert("Error deleting product.");
        }
    };

    const handleAddProduct = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);

        try {
            const token = localStorage.getItem('adminToken');
            const res = await fetch('/api/admin/product', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Basic ${token}` },
                body: JSON.stringify(newProduct)
            });

            if (res.ok) {
                setShowAddModal(false);
                setNewProduct({ name: '', category: 'AI Software', brand: 'NeuroStore', price: '', shortDescription: '', moq: '1 License' });
                fetchAllData();
            } else {
                alert("Failed to add software product.");
            }
        } catch (err) {
            alert("Error adding software product.");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleUpdateOrderStatus = async (orderId, newStatus) => {
        const token = localStorage.getItem('adminToken');
        try {
            const res = await fetch(`/api/admin/orders/${orderId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Basic ${token}`
                },
                body: JSON.stringify({ status: newStatus })
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                setOrders(prev => prev.map(o => o.id === orderId ? { ...o, status: newStatus } : o));
                if (selectedOrder && selectedOrder.id === orderId) {
                    setSelectedOrder(prev => ({ ...prev, status: newStatus }));
                }
            } else {
                alert(data.message || 'Failed to update order status');
            }
        } catch (err) {
            console.error('Update status error:', err);
            alert('Network error updating order status');
        }
    };

    const fmt = (v) => Number(v || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 });

    // Calculate Dashboard Stats
    const totalRevenue = orders
        .filter(o => o.status !== 'Cancelled')
        .reduce((sum, o) => sum + Number(o.total || 0), 0);

    const activeOrders = orders.filter(o => !['Delivered', 'Cancelled'].includes(o.status));

    // Dynamic list of categories derived from active products (Software for now)
    const availableCategories = Array.from(new Set(['AI Software', 'Software', ...products.map(p => p.category).filter(Boolean)]));

    // Filtered lists for tabs
    const filteredProducts = products.filter(p => {
        const matchesSearch = p.name.toLowerCase().includes(productSearch.toLowerCase()) ||
                              p.brand?.toLowerCase().includes(productSearch.toLowerCase());
        const matchesCat    = categoryFilter === 'All' || p.category === categoryFilter;
        return matchesSearch && matchesCat;
    });

    const filteredOrders = orders.filter(o => {
        if (orderStatusFilter === 'All') return true;
        return o.status === orderStatusFilter;
    });

    const filteredUsers = users.filter(u => {
        return u.name?.toLowerCase().includes(userSearch.toLowerCase()) ||
               u.email?.toLowerCase().includes(userSearch.toLowerCase());
    });

    if (isLoading) {
        return (
            <div style={{ background: '#090d16', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontFamily: 'Inter' }}>
                <div style={{ textAlign: 'center' }}>
                    <RefreshCw size={36} style={{ animation: 'spin 1s linear infinite', color: '#38bdf8', marginBottom: 16 }} />
                    <h3 style={{ fontFamily: 'Space Grotesk', margin: 0 }}>Initializing Admin Terminal...</h3>
                    <p style={{ color: '#94a3b8', fontSize: '0.88rem' }}>Authenticating security protocols</p>
                </div>
            </div>
        );
    }

    return (
        <div className="admin-wrapper">
            
            {/* Top Navbar */}
            <header className="admin-navbar">
                <div className="admin-brand">
                    <div className="admin-logo-icon">N</div>
                    <div>
                        <h1 className="admin-brand-title">
                            NeuroStore Admin <span className="admin-badge">Full Store Control</span>
                        </h1>
                    </div>
                </div>

                <div className="admin-nav-actions">
                    <div className="system-status-indicator">
                        <div className="status-dot"></div>
                        <span>Backend Active</span>
                    </div>

                    <button className="admin-btn-logout" onClick={handleLogout}>
                        <LogOut size={16} /> Exit Terminal
                    </button>
                </div>
            </header>

            {/* Container */}
            <div className="admin-container">

                {/* Tabs Header */}
                <div className="admin-tabs">
                    {[
                        { id: 'overview',   label: 'Overview',                          Icon: LayoutDashboard },
                        { id: 'software',   label: `Product Catalog (${products.length})`, Icon: Package },
                        { id: 'orders',     label: `Orders (${orders.length})`,         Icon: ShoppingCart },
                        { id: 'users',      label: `Users (${users.length})`,           Icon: Users },
                        { id: 'analytics',  label: 'User Analytics',                    Icon: BarChart2 },
                        { id: 'health',     label: 'System Health',                     Icon: ShieldCheck },
                    ].map(({ id, label, Icon }) => (
                        <button
                            key={id}
                            className={`admin-tab-btn ${activeTab === id ? 'active' : ''}`}
                            onClick={() => {
                                setActiveTab(id);
                                if (id === 'analytics') fetchAnalytics();
                            }}
                        >
                            <Icon size={18} /> {label}
                        </button>
                    ))}
                </div>

                {/* Notice Banner */}
                <div className="admin-notice">
                    <Info size={18} color="#818cf8" />
                    <span>
                        <strong>Dynamic Catalog Sync:</strong> Displays all active items (Hardware & Software) in real time from the backend database.
                    </span>
                </div>

                {/* ── TAB 1: OVERVIEW ── */}
                {activeTab === 'overview' && (
                    <div>
                        {/* Stat Cards */}
                        <div className="admin-stats-grid">
                            <div className="admin-stat-card">
                                <div className="stat-icon-wrapper stat-icon-purple">
                                    <DollarSign size={26} />
                                </div>
                                <div className="stat-info">
                                    <p>Total Revenue</p>
                                    <h3>₹{fmt(totalRevenue)}</h3>
                                </div>
                            </div>

                            <div className="admin-stat-card">
                                <div className="stat-icon-wrapper stat-icon-cyan">
                                    <Package size={26} />
                                </div>
                                <div className="stat-info">
                                    <p>Catalog Items</p>
                                    <h3>{products.length} Products</h3>
                                </div>
                            </div>

                            <div className="admin-stat-card">
                                <div className="stat-icon-wrapper stat-icon-amber">
                                    <ShoppingCart size={26} />
                                </div>
                                <div className="stat-info">
                                    <p>Active Orders</p>
                                    <h3>{activeOrders.length} Pending</h3>
                                </div>
                            </div>

                            <div className="admin-stat-card">
                                <div className="stat-icon-wrapper stat-icon-green">
                                    <Users size={26} />
                                </div>
                                <div className="stat-info">
                                    <p>Registered Users</p>
                                    <h3>{users.length} Accounts</h3>
                                </div>
                            </div>
                        </div>

                        {/* Recent Activity */}
                        <div className="admin-card">
                            <div className="admin-card-header">
                                <h3 className="admin-card-title"><Activity size={20} color="#38bdf8" /> Recent Orders Stream</h3>
                                <button className="admin-btn-primary" onClick={fetchAllData} style={{ fontSize: '0.8rem', padding: '6px 14px' }}>
                                    <RefreshCw size={13} /> Sync Data
                                </button>
                            </div>

                            <div className="admin-table-wrapper">
                                <table className="admin-table">
                                    <thead>
                                        <tr>
                                            <th>Order ID</th>
                                            <th>User Email</th>
                                            <th>Total (₹)</th>
                                            <th>Payment Method</th>
                                            <th>Status</th>
                                            <th>Date</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {orders.slice(0, 5).map(ord => (
                                            <tr key={ord.id}>
                                                <td style={{ fontWeight: 700, color: '#fff' }}>#{ord.id}</td>
                                                <td>{ord.user_email || 'Guest'}</td>
                                                <td style={{ fontWeight: 600, color: '#34d399' }}>₹{fmt(ord.total)}</td>
                                                <td>{ord.payment || 'Online'}</td>
                                                <td>
                                                    <span className={`badge-status badge-${(ord.status || 'Confirmed').toLowerCase()}`}>
                                                        {ord.status || 'Confirmed'}
                                                    </span>
                                                </td>
                                                <td>{ord.created_at?.split(' ')[0] || '—'}</td>
                                            </tr>
                                        ))}
                                        {orders.length === 0 && (
                                            <tr>
                                                <td colSpan="6" style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>No order activity recorded yet.</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {/* ── TAB 2: SOFTWARE CATALOG ── */}
                {activeTab === 'software' && (
                    <div className="admin-card">
                        <div className="admin-card-header">
                            <div>
                                <h3 className="admin-card-title"><Package size={22} color="#818cf8" /> Software & AI License Inventory</h3>
                                <p style={{ color: '#94a3b8', fontSize: '0.85rem', margin: '4px 0 0' }}>Manage active digital software products and licenses</p>
                            </div>

                            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                                <input
                                    type="text"
                                    placeholder="Search software..."
                                    className="admin-search-input"
                                    value={productSearch}
                                    onChange={e => setProductSearch(e.target.value)}
                                />
                                <select
                                    className="admin-search-input"
                                    style={{ minWidth: 150 }}
                                    value={categoryFilter}
                                    onChange={e => setCategoryFilter(e.target.value)}
                                >
                                    <option value="All">All Categories</option>
                                    {availableCategories.map(cat => (
                                        <option key={cat} value={cat}>{cat}</option>
                                    ))}
                                </select>
                                <button className="admin-btn-primary" onClick={() => setShowAddModal(true)}>
                                    <Plus size={16} /> Add Product
                                </button>
                            </div>
                        </div>

                        <div className="admin-table-wrapper">
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Product Name</th>
                                        <th>Category</th>
                                        <th>Brand</th>
                                        <th>Price (₹)</th>
                                        <th>License MOQ</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredProducts.map(p => (
                                        <tr key={p.id}>
                                            <td style={{ fontWeight: 700, color: '#94a3b8' }}>#{p.id}</td>
                                            <td style={{ fontWeight: 600, color: '#fff' }}>{p.name}</td>
                                            <td>
                                                <span style={{ background: 'rgba(99, 102, 241, 0.12)', color: '#818cf8', padding: '4px 10px', borderRadius: 6, fontSize: '0.78rem', fontWeight: 600 }}>
                                                    {p.category}
                                                </span>
                                            </td>
                                            <td>{p.brand || 'NeuroStore'}</td>
                                            <td style={{ fontWeight: 700, color: '#34d399' }}>₹{fmt(p.price)}</td>
                                            <td>{p.moq || '1 License'}</td>
                                            <td>
                                                <div style={{ display: 'flex', gap: 8 }}>
                                                    <button
                                                        style={{ background: 'rgba(239, 68, 68, 0.12)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.25)', padding: '6px 12px', borderRadius: 8, cursor: 'pointer', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 4 }}
                                                        onClick={() => handleDeleteProduct(p.id)}
                                                    >
                                                        <Trash2 size={13} /> Delete
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                    {filteredProducts.length === 0 && (
                                        <tr>
                                            <td colSpan="7" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>No software products match your search.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* ── TAB 3: ORDERS MANAGEMENT ── */}
                {activeTab === 'orders' && (
                    <div className="admin-card">
                        <div className="admin-card-header">
                            <div>
                                <h3 className="admin-card-title"><ShoppingCart size={22} color="#38bdf8" /> Customer Orders Log</h3>
                                <p style={{ color: '#94a3b8', fontSize: '0.85rem', margin: '4px 0 0' }}>View and inspect all incoming customer transactions</p>
                            </div>

                            <div style={{ display: 'flex', gap: 12 }}>
                                <select
                                    className="admin-search-input"
                                    value={orderStatusFilter}
                                    onChange={e => setOrderStatusFilter(e.target.value)}
                                >
                                    <option value="All">All Statuses</option>
                                    <option value="Confirmed">Confirmed</option>
                                    <option value="Processing">Processing</option>
                                    <option value="Shipped">Shipped</option>
                                    <option value="Delivered">Delivered</option>
                                    <option value="Cancelled">Cancelled</option>
                                </select>
                            </div>
                        </div>

                        <div className="admin-table-wrapper">
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>Order ID</th>
                                        <th>Customer Email</th>
                                        <th>Payment</th>
                                        <th>Txn / Payment ID</th>
                                        <th>Total</th>
                                        <th>Status</th>
                                        <th>Date</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredOrders.map(o => (
                                        <tr key={o.id}>
                                            <td style={{ fontWeight: 700, color: '#fff' }}>#{o.id}</td>
                                            <td>{o.user_email || 'Guest User'}</td>
                                            <td>{o.payment || 'Online'}</td>
                                            <td style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#94a3b8' }}>
                                                {o.payment_id || 'N/A'}
                                            </td>
                                            <td style={{ fontWeight: 700, color: '#34d399' }}>₹{fmt(o.total)}</td>
                                            <td>
                                                <select
                                                    value={o.status || 'Confirmed'}
                                                    onChange={(e) => handleUpdateOrderStatus(o.id, e.target.value)}
                                                    className={`badge-status badge-${(o.status || 'Confirmed').toLowerCase()}`}
                                                    style={{
                                                        border: '1px solid rgba(255, 255, 255, 0.2)',
                                                        cursor: 'pointer',
                                                        outline: 'none',
                                                        fontFamily: 'inherit',
                                                        fontWeight: 600,
                                                        padding: '5px 10px',
                                                        borderRadius: '16px'
                                                    }}
                                                >
                                                    <option value="Confirmed" style={{ background: '#151c2e', color: '#a5b4fc' }}>Confirmed</option>
                                                    <option value="Processing" style={{ background: '#151c2e', color: '#fbbf24' }}>Processing</option>
                                                    <option value="Shipped" style={{ background: '#151c2e', color: '#38bdf8' }}>Shipped</option>
                                                    <option value="Delivered" style={{ background: '#151c2e', color: '#34d399' }}>Delivered</option>
                                                    <option value="Cancelled" style={{ background: '#151c2e', color: '#f87171' }}>Cancelled</option>
                                                </select>
                                            </td>
                                            <td>{o.created_at?.split(' ')[0] || '—'}</td>
                                            <td>
                                                <button
                                                    style={{ background: 'rgba(56, 189, 248, 0.12)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.25)', padding: '6px 12px', borderRadius: 8, cursor: 'pointer', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 4 }}
                                                    onClick={() => setSelectedOrder(o)}
                                                >
                                                    <Eye size={13} /> Details
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                    {filteredOrders.length === 0 && (
                                        <tr>
                                            <td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>No orders found.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* ── TAB 4: USERS MANAGEMENT ── */}
                {activeTab === 'users' && (
                    <div className="admin-card">
                        <div className="admin-card-header">
                            <div>
                                <h3 className="admin-card-title"><Users size={22} color="#34d399" /> Registered User Accounts</h3>
                                <p style={{ color: '#94a3b8', fontSize: '0.85rem', margin: '4px 0 0' }}>Accounts created on NeuroStore</p>
                            </div>

                            <input
                                type="text"
                                placeholder="Search by name or email..."
                                className="admin-search-input"
                                value={userSearch}
                                onChange={e => setUserSearch(e.target.value)}
                            />
                        </div>

                        <div className="admin-table-wrapper">
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>User ID</th>
                                        <th>Full Name</th>
                                        <th>Email Address</th>
                                        <th>Phone</th>
                                        <th>Role / Tier</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredUsers.map(u => (
                                        <tr key={u.id}>
                                            <td style={{ fontWeight: 700, color: '#94a3b8' }}>#{u.id}</td>
                                            <td style={{ fontWeight: 600, color: '#fff' }}>{u.name}</td>
                                            <td>{u.email}</td>
                                            <td>{u.phone || '—'}</td>
                                            <td>
                                                <span style={{ background: 'rgba(16, 185, 129, 0.12)', color: '#34d399', padding: '4px 10px', borderRadius: 6, fontSize: '0.78rem', fontWeight: 600 }}>
                                                    {u.type || 'Registered User'}
                                                </span>
                                            </td>
                                            <td>
                                                <button
                                                    style={{ background: 'rgba(129,140,248,0.12)', color: '#818cf8', border: '1px solid rgba(129,140,248,0.3)', padding: '6px 12px', borderRadius: 8, cursor: 'pointer', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 5, whiteSpace: 'nowrap' }}
                                                    onClick={() => loadUserProfile(u.email)}
                                                >
                                                    <UserCheck size={13} /> View Profile
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                    {filteredUsers.length === 0 && (
                                        <tr>
                                            <td colSpan="6" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>No user accounts found.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* ── TAB 5: USER ANALYTICS ── */}
                {activeTab === 'analytics' && (
                    <div>
                        {analyticsLoading ? (
                            <div style={{ textAlign: 'center', padding: '60px', color: '#94a3b8' }}>
                                <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite', color: '#818cf8', marginBottom: 14 }} />
                                <p>Loading analytics data...</p>
                            </div>
                        ) : (
                        <>

                        {/* Top Wishlisted Products */}
                        <div className="admin-card" style={{ marginBottom: 20 }}>
                            <div className="admin-card-header">
                                <h3 className="admin-card-title"><Heart size={20} color="#f472b6" /> Top Wishlisted Products</h3>
                                <button className="admin-btn-secondary" onClick={fetchAnalytics}>
                                    <RefreshCw size={14} /> Refresh
                                </button>
                            </div>
                            {analytics.top_wishlisted.length === 0 ? (
                                <p style={{ color: '#64748b', padding: '20px 0', textAlign: 'center' }}>No wishlist data yet. Users need to add products to their wishlists.</p>
                            ) : (
                            <div className="admin-table-wrapper">
                                <table className="admin-table">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>Product ID</th>
                                            <th>Product Name</th>
                                            <th>Wishlisted By (Users)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {analytics.top_wishlisted.map((row, idx) => {
                                            const prod = products.find(p => p.id === row.product_id);
                                            return (
                                                <tr key={row.product_id}>
                                                    <td style={{ color: '#94a3b8', fontWeight: 700 }}>{idx + 1}</td>
                                                    <td style={{ color: '#818cf8', fontWeight: 600, fontFamily: 'monospace' }}>#{row.product_id}</td>
                                                    <td style={{ color: '#fff', fontWeight: 600 }}>{prod ? prod.name : `Product #${row.product_id}`}</td>
                                                    <td>
                                                        <span style={{ background: 'rgba(244,114,182,0.12)', color: '#f472b6', padding: '4px 12px', borderRadius: 6, fontWeight: 700 }}>
                                                            ❤ {row.wishlist_count} user{row.wishlist_count !== 1 ? 's' : ''}
                                                        </span>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                            )}
                        </div>

                        {/* Most Viewed Products */}
                        <div className="admin-card" style={{ marginBottom: 20 }}>
                            <h3 className="admin-card-title" style={{ marginBottom: 16 }}><TrendingUp size={20} color="#38bdf8" /> Most Viewed Products</h3>
                            {analytics.top_viewed.length === 0 ? (
                                <p style={{ color: '#64748b', padding: '20px 0', textAlign: 'center' }}>No view data yet. Views are tracked when users open a product page.</p>
                            ) : (
                            <div className="admin-table-wrapper">
                                <table className="admin-table">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>Product ID</th>
                                            <th>Product Name</th>
                                            <th>Total Views</th>
                                            <th>Unique Visitors</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {analytics.top_viewed.map((row, idx) => {
                                            const prod = products.find(p => p.id === row.product_id);
                                            return (
                                                <tr key={row.product_id}>
                                                    <td style={{ color: '#94a3b8', fontWeight: 700 }}>{idx + 1}</td>
                                                    <td style={{ color: '#818cf8', fontWeight: 600, fontFamily: 'monospace' }}>#{row.product_id}</td>
                                                    <td style={{ color: '#fff', fontWeight: 600 }}>{prod ? prod.name : `Product #${row.product_id}`}</td>
                                                    <td>
                                                        <span style={{ background: 'rgba(56,189,248,0.12)', color: '#38bdf8', padding: '4px 12px', borderRadius: 6, fontWeight: 700 }}>
                                                            👁 {row.view_count}
                                                        </span>
                                                    </td>
                                                    <td>
                                                        <span style={{ background: 'rgba(129,140,248,0.12)', color: '#818cf8', padding: '4px 12px', borderRadius: 6, fontWeight: 700 }}>
                                                            👤 {row.unique_users}
                                                        </span>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                            )}
                        </div>

                        {/* Per-User Wishlist Breakdown */}
                        <div className="admin-card">
                            <h3 className="admin-card-title" style={{ marginBottom: 16 }}><Users size={20} color="#34d399" /> Per-User Wishlist Breakdown</h3>
                            {analytics.user_wishlists.length === 0 ? (
                                <p style={{ color: '#64748b', padding: '20px 0', textAlign: 'center' }}>No user wishlist data available.</p>
                            ) : (
                            <div className="admin-table-wrapper">
                                <table className="admin-table">
                                    <thead>
                                        <tr>
                                            <th>User Email</th>
                                            <th>Wishlisted Products</th>
                                            <th>Total Wishlisted</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {analytics.user_wishlists.map((row, idx) => (
                                            <tr key={idx}>
                                                <td style={{ color: '#fff', fontWeight: 600 }}>{row.email}</td>
                                                <td style={{ color: '#cbd5e1', fontSize: '0.82rem', maxWidth: 400 }}>
                                                    {row.items.map(item => {
                                                        const prod = products.find(p => p.id === item.product_id);
                                                        const name = prod ? prod.name.substring(0, 36) + (prod.name.length > 36 ? '…' : '') : `#${item.product_id}`;
                                                        return (
                                                            <span key={item.product_id} style={{ display: 'inline-block', background: 'rgba(129,140,248,0.1)', border: '1px solid rgba(129,140,248,0.25)', borderRadius: 5, padding: '2px 8px', margin: '2px 4px 2px 0', fontSize: '0.78rem', color: '#818cf8' }}>
                                                                {name}
                                                            </span>
                                                        );
                                                    })}
                                                </td>
                                                <td>
                                                    <span style={{ background: 'rgba(52,211,153,0.12)', color: '#34d399', padding: '4px 12px', borderRadius: 6, fontWeight: 700 }}>
                                                        {row.items.length} item{row.items.length !== 1 ? 's' : ''}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            )}
                        </div>

                        </>
                        )}
                    </div>
                )}

                {/* ── TAB 6: SYSTEM HEALTH ── */}
                {activeTab === 'health' && (
                    <div>
                        <div className="admin-card">
                            <h3 className="admin-card-title" style={{ marginBottom: 20 }}><Server size={22} color="#38bdf8" /> Infrastructure Diagnostics</h3>
                            
                            <div className="health-grid">
                                <div className="health-card">
                                    <div>
                                        <h4 style={{ color: '#fff', margin: '0 0 4px', fontSize: '0.95rem' }}>SQLite Database Engine</h4>
                                        <p style={{ color: '#94a3b8', margin: 0, fontSize: '0.8rem' }}>neurostore.db (Orders, Carts, Users, Addresses)</p>
                                    </div>
                                    <div className="health-status-good"><CheckCircle2 size={16} /> Operational</div>
                                </div>

                                <div className="health-card">
                                    <div>
                                        <h4 style={{ color: '#fff', margin: '0 0 4px', fontSize: '0.95rem' }}>Flask REST API</h4>
                                        <p style={{ color: '#94a3b8', margin: 0, fontSize: '0.8rem' }}>Port 8000 — CORS Enabled</p>
                                    </div>
                                    <div className="health-status-good"><CheckCircle2 size={16} /> Connected</div>
                                </div>

                                <div className="health-card">
                                    <div>
                                        <h4 style={{ color: '#fff', margin: '0 0 4px', fontSize: '0.95rem' }}>Razorpay Gateway</h4>
                                        <p style={{ color: '#94a3b8', margin: 0, fontSize: '0.8rem' }}>Live Verification & Webhooks</p>
                                    </div>
                                    <div className="health-status-good"><CheckCircle2 size={16} /> Ready</div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

            </div>

            {/* ── MODAL: ADD SOFTWARE PRODUCT ── */}
            {showAddModal && (
                <div className="admin-modal-overlay" onClick={() => setShowAddModal(false)}>
                    <div className="admin-modal-content" onClick={e => e.stopPropagation()}>
                        <button className="admin-modal-close" onClick={() => setShowAddModal(false)}>✕</button>
                        
                        <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1.4rem', margin: '0 0 20px', color: '#fff' }}>
                            Add Software Product
                        </h3>

                        <form onSubmit={handleAddProduct}>
                            <div className="admin-form-group">
                                <label>Product Name</label>
                                <input
                                    type="text"
                                    required
                                    placeholder="e.g. Vision Analytics Suite Pro"
                                    className="admin-form-input"
                                    value={newProduct.name}
                                    onChange={e => setNewProduct({ ...newProduct, name: e.target.value })}
                                />
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                                <div className="admin-form-group">
                                    <label>Category</label>
                                    <select
                                        className="admin-form-select"
                                        value={newProduct.category}
                                        onChange={e => setNewProduct({ ...newProduct, category: e.target.value })}
                                    >
                                        <option value="AI Software">AI Software</option>
                                        <option value="Software">Software</option>
                                    </select>
                                </div>

                                <div className="admin-form-group">
                                    <label>Brand / Publisher</label>
                                    <input
                                        type="text"
                                        required
                                        placeholder="e.g. NeuroStore AI"
                                        className="admin-form-input"
                                        value={newProduct.brand}
                                        onChange={e => setNewProduct({ ...newProduct, brand: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                                <div className="admin-form-group">
                                    <label>Price (₹)</label>
                                    <input
                                        type="number"
                                        required
                                        placeholder="e.g. 4999"
                                        className="admin-form-input"
                                        value={newProduct.price}
                                        onChange={e => setNewProduct({ ...newProduct, price: e.target.value })}
                                    />
                                </div>

                                <div className="admin-form-group">
                                    <label>License Type / MOQ</label>
                                    <input
                                        type="text"
                                        placeholder="e.g. 1 License / Annual"
                                        className="admin-form-input"
                                        value={newProduct.moq}
                                        onChange={e => setNewProduct({ ...newProduct, moq: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="admin-form-group">
                                <label>Short Description</label>
                                <textarea
                                    rows="3"
                                    required
                                    placeholder="Brief description of the software features..."
                                    className="admin-form-textarea"
                                    value={newProduct.shortDescription}
                                    onChange={e => setNewProduct({ ...newProduct, shortDescription: e.target.value })}
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="admin-btn-primary"
                                style={{ width: '100%', justifyContent: 'center', padding: '14px', marginTop: 10 }}
                            >
                                {isSubmitting ? 'Adding to Catalog...' : 'Add Software Product'}
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* ── MODAL: ORDER DETAILS ── */}
            {selectedOrder && (
                <div className="admin-modal-overlay" onClick={() => setSelectedOrder(null)}>
                    <div className="admin-modal-content" onClick={e => e.stopPropagation()}>
                        <button className="admin-modal-close" onClick={() => setSelectedOrder(null)}>✕</button>

                        <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1.4rem', margin: '0 0 16px', color: '#fff' }}>
                            Order Details #{selectedOrder.id}
                        </h3>

                        <div style={{ background: '#090d16', padding: '16px', borderRadius: 12, border: '1px solid rgba(255,255,255,0.08)', marginBottom: 20 }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: '0.88rem' }}>
                                <div><span style={{ color: '#94a3b8' }}>User Email:</span> <strong style={{ color: '#fff' }}>{selectedOrder.user_email || 'Guest'}</strong></div>
                                <div><span style={{ color: '#94a3b8' }}>Payment Method:</span> <strong style={{ color: '#fff' }}>{selectedOrder.payment}</strong></div>
                                <div><span style={{ color: '#94a3b8' }}>Payment ID:</span> <strong style={{ color: '#38bdf8', fontFamily: 'monospace' }}>{selectedOrder.payment_id || 'N/A'}</strong></div>
                                <div><span style={{ color: '#94a3b8' }}>Date:</span> <strong style={{ color: '#fff' }}>{selectedOrder.created_at}</strong></div>
                                <div><span style={{ color: '#94a3b8' }}>Total Amount:</span> <strong style={{ color: '#34d399', fontSize: '1rem' }}>₹{fmt(selectedOrder.total)}</strong></div>
                                <div><span style={{ color: '#94a3b8' }}>Current Status:</span> <strong style={{ color: '#818cf8' }}>{selectedOrder.status || 'Confirmed'}</strong></div>
                            </div>
                        </div>

                        {/* Order Status Control */}
                        <div style={{ background: 'rgba(56, 189, 248, 0.05)', padding: '16px', borderRadius: 12, border: '1px solid rgba(56, 189, 248, 0.2)', marginBottom: 20 }}>
                            <h4 style={{ color: '#38bdf8', fontSize: '0.82rem', textTransform: 'uppercase', margin: '0 0 8px', fontWeight: 700, letterSpacing: '0.5px' }}>
                                Change Order Status (Live Sync to User)
                            </h4>
                            <select
                                value={selectedOrder.status || 'Confirmed'}
                                onChange={(e) => handleUpdateOrderStatus(selectedOrder.id, e.target.value)}
                                className="admin-form-select"
                                style={{ width: '100%', padding: '10px 14px', background: '#090d16', color: '#fff', cursor: 'pointer' }}
                            >
                                <option value="Confirmed">Confirmed</option>
                                <option value="Processing">Processing</option>
                                <option value="Shipped">Shipped</option>
                                <option value="Delivered">Delivered</option>
                                <option value="Cancelled">Cancelled</option>
                            </select>
                        </div>

                        <div style={{ marginBottom: 20 }}>
                            <h4 style={{ color: '#94a3b8', fontSize: '0.8rem', textTransform: 'uppercase', margin: '0 0 8px' }}>Shipping Address</h4>
                            <p style={{ background: '#090d16', padding: '12px', borderRadius: 8, fontSize: '0.88rem', color: '#cbd5e1', margin: 0 }}>
                                {selectedOrder.address || 'No address specified'}
                            </p>
                        </div>

                        <button className="admin-btn-primary" onClick={() => setSelectedOrder(null)} style={{ width: '100%', justifyContent: 'center' }}>
                            Close Details
                        </button>
                    </div>
                </div>
            )}

            {/* ── USER PROFILE DRAWER ── */}
            {selectedUserProfile && (
                <div
                    style={{ position: 'fixed', inset: 0, zIndex: 9999, display: 'flex', alignItems: 'flex-start', justifyContent: 'flex-end', background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)' }}
                    onClick={() => setSelectedUserProfile(null)}
                >
                    <div
                        style={{ width: 540, maxWidth: '96vw', height: '100vh', overflowY: 'auto', background: '#0f1729', borderLeft: '1px solid rgba(129,140,248,0.25)', padding: '0 0 40px', boxShadow: '-8px 0 48px rgba(0,0,0,0.6)' }}
                        onClick={e => e.stopPropagation()}
                    >
                        {/* Drawer Header */}
                        <div style={{ background: 'linear-gradient(135deg,#1e1b4b 0%,#0f172a 100%)', padding: '28px 28px 20px', borderBottom: '1px solid rgba(129,140,248,0.15)', position: 'sticky', top: 0, zIndex: 10 }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <div style={{ width: 48, height: 48, borderRadius: '50%', background: 'linear-gradient(135deg,#818cf8,#a78bfa)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, fontWeight: 800, color: '#fff' }}>
                                        {selectedUserProfile.data?.user?.name?.[0]?.toUpperCase() || '?'}
                                    </div>
                                    <div>
                                        <h3 style={{ margin: 0, color: '#fff', fontSize: '1.15rem', fontFamily: 'Space Grotesk' }}>{selectedUserProfile.data?.user?.name || 'Loading...'}</h3>
                                        <p style={{ margin: '2px 0 0', color: '#94a3b8', fontSize: '0.82rem' }}>User Profile</p>
                                    </div>
                                </div>
                                <button onClick={() => setSelectedUserProfile(null)} style={{ background: 'rgba(255,255,255,0.08)', border: 'none', borderRadius: 8, padding: '8px', cursor: 'pointer', color: '#94a3b8', display: 'flex' }}>
                                    <X size={18} />
                                </button>
                            </div>
                        </div>

                        {selectedUserProfile.loading ? (
                            <div style={{ textAlign: 'center', padding: '80px 20px', color: '#94a3b8' }}>
                                <RefreshCw size={30} style={{ animation: 'spin 1s linear infinite', color: '#818cf8', marginBottom: 14 }} />
                                <p>Loading profile...</p>
                            </div>
                        ) : selectedUserProfile.data ? (() => {
                            const { user, orders: uOrders, wishlist, top_searched, top_viewed } = selectedUserProfile.data;
                            const fmt = (v) => Number(v || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 });
                            const statusColors = { Confirmed: '#a5b4fc', Processing: '#fbbf24', Shipped: '#38bdf8', Delivered: '#34d399', Cancelled: '#f87171' };

                            const resolve = (pid) => {
                                const p = products.find(x => x.id === parseInt(pid));
                                return p ? p.name : `Product #${pid}`;
                            };

                            return (
                                <div style={{ padding: '24px 28px' }}>

                                    {/* Account Info */}
                                    <div style={{ background: '#151c2e', borderRadius: 14, padding: '18px 20px', marginBottom: 20, border: '1px solid rgba(255,255,255,0.06)' }}>
                                        <h4 style={{ color: '#818cf8', fontSize: '0.76rem', textTransform: 'uppercase', letterSpacing: '0.6px', margin: '0 0 14px', fontWeight: 700 }}>Account Details</h4>
                                        <div style={{ display: 'grid', gap: 10 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.88rem' }}>
                                                <Mail size={14} color="#64748b" />
                                                <span style={{ color: '#94a3b8' }}>Email:</span>
                                                <span style={{ color: '#fff', fontWeight: 600 }}>{user.email}</span>
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.88rem' }}>
                                                <Phone size={14} color="#64748b" />
                                                <span style={{ color: '#94a3b8' }}>Phone:</span>
                                                <span style={{ color: '#fff', fontWeight: 600 }}>{user.phone || '—'}</span>
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.88rem' }}>
                                                <ShoppingBag size={14} color="#64748b" />
                                                <span style={{ color: '#94a3b8' }}>Orders:</span>
                                                <span style={{ color: '#34d399', fontWeight: 700 }}>{uOrders.length}</span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Wishlist */}
                                    <div style={{ background: '#151c2e', borderRadius: 14, padding: '18px 20px', marginBottom: 20, border: '1px solid rgba(255,255,255,0.06)' }}>
                                        <h4 style={{ color: '#f472b6', fontSize: '0.76rem', textTransform: 'uppercase', letterSpacing: '0.6px', margin: '0 0 14px', fontWeight: 700 }}>❤ Wishlist ({wishlist.length} items)</h4>
                                        {wishlist.length === 0 ? (
                                            <p style={{ color: '#64748b', fontSize: '0.85rem', margin: 0 }}>No items in wishlist yet.</p>
                                        ) : (
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                                {wishlist.map(item => (
                                                    <span key={item.product_id} style={{ background: 'rgba(244,114,182,0.1)', border: '1px solid rgba(244,114,182,0.25)', borderRadius: 8, padding: '6px 12px', fontSize: '0.8rem', color: '#f9a8d4' }}>
                                                        {resolve(item.product_id)}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {/* Most Searched */}
                                    <div style={{ background: '#151c2e', borderRadius: 14, padding: '18px 20px', marginBottom: 20, border: '1px solid rgba(255,255,255,0.06)' }}>
                                        <h4 style={{ color: '#38bdf8', fontSize: '0.76rem', textTransform: 'uppercase', letterSpacing: '0.6px', margin: '0 0 14px', fontWeight: 700 }}>🔍 Most Searched Products</h4>
                                        {top_searched.length === 0 ? (
                                            <p style={{ color: '#64748b', fontSize: '0.85rem', margin: 0 }}>No search data yet.</p>
                                        ) : (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                                {top_searched.map((s, i) => (
                                                    <div key={s.product_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(56,189,248,0.05)', borderRadius: 8, padding: '8px 12px', border: '1px solid rgba(56,189,248,0.12)' }}>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                                            <span style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 700, minWidth: 18 }}>#{i+1}</span>
                                                            <span style={{ color: '#e2e8f0', fontSize: '0.85rem', fontWeight: 600 }}>{resolve(s.product_id)}</span>
                                                        </div>
                                                        <span style={{ background: 'rgba(56,189,248,0.15)', color: '#38bdf8', padding: '3px 10px', borderRadius: 6, fontSize: '0.78rem', fontWeight: 700 }}>
                                                            {s.count}×
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {/* Most Viewed */}
                                    <div style={{ background: '#151c2e', borderRadius: 14, padding: '18px 20px', marginBottom: 20, border: '1px solid rgba(255,255,255,0.06)' }}>
                                        <h4 style={{ color: '#a78bfa', fontSize: '0.76rem', textTransform: 'uppercase', letterSpacing: '0.6px', margin: '0 0 14px', fontWeight: 700 }}>👁 Most Viewed Products</h4>
                                        {top_viewed.length === 0 ? (
                                            <p style={{ color: '#64748b', fontSize: '0.85rem', margin: 0 }}>No view data yet.</p>
                                        ) : (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                                {top_viewed.map((v, i) => (
                                                    <div key={v.product_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(167,139,250,0.05)', borderRadius: 8, padding: '8px 12px', border: '1px solid rgba(167,139,250,0.12)' }}>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                                            <span style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 700, minWidth: 18 }}>#{i+1}</span>
                                                            <span style={{ color: '#e2e8f0', fontSize: '0.85rem', fontWeight: 600 }}>{resolve(v.product_id)}</span>
                                                        </div>
                                                        <span style={{ background: 'rgba(167,139,250,0.15)', color: '#a78bfa', padding: '3px 10px', borderRadius: 6, fontSize: '0.78rem', fontWeight: 700 }}>
                                                            {v.count}×
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {/* Order History */}
                                    <div style={{ background: '#151c2e', borderRadius: 14, padding: '18px 20px', border: '1px solid rgba(255,255,255,0.06)' }}>
                                        <h4 style={{ color: '#34d399', fontSize: '0.76rem', textTransform: 'uppercase', letterSpacing: '0.6px', margin: '0 0 14px', fontWeight: 700 }}>🛒 Order History ({uOrders.length})</h4>
                                        {uOrders.length === 0 ? (
                                            <p style={{ color: '#64748b', fontSize: '0.85rem', margin: 0 }}>No orders placed yet.</p>
                                        ) : (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                                {uOrders.map(o => (
                                                    <div key={o.id} style={{ background: '#0f1729', borderRadius: 10, padding: '12px 14px', border: '1px solid rgba(255,255,255,0.06)' }}>
                                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                                                            <span style={{ color: '#94a3b8', fontSize: '0.82rem', fontFamily: 'monospace' }}>Order #{o.id}</span>
                                                            <span style={{ background: `rgba(${statusColors[o.status] ? '255,255,255' : '255,255,255'},0.05)`, color: statusColors[o.status] || '#94a3b8', padding: '3px 10px', borderRadius: 6, fontSize: '0.78rem', fontWeight: 700 }}>
                                                                {o.status || 'Confirmed'}
                                                            </span>
                                                        </div>
                                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                                                            <span style={{ color: '#64748b' }}>{o.created_at?.split(' ')[0] || '—'}</span>
                                                            <span style={{ color: '#34d399', fontWeight: 700 }}>₹{fmt(o.total)}</span>
                                                        </div>
                                                        <div style={{ marginTop: 6, fontSize: '0.78rem', color: '#475569' }}>{o.payment || '—'}</div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                </div>
                            );
                        })() : (
                            <div style={{ textAlign: 'center', padding: '60px 20px', color: '#f87171' }}>
                                Failed to load profile.
                            </div>
                        )}
                    </div>
                </div>
            )}

        </div>
    );
};

export default AdminDashboard;
