import React, { useContext, useState, useMemo, useEffect } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ShopContext } from '../components/context/ShopContext';
import { Heart, SlidersHorizontal, ChevronRight, Phone, ChevronLeft, X } from 'lucide-react';
import './products.css';

// Helper function to create clean SEO-friendly URLs (e.g., "Vision & Security" -> "vision-security")
const generateSlug = (text) => {
    if (!text) return '';
    return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');
};

const Products = () => {
    const { products, wishlistItems, toggleWishlistUnguarded, user } = useContext(ShopContext);
    const [selectedCategory, setSelectedCategory] = useState("All");
    const [showLoginPopup, setShowLoginPopup] = useState(false);

    const handleHeartClick = (id) => {
        if (!user) { setShowLoginPopup(true); return; }
        toggleWishlistUnguarded(id);
    };

    // Sync state with URL param
    const { category } = useParams();
    const navigate = useNavigate();

    useEffect(() => {
        if (category) {
            // Find a product that matches this category slug to get the exact category name
            const matched = products.find(p => generateSlug(p.category) === category);
            setSelectedCategory(matched ? matched.category : "All");
        } else {
            setSelectedCategory("All");
        }
    }, [category, products]);

    // Default 600k to cover your most expensive items
    const [priceRange, setPriceRange] = useState(600000);

    // --- PAGINATION STATES ---
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 9; // Shows 9 items per page

    const categories = useMemo(() => ["All", ...new Set(products.map(p => p.category))], [products]);

    const filtered = products.filter(p =>
        (selectedCategory === "All" || p.category === selectedCategory) && p.price <= priceRange
    );

    // Reset to page 1 whenever a filter is changed
    useEffect(() => {
        setCurrentPage(1);
    }, [selectedCategory, priceRange]);

    // --- PAGINATION MATH ---
    const indexOfLastItem = currentPage * itemsPerPage;
    const indexOfFirstItem = indexOfLastItem - itemsPerPage;
    const currentItems = filtered.slice(indexOfFirstItem, indexOfLastItem);
    const totalPages = Math.ceil(filtered.length / itemsPerPage);

    const paginate = (pageNumber) => {
        setCurrentPage(pageNumber);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    return (
        <div className="products-page-wrapper">
            <aside className="neuro-sidebar">
                <div className="sidebar-header">
                    <SlidersHorizontal size={18} />
                    <h3 className="neuro-filter-title">Filter Options</h3>
                </div>

                <div className="filter-section">
                    <h4>Collections</h4>
                    <div className="category-pills">
                        {categories.map(cat => (
                            <button
                                key={cat}
                                className={`pill-btn ${selectedCategory === cat ? 'active' : ''}`}
                               onClick={() => navigate(cat === "All" ? "/products" : `/products/${generateSlug(cat)}`)}
                            >
                                {cat}
                                <ChevronRight size={14} className="pill-arrow" />
                            </button>
                        ))}
                    </div>
                </div>

                <div className="filter-section">
                    <div className="price-info">
                        <h4>Price Range</h4>
                        <span className="price-tag">₹{(priceRange/1000).toFixed(0)}k</span>
                    </div>
                    <div className="slider-wrapper">
                        <input
                            type="range"
                            min="0" max="600000" step="10000"
                            value={priceRange}
                            onChange={(e) => setPriceRange(Number(e.target.value))}
                            className="neuro-slider"
                        />
                    </div>
                </div>
            </aside>

            <main className="neuro-products-content">
                <div className="neuro-products-header">
                    <h2>Inventory</h2>
                    <span className="result-indicator">
                        Showing <strong>{filtered.length === 0 ? 0 : indexOfFirstItem + 1}-{Math.min(indexOfLastItem, filtered.length)}</strong> of <strong>{filtered.length}</strong> results
                    </span>
                </div>

                <div className="neuro-products-grid">
                    {currentItems.map(p => (
                        <div className="product-card" key={p.id}>
                            <div className="product-image-box">
                                <img src={p.image} alt={p.name} className="product-image" />

                                <button
                                    className={`wishlist-heart-btn ${wishlistItems[p.id] ? 'is-liked' : ''}`}
                                    onClick={() => handleHeartClick(p.id)}
                                >
                                    <Heart
                                        size={28}
                                        fill={wishlistItems[p.id] ? "#ff4757" : "transparent"}
                                        color={wishlistItems[p.id] ? "#ff4757" : "#1a1a1a"}
                                        strokeWidth={2.5}
                                    />
                                </button>

                                {p.badge && <span className="p-badge">{p.badge}</span>}
                            </div>

                            <div className="product-details">
                                <span className="p-category">{p.category}</span>
                                <h3 className="p-name">{p.name}</h3>

                                <div className="p-action-buttons">
                                    <a href="tel:+9104422353175" className="action-btn btn-call">
                                        <Phone size={14} /> Call for Price
                                    </a>

                                    <Link to={`/products/${generateSlug(p.category)}/${generateSlug(p.name)}`} className="action-btn btn-view">
                                        VIEW
                                    </Link>

                                    <a
                                        href={`https://wa.me/919384813815?text=Hi! I'm interested in the ${encodeURIComponent(p.name)}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="action-btn btn-wa"
                                    >
                                        WhatsApp
                                    </a>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {totalPages > 1 && (
                    <div className="pagination-container">
                        <button
                            className="page-btn nav-btn"
                            onClick={() => paginate(currentPage - 1)}
                            disabled={currentPage === 1}
                        >
                            <ChevronLeft size={16} /> Prev
                        </button>

                        {[...Array(totalPages)].map((_, i) => (
                            <button
                                key={i + 1}
                                onClick={() => paginate(i + 1)}
                                className={`page-btn ${currentPage === i + 1 ? 'active' : ''}`}
                            >
                                {i + 1}
                            </button>
                        ))}

                        <button
                            className="page-btn nav-btn"
                            onClick={() => paginate(currentPage + 1)}
                            disabled={currentPage === totalPages}
                        >
                            Next <ChevronRight size={16} />
                        </button>
                    </div>
                )}
            </main>

            {/* ── Wishlist login popup ── */}
            {showLoginPopup && (
                <div className="wl-popup-overlay" onClick={() => setShowLoginPopup(false)}>
                    <div className="wl-popup-card" onClick={e => e.stopPropagation()}>
                        <button className="wl-popup-close" onClick={() => setShowLoginPopup(false)}>
                            <X size={16} />
                        </button>
                        <div className="wl-popup-icon">
                            <Heart size={32} fill="#818cf8" color="#818cf8" />
                        </div>
                        <h3 className="wl-popup-title">Sign in to save to Wishlist</h3>
                        <p className="wl-popup-sub">Login or create an account to save your favourite AI products.</p>
                        <button
                            className="wl-popup-btn"
                            onClick={() => { setShowLoginPopup(false); navigate('/login'); }}
                        >
                            Login / Register
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Products;