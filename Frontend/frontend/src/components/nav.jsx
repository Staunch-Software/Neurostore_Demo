import React, { useState, useContext, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import logo from '../assets/logo.ico';
import {
  Phone, Mail, Facebook, Instagram, Linkedin, Twitter,
  Search, X, Heart, ShoppingCart, Menu, ChevronDown, ChevronRight,
  User, LogOut // <-- NEW: Added User and LogOut icons
} from 'lucide-react';
import { ShopContext } from './context/ShopContext';
import './nav.css';

// Data for Dropdowns
const hardwareItems = [
  { name: 'AI Graphics Cards', href: '/products/ai-graphics-cards' },
  { name: 'AI Vision & Security', href: '/products/ai-vision-security' },
  { name: 'AI Dev Boards', href: '/products/ai-dev-boards' },
  { name: 'AI Workstation GPUs', href: '/products/ai-workstation-gpus' },
  { name: 'AI Networking & Storage', href: '/products/ai-networking-storage' },
  { name: 'AI Monitor', href: '/products/ai-monitors' },
  { name: 'AI Smart Monitor', href: '/products/ai-smart-monitors' },
  { name: 'AI Commercial Displays', href: '/products/ai-commercial-displays' },
  { name: 'AI Interactive Displays', href: '/products/ai-interactive-displays' },
  { name: 'AI AR/VR Wearables', href: '/products/ai-ar-vr-wearables' },
  { name: 'AI Accessories', href: '/products/ai-accessories' },
];

const softwareItems = [
  { name: 'Non AI Software', href: '/products/software' },
  { name: 'AI Software', href: '/products/ai-software' },
];

// --- SEARCH SLUG HELPER ---
const generateSlug = (text) => {
  if (!text) return '';
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');
};

// --- SEARCH BAR COMPONENT ---
const SearchBar = () => {
  const { products } = useContext(ShopContext);
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const navigate = useNavigate();

  const handleSearch = (e) => {
    const text = e.target.value;
    setQuery(text);

    if (text.length > 0) {
      const filtered = products.filter(product =>
        product.name.toLowerCase().includes(text.toLowerCase()) ||
        product.category.toLowerCase().includes(text.toLowerCase())
      );
      setResults(filtered);
    } else {
      setResults([]);
    }
  };

  const handleResultClick = (product) => {
    setIsOpen(false);
    setQuery("");
    setResults([]);
    navigate(`/products/${generateSlug(product.category)}/${generateSlug(product.name)}`);
  };

  return (
    <div className="neuro-search-bar-container">
      <button onClick={() => setIsOpen(!isOpen)} className="neuro-nav-icon-btn">
        {isOpen ? <X size={20} /> : <Search size={20} />}
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 240, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="neuro-search-input-wrapper"
          >
            <input
              type="text"
              placeholder="Search products..."
              className="neuro-search-input"
              autoFocus
              value={query}
              onChange={handleSearch}
            />

            {/* Search Results Dropdown */}
            {results.length > 0 && (
              <div className="search-results-dropdown">
                {results.slice(0, 5).map(product => (
                  <div
                    key={product.id}
                    className="search-result-item"
                    onClick={() => handleResultClick(product)}
                  >
                    <img src={product.image} alt={product.name} />
                    <div className="search-result-info">
                      <h4>{product.name}</h4>
                      <p>₹{product.price}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {query.length > 0 && results.length === 0 && (
              <div className="search-results-dropdown" style={{ padding: '10px', textAlign: 'center', color: '#666' }}>
                No products found
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export const Navbar = () => {
  const { cartItems, getTotalWishlistItems, user, logout } = useContext(ShopContext);
  const navigate = useNavigate();

  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showWishlistPopup, setShowWishlistPopup] = useState(false);
  const [showCartPopup,    setShowCartPopup]    = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [productsOpen, setProductsOpen] = useState(false);
  const [hardwareOpen, setHardwareOpen] = useState(false);
  const [softwareOpen, setSoftwareOpen] = useState(false);

  const cartCount = Object.values(cartItems || {}).reduce((total, qty) => total + (qty > 0 ? qty : 0), 0);

  const handleLogout = () => {
    logout();
    setShowUserDropdown(false);
    navigate("/");
  };

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="neuro-navbar"
    >
      {/* --- Top Bar --- */}
      <div className="neuro-top-bar">
        <div className="neuro-container neuro-top-bar-content">
          <div className="neuro-contact-info">
            <a href="tel:+18881234567" className="neuro-contact-link"><Phone size={14} /> +91 (044) 22353175</a>
            <a href="mailto:info@neurostore.ai" className="neuro-contact-link"><Mail size={14} /> info@neurostore.ai</a>
          </div>
          <div className="neuro-social-icons">
            <a href="#" className="neuro-social-link"><Facebook size={14} /></a>
            <a href="#" className="neuro-social-link"><Instagram size={14} /></a>
            <a href="#" className="neuro-social-link"><Twitter size={14} /></a>
            <a href="#" className="neuro-social-link"><Linkedin size={14} /></a>
          </div>
        </div>
      </div>

      {/* --- Main Nav --- */}
      <div className="neuro-main-nav">
        <div className="neuro-container neuro-main-nav-content">
          <Link to="/" className="neuro-logo">
            <div className="neuro-logo-icon">
              <img src={logo} alt="NeuroStore Logo" className="neuro-logo-img" />
            </div>
            <span className="neuro-logo-text">NeuroStore - Anything AI</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="neuro-desktop-nav">
            <Link to="/" className="neuro-nav-link">Home</Link>
            <Link to="/about" className="neuro-nav-link">About</Link>

            {/* Products Dropdown with Sub-menus */}
            <div className="neuro-dropdown-wrapper" onMouseLeave={() => setProductsOpen(false)}>
              <button
                className="neuro-nav-link"
                onMouseEnter={() => setProductsOpen(true)}
                onClick={() => setProductsOpen(!productsOpen)}
              >
                Products <ChevronDown size={14} />
              </button>

              <AnimatePresence>
                {productsOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="neuro-dropdown-menu"
                  >
                    <Link to="/products" className="neuro-dropdown-item">All Products</Link>

                    {/* Hardware Sub-menu */}
                    <div
                      className="neuro-dropdown-item"
                      onMouseEnter={() => setHardwareOpen(true)}
                      onMouseLeave={() => setHardwareOpen(false)}
                    >
                      Hardware <ChevronRight size={14} />
                      {hardwareOpen && (
                        <div className="neuro-dropdown-submenu">
                          {hardwareItems.map(item => (
                            <Link key={item.name} to={item.href} className="neuro-dropdown-item">
                              {item.name}
                            </Link>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Software Sub-menu */}
                    <div
                      className="neuro-dropdown-item"
                      onMouseEnter={() => setSoftwareOpen(true)}
                      onMouseLeave={() => setSoftwareOpen(false)}
                    >
                      Software <ChevronRight size={14} />
                      {softwareOpen && (
                        <div className="neuro-dropdown-submenu">
                          {softwareItems.map(item => (
                            <Link key={item.name} to={item.href} className="neuro-dropdown-item">
                              {item.name}
                            </Link>
                          ))}
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <Link to="/brands" className="neuro-nav-link">Brands</Link>

            {/* Actions: Search, Wishlist, Cart, Login */}
            <div className="neuro-nav-actions">
              <SearchBar />

              <div style={{ position: 'relative' }}>
                <button
                  className="neuro-nav-icon-btn"
                  onClick={() => {
                    if (user) { navigate('/wishlist'); }
                    else { setShowCartPopup(false); setShowWishlistPopup(v => !v); }
                  }}
                >
                  <Heart size={20} />
                  {getTotalWishlistItems() > 0 && (
                    <span className="neuro-badge">{getTotalWishlistItems()}</span>
                  )}
                </button>

                <AnimatePresence>
                  {showWishlistPopup && !user && (
                    <motion.div
                      initial={{ opacity: 0, y: 8, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 8, scale: 0.95 }}
                      transition={{ duration: 0.18 }}
                      className="wishlist-login-popup"
                    >
                      <button className="wishlist-popup-close" onClick={() => setShowWishlistPopup(false)}>
                        <X size={14} />
                      </button>
                      <Heart size={28} className="wishlist-popup-icon" />
                      <p className="wishlist-popup-title">Sign in to view your Wishlist</p>
                      <p className="wishlist-popup-sub">Save your favourite AI products and access them anytime.</p>
                      <button
                        className="wishlist-popup-btn"
                        onClick={() => { setShowWishlistPopup(false); navigate('/login'); }}
                      >
                        Login / Register
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <div style={{ position: 'relative' }}>
                <button
                  className="neuro-nav-icon-btn"
                  onClick={() => {
                    if (user) { navigate('/cart'); }
                    else { setShowWishlistPopup(false); setShowCartPopup(v => !v); }
                  }}
                >
                  <ShoppingCart size={20} />
                  {cartCount > 0 && (
                    <span className="neuro-badge">{cartCount}</span>
                  )}
                </button>

                <AnimatePresence>
                  {showCartPopup && !user && (
                    <motion.div
                      initial={{ opacity: 0, y: 8, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 8, scale: 0.95 }}
                      transition={{ duration: 0.18 }}
                      className="wishlist-login-popup"
                    >
                      <button className="wishlist-popup-close" onClick={() => setShowCartPopup(false)}>
                        <X size={14} />
                      </button>
                      <ShoppingCart size={28} className="wishlist-popup-icon" />
                      <p className="wishlist-popup-title">Sign in to view your Cart</p>
                      <p className="wishlist-popup-sub">Login or register to add products to your cart and checkout.</p>
                      <button
                        className="wishlist-popup-btn"
                        onClick={() => { setShowCartPopup(false); navigate('/login'); }}
                      >
                        Login / Register
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* --- NEW: USER AUTH ICON --- */}
              <div style={{ position: 'relative' }}>
                {user ? (
                  <div
                    onClick={() => setShowUserDropdown(!showUserDropdown)}
                    style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', background: 'rgba(255,255,255,0.1)', padding: '6px 12px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.2)', color: 'white', transition: '0.2s' }}
                  >
                    <User size={16} />
                    <span style={{ fontSize: '13px', fontWeight: '600' }}>
                      {user.name.split(' ')[0]}
                    </span>
                  </div>
                ) : (
                  <Link to="/login" className="neuro-nav-icon-btn">
                    <User size={20} />
                  </Link>
                )}

                <AnimatePresence>
                  {showUserDropdown && user && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      style={{
                        position: 'absolute', top: '130%', right: '0', background: 'white',
                        border: '1px solid #e2e8f0', borderRadius: '12px',
                        boxShadow: '0 10px 30px rgba(0,0,0,0.1)', width: '200px',
                        padding: '16px', zIndex: 1000
                      }}
                    >
                      <p style={{ margin: '0 0 4px 0', fontSize: '14px', fontWeight: '700', color: '#1a1a1a' }}>
                        {user.name}
                      </p>
                      <p style={{ margin: '0 0 16px 0', fontSize: '12px', color: '#64748b', wordBreak: 'break-all' }}>
                        {user.email}
                      </p>

                      <button
                        onClick={() => {
                          setShowUserDropdown(false);
                          navigate("/profile");
                        }}
                        style={{
                          width: '100%', background: '#f8fafc', color: '#334155',
                          border: '1px solid #e2e8f0', padding: '10px', borderRadius: '8px',
                          cursor: 'pointer', display: 'flex', alignItems: 'center',
                          justifyContent: 'center', gap: '8px', fontWeight: '600', fontSize: '13px',
                          transition: '0.2s', marginBottom: '8px'
                        }}
                        onMouseOver={(e) => e.target.style.background = '#f1f5f9'}
                        onMouseOut={(e) => e.target.style.background = '#f8fafc'}
                      >
                        <User size={16} /> My Profile
                      </button>

                      <button
                        onClick={handleLogout}
                        style={{
                          width: '100%', background: '#fef2f2', color: '#ef4444',
                          border: '1px solid #fecaca', padding: '10px', borderRadius: '8px',
                          cursor: 'pointer', display: 'flex', alignItems: 'center',
                          justifyContent: 'center', gap: '8px', fontWeight: '600', fontSize: '13px',
                          transition: '0.2s'
                        }}
                        onMouseOver={(e) => e.target.style.background = '#fee2e2'}
                        onMouseOut={(e) => e.target.style.background = '#fef2f2'}
                      >
                        <LogOut size={16} /> Sign Out
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

            </div>

            <Link to="/contact" className="neuro-contact-btn">Contact Us</Link>
          </div>

          {/* Mobile Toggle */}
          <div className="neuro-mobile-top-actions">
            <button
              onClick={() => { if (user) navigate('/cart'); else setShowCartPopup(v => !v); }}
              style={{ background: 'none', border: 'none', padding: 0, color: 'white', marginRight: '15px', position: 'relative', cursor: 'pointer' }}
            >
              <ShoppingCart size={20} />
              {cartCount > 0 && <span className="neuro-badge" style={{ top: '-8px', right: '-8px' }}>{cartCount}</span>}
            </button>
            <button onClick={() => setIsOpen(!isOpen)} className="neuro-mobile-menu-btn">
              {isOpen ? <X /> : <Menu />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="neuro-mobile-menu"
          >
            <div className="neuro-mobile-menu-content">
              {/* --- MOBILE USER INFO --- */}
              {user ? (
                <div style={{ background: '#f8f9fb', padding: '15px', borderRadius: '8px', marginBottom: '15px' }}>
                  <p style={{ margin: '0 0 10px 0', fontWeight: 'bold', color: '#1a1a1a' }}>Hi, {user.name}</p>
                  
                  <Link 
                    to="/profile" 
                    onClick={() => setIsOpen(false)} 
                    style={{ color: '#2563eb', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '10px', textDecoration: 'none' }}
                  >
                    <User size={14} /> My Profile
                  </Link>
                  
                  <button onClick={handleLogout} style={{ background: 'none', border: 'none', color: '#ef4444', fontWeight: '600', padding: 0, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <LogOut size={14} /> Sign Out
                  </button>
                </div>
              ) : (
                <Link to="/login" className="neuro-mobile-nav-link" onClick={() => setIsOpen(false)} style={{ color: '#2563eb', fontWeight: 'bold' }}>Login / Register</Link>
              )}

              <Link to="/" className="neuro-mobile-nav-link" onClick={() => setIsOpen(false)}>Home</Link>
              <Link to="/products" className="neuro-mobile-nav-link" onClick={() => setIsOpen(false)}>Products</Link>
              {user
                ? <Link to="/wishlist" className="neuro-mobile-nav-link" onClick={() => setIsOpen(false)}>Wishlist</Link>
                : <button
                    className="neuro-mobile-nav-link"
                    style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: 0, width: '100%' }}
                    onClick={() => { setIsOpen(false); setShowWishlistPopup(true); }}
                  >Wishlist</button>
              }
              {user
                ? <Link to="/cart" className="neuro-mobile-nav-link" onClick={() => setIsOpen(false)}>Cart ({cartCount})</Link>
                : <button
                    className="neuro-mobile-nav-link"
                    style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: 0, width: '100%' }}
                    onClick={() => { setIsOpen(false); setShowCartPopup(true); }}
                  >Cart</button>
              }
              <Link to="/contact" className="neuro-mobile-nav-link" onClick={() => setIsOpen(false)}>Contact</Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
};

export default Navbar;