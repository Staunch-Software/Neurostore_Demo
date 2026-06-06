import React, { useState, useContext, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import logo from '../assets/logo.ico';
import {
  Phone, Mail, Facebook, Instagram, Linkedin, Twitter,
  Search, X, Heart, ShoppingCart, Menu, ChevronDown, ChevronRight,
  User, LogOut
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
              <div
                className="search-results-dropdown"
                style={{
                  padding: '10px',
                  textAlign: 'center',
                  color: '#666'
                }}
              >
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

  const {
    cartItems,
    getTotalWishlistItems,
    user,
    logout
  } = useContext(ShopContext);

  const navigate = useNavigate();

  const [showUserDropdown, setShowUserDropdown] = useState(false);

  const [isOpen, setIsOpen] = useState(false);
  const [productsOpen, setProductsOpen] = useState(false);
  const [hardwareOpen, setHardwareOpen] = useState(false);
  const [softwareOpen, setSoftwareOpen] = useState(false);

  const cartCount = Object.values(cartItems || {}).reduce(
    (total, qty) => total + (qty > 0 ? qty : 0),
    0
  );

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
            <a href="tel:+18881234567" className="neuro-contact-link">
              <Phone size={14} />
              +91 (044) 22353175
            </a>

            <a href="mailto:info@neurostore.ai" className="neuro-contact-link">
              <Mail size={14} />
              info@neurostore.ai
            </a>
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
              <img
                src={logo}
                alt="NeuroStore Logo"
                className="neuro-logo-img"
              />
            </div>

            <span className="neuro-logo-text">
              NeuroStore - Anything AI
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="neuro-desktop-nav">

            <Link to="/" className="neuro-nav-link">
              Home
            </Link>

            <Link to="/about" className="neuro-nav-link">
              About
            </Link>

            {/* Products Dropdown */}
            <div
              className="neuro-dropdown-wrapper"
              onMouseLeave={() => setProductsOpen(false)}
            >

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

                    <Link
                      to="/products"
                      className="neuro-dropdown-item"
                    >
                      All Products
                    </Link>

                    {/* Hardware */}
                    <div
                      className="neuro-dropdown-item"
                      onMouseEnter={() => setHardwareOpen(true)}
                      onMouseLeave={() => setHardwareOpen(false)}
                    >
                      Hardware <ChevronRight size={14} />

                      {hardwareOpen && (
                        <div className="neuro-dropdown-submenu">
                          {hardwareItems.map(item => (
                            <Link
                              key={item.name}
                              to={item.href}
                              className="neuro-dropdown-item"
                            >
                              {item.name}
                            </Link>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Software */}
                    <div
                      className="neuro-dropdown-item"
                      onMouseEnter={() => setSoftwareOpen(true)}
                      onMouseLeave={() => setSoftwareOpen(false)}
                    >
                      Software <ChevronRight size={14} />

                      {softwareOpen && (
                        <div className="neuro-dropdown-submenu">
                          {softwareItems.map(item => (
                            <Link
                              key={item.name}
                              to={item.href}
                              className="neuro-dropdown-item"
                            >
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

            <Link to="/brands" className="neuro-nav-link">
              Brands
            </Link>

            {/* Actions */}
            <div className="neuro-nav-actions">

              <SearchBar />

              {/* Wishlist */}
              <button
                className="neuro-nav-icon-btn"
                onClick={() => navigate('/wishlist')}
              >
                <Heart size={20} />

                {getTotalWishlistItems() > 0 && (
                  <span className="neuro-badge">
                    {getTotalWishlistItems()}
                  </span>
                )}
              </button>

              {/* Cart */}
              <button
                className="neuro-nav-icon-btn"
                onClick={() => navigate('/cart')}
              >
                <ShoppingCart size={20} />

                {cartCount > 0 && (
                  <span className="neuro-badge">
                    {cartCount}
                  </span>
                )}
              </button>

              {/* User */}
              <div style={{ position: 'relative' }}>

                {user ? (
                  <div
                    onClick={() => setShowUserDropdown(!showUserDropdown)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      cursor: 'pointer',
                      background: 'rgba(255,255,255,0.1)',
                      padding: '6px 12px',
                      borderRadius: '20px',
                      border: '1px solid rgba(255,255,255,0.2)',
                      color: 'white'
                    }}
                  >
                    <User size={16} />

                    <span
                      style={{
                        fontSize: '13px',
                        fontWeight: '600'
                      }}
                    >
                      {user.name.split(' ')[0]}
                    </span>
                  </div>
                ) : (
                  <Link
                    to="/login"
                    className="neuro-nav-icon-btn"
                  >
                    <User size={20} />
                  </Link>
                )}

                {/* ---- ONLY THIS SECTION CHANGED ---- */}
                <AnimatePresence>
                  {showUserDropdown && user && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      className="neuro-user-dropdown"
                    >
                      <p className="neuro-user-dropdown-name">{user.name}</p>
                      <p className="neuro-user-dropdown-email">{user.email}</p>
                      <hr className="neuro-user-dropdown-divider" />

                      <button
                        className="neuro-user-dropdown-btn"
                        onClick={() => {
                          setShowUserDropdown(false);
                          navigate("/profile");
                        }}
                      >
                        <User size={15} />
                        My Profile
                      </button>

                      <button
                        className="neuro-user-dropdown-btn signout"
                        onClick={handleLogout}
                      >
                        <LogOut size={15} />
                        Sign Out
                      </button>

                    </motion.div>
                  )}
                </AnimatePresence>
                {/* ---- END OF CHANGE ---- */}

              </div>

            </div>

            <Link to="/contact" className="neuro-contact-btn">
              Contact Us
            </Link>

          </div>

          {/* Mobile */}
          <div className="neuro-mobile-top-actions">

            <button
              onClick={() => navigate('/cart')}
              style={{
                background: 'none',
                border: 'none',
                padding: 0,
                color: 'white',
                marginRight: '15px',
                position: 'relative',
                cursor: 'pointer'
              }}
            >
              <ShoppingCart size={20} />

              {cartCount > 0 && (
                <span
                  className="neuro-badge"
                  style={{
                    top: '-8px',
                    right: '-8px'
                  }}
                >
                  {cartCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setIsOpen(!isOpen)}
              className="neuro-mobile-menu-btn"
            >
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

              {user ? (
                <div
                  style={{
                    background: '#f8f9fb',
                    padding: '15px',
                    borderRadius: '8px',
                    marginBottom: '15px'
                  }}
                >

                  <p
                    style={{
                      margin: '0 0 10px 0',
                      fontWeight: 'bold',
                      color: '#1a1a1a'
                    }}
                  >
                    Hi, {user.name}
                  </p>

                  <Link
                    to="/profile"
                    onClick={() => setIsOpen(false)}
                    style={{
                      color: '#2563eb',
                      fontWeight: '600',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      marginBottom: '10px',
                      textDecoration: 'none'
                    }}
                  >
                    <User size={14} />
                    My Profile
                  </Link>

                  <button
                    onClick={handleLogout}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#ef4444',
                      fontWeight: '600',
                      padding: 0,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px'
                    }}
                  >
                    <LogOut size={14} />
                    Sign Out
                  </button>

                </div>
              ) : (
                <Link
                  to="/login"
                  className="neuro-mobile-nav-link"
                  onClick={() => setIsOpen(false)}
                >
                  Login / Register
                </Link>
              )}

              <Link
                to="/"
                className="neuro-mobile-nav-link"
                onClick={() => setIsOpen(false)}
              >
                Home
              </Link>

              <Link
                to="/products"
                className="neuro-mobile-nav-link"
                onClick={() => setIsOpen(false)}
              >
                Products
              </Link>

              <Link
                to="/wishlist"
                className="neuro-mobile-nav-link"
                onClick={() => setIsOpen(false)}
              >
                Wishlist
              </Link>

              <Link
                to="/cart"
                className="neuro-mobile-nav-link"
                onClick={() => setIsOpen(false)}
              >
                Cart ({cartCount})
              </Link>

              <Link
                to="/contact"
                className="neuro-mobile-nav-link"
                onClick={() => setIsOpen(false)}
              >
                Contact
              </Link>

            </div>

          </motion.div>
        )}
      </AnimatePresence>

    </motion.nav>
  );
};

export default Navbar;   