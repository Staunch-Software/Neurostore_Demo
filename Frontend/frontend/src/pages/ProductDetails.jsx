import React, { useContext, useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ShopContext } from '../components/context/ShopContext';
import { Phone, CheckCircle2, Truck, Package, ShieldCheck, Mail, ChevronLeft, Heart, X } from 'lucide-react';
import './ProductDetails.css';

// Helper function to create clean SEO-friendly URLs to match your products page
const generateSlug = (text) => {
    if (!text) return '';
    return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');
};

const ProductDetails = () => {
    const { category, productName } = useParams();
    const { products, wishlistItems, toggleWishlistUnguarded, user } = useContext(ShopContext);
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('description');

    // Inquiry Modal State
    const [showModal,     setShowModal]     = useState(false);
    const [isSubmitting,  setIsSubmitting]  = useState(false);
    const [showSuccess,   setShowSuccess]   = useState(false);
    const [showLoginPopup, setShowLoginPopup] = useState(false);

    const handleHeartClick = () => {
        if (!user) { setShowLoginPopup(true); return; }
        toggleWishlistUnguarded(product.id);
    };

    // Scroll to top when loading a new product
    useEffect(() => {
        window.scrollTo(0, 0);
    }, [productName]);

    const product = products.find((p) => generateSlug(p.name) === productName);

    if (!product) {
        return <div className="product-not-found">Product not found! <Link to="/products">Go back</Link></div>;
    }

    // Handle Inquiry Form Submission
    const handleInquirySubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);

        const inquiryData = {
            name: e.target.name.value,
            email: e.target.email.value,
            phone: e.target.phone.value || "Not Provided",
            product: `[Product Page Inquiry] ${product.name}`, // Auto-attaches the product name!
            message: e.target.message.value
        };

        try {
            const response = await fetch("http://localhost:5000/api/inquiry", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(inquiryData)
            });

            if (response.ok) {
                setShowSuccess(true);
                setShowModal(false);
                e.target.reset();
            } else {
                alert("Failed to send inquiry.");
            }
        } catch (error) {
            console.error("Backend Error:", error);
            alert("Could not connect to the backend server. Please ensure app.py is running!");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="product-details-wrapper">
            <div className="container">
                {/* Breadcrumb / Back Button */}
                <Link to="/products" className="back-link">
                    <ChevronLeft size={16} /> Back to Inventory
                </Link>

                {/* Top Section: Image and Info */}
                <div className="pd-top-section">
                    {/* Left: Image */}
                    <div className="pd-image-col">
                        <img src={product.image} alt={product.name} />
                    </div>

                    {/* Right: Info */}
                    <div className="pd-info-col">
                        <h1 className="pd-title">{product.name}</h1>
                        <p className="pd-short-desc">{product.shortDescription}</p>

                        <div className="pd-action-row">
                            <a href="tel:+9104422353175" className="pd-call-btn">
                                <Phone size={16} /> Call for Price
                            </a>
                            <button
                                className={`pd-wishlist-btn ${wishlistItems[product?.id] ? 'pd-wishlist-btn--active' : ''}`}
                                onClick={handleHeartClick}
                                title={wishlistItems[product?.id] ? 'Remove from Wishlist' : 'Add to Wishlist'}
                            >
                                <Heart
                                    size={20}
                                    fill={wishlistItems[product?.id] ? '#ff4757' : 'transparent'}
                                    color={wishlistItems[product?.id] ? '#ff4757' : 'currentColor'}
                                    strokeWidth={2}
                                />
                            </button>
                            {product.moq && <span className="pd-moq-badge">MOQ: {product.moq}</span>}
                        </div>

                        <div className="pd-meta">
                            <p><strong>Category:</strong> {product.category}</p>
                            <p><strong>Brand:</strong> {product.brand}</p>
                        </div>

                        {/* Feature Ticks */}
                        <div className="pd-features">
                            <span><CheckCircle2 size={16} color="#10b981" /> 100% Genuine</span>
                            <span><Truck size={16} color="#10b981" /> Fast Delivery</span>
                            <span><Package size={16} color="#10b981" /> Bulk Discount</span>
                            <span><ShieldCheck size={16} color="#10b981" /> Secure Checkout</span>
                        </div>

                        {/* Updated Inquiry Button (Opens Modal) */}
                        <button onClick={() => setShowModal(true)} className="pd-inquiry-btn">
                            <Mail size={18} /> SEND INQUIRY
                        </button>

                        {/* Payment & Shipping Icons */}
                        <div className="pd-logistics">
                            <div className="pd-logistic-item">
                                <strong>PAYMENT:</strong>
                                <div className="logistic-icons">
                                    💳 PayPal 💳 Visa 💳 Mastercard
                                </div>
                            </div>
                            <div className="pd-logistic-item">
                                <strong>SHIPPING:</strong>
                                <div className="logistic-icons">
                                    ✈️ DHL ✈️ FedEx ✈️ UPS
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Bottom Section: Tabs */}
                <div className="pd-bottom-section">
                    <div className="pd-tabs-header">
                        <button
                            className={`pd-tab-btn ${activeTab === 'description' ? 'active' : ''}`}
                            onClick={() => setActiveTab('description')}
                        >
                            Description
                        </button>
                        <button
                            className={`pd-tab-btn ${activeTab === 'additional' ? 'active' : ''}`}
                            onClick={() => setActiveTab('additional')}
                        >
                            Additional Information
                        </button>
                        <button
                            className={`pd-tab-btn ${activeTab === 'warranty' ? 'active' : ''}`}
                            onClick={() => setActiveTab('warranty')}
                        >
                            Warranty
                        </button>
                    </div>

                    <div className="pd-tab-content">
                        {activeTab === 'description' && (
                            <div className="tab-pane">
                                <h2>Product Description</h2>
                                <p>{product.description || "No detailed description available."}</p>
                            </div>
                        )}

                        {activeTab === 'additional' && (
                            <div className="tab-pane">
                                <h2>Additional Information</h2>
                                {product.additionalInfo ? (
                                    <table className="pd-info-table">
                                        <tbody>
                                            {Object.entries(product.additionalInfo).map(([key, value]) => (
                                                <tr key={key}>
                                                    <td className="table-key">{key}</td>
                                                    <td className="table-value">{value}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                ) : (
                                    <p>No additional info provided.</p>
                                )}
                            </div>
                        )}

                        {activeTab === 'warranty' && (
                            <div className="tab-pane">
                                <h2>Warranty</h2>
                                <p>{product.warranty || "Please contact support for warranty details."}</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* --- INQUIRY MODAL --- */}
            {showModal && (
                <div className="pd-modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="pd-modal-box" onClick={(e) => e.stopPropagation()}>
                        <button className="pd-modal-close" onClick={() => setShowModal(false)}>✕</button>
                        <h2 className="pd-modal-title">Product Inquiry</h2>
                        <p className="pd-modal-subtitle">You are inquiring about: <br/><strong>{product.name}</strong></p>

                        <form onSubmit={handleInquirySubmit} className="pd-modal-form">
                            <div className="pd-form-group">
                                <label>Full Name *</label>
                                <input type="text" name="name" required placeholder="John Doe" />
                            </div>
                            <div className="pd-form-group">
                                <label>Email Address *</label>
                                <input type="email" name="email" required placeholder="john@example.com" />
                            </div>
                            <div className="pd-form-group">
                                <label>Phone Number</label>
                                <input type="tel" name="phone" placeholder="+1 234 567 890" />
                            </div>
                            <div className="pd-form-group">
                                <label>Your Message *</label>
                                <textarea name="message" required rows="4" placeholder="What details do you need about this product?"></textarea>
                            </div>
                            <button type="submit" className="pd-modal-submit-btn" disabled={isSubmitting}>
                                {isSubmitting ? 'Sending Request...' : 'Send Inquiry'}
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* --- WISHLIST LOGIN POPUP --- */}
            {showLoginPopup && !user && (
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

            {/* --- SUCCESS MODAL --- */}
            {showSuccess && (
                <div className="pd-modal-overlay" onClick={() => setShowSuccess(false)}>
                    <div className="pd-modal-box pd-success-box" onClick={(e) => e.stopPropagation()}>
                        <button className="pd-modal-close" onClick={() => setShowSuccess(false)}>✕</button>
                        <div className="pd-success-icon">✓</div>
                        <h2 className="pd-modal-title">Inquiry Sent!</h2>
                        <p className="pd-modal-subtitle">We've received your request regarding <strong>{product.name}</strong>. Our sales team will email you shortly.</p>
                        <button className="pd-modal-submit-btn" onClick={() => setShowSuccess(false)}>Close</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProductDetails;