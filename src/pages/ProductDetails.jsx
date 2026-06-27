import React, { useContext, useState, useEffect } from 'react';
import SEO from '../components/SEO';      
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom';
import { createPortal } from 'react-dom';
import { ShopContext } from '../components/context/ShopContext';
import { Phone, CheckCircle2, Truck, Package, ShieldCheck, Mail, ChevronLeft, ShoppingCart, Check, Heart, X, Plus, Minus, Trash2, ArrowRight, ShieldCheck as Shield } from 'lucide-react';
import './ProductDetails.css';

const generateSlug = (text) => {
    if (!text) return '';
    return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');
};

const ProductDetails = () => {
    const { category, productName } = useParams();
    const { products, cartItems, addToCart, removeFromCart, updateCartItemCount, getTotalCartAmount, wishlistItems, toggleWishlist } = useContext(ShopContext);
    const navigate = useNavigate();
    const { pathname } = useLocation(); 
    const [activeTab, setActiveTab]       = useState('description');
    const [showModal, setShowModal]       = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [showSuccess, setShowSuccess]   = useState(false);
    const [justAdded, setJustAdded]       = useState(false);
    const [wishlistAnim, setWishlistAnim] = useState(false);
    const [showCartDrawer, setShowCartDrawer] = useState(false);

    const handleAddToCart = () => {
        addToCart(product.id);
        setJustAdded(true);
        setShowCartDrawer(true);
        setTimeout(() => setJustAdded(false), 1800);
    };

    const handleWishlist = () => {
        toggleWishlist(product.id);
        setWishlistAnim(true);
        setTimeout(() => setWishlistAnim(false), 300);
    };

    useEffect(() => {
        window.scrollTo(0, 0);
    }, [productName]);

    useEffect(() => {
        if (showCartDrawer) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
        return () => { document.body.style.overflow = ''; };
    }, [showCartDrawer]);

    const product = products.find((p) => generateSlug(p.name) === productName);

    if (!product) {
        return (
            <div className="product-not-found">
                Product not found! <Link to="/products">Go back</Link>
            </div>
        );
    }

    const inCart       = cartItems && cartItems[product.id] > 0;
    const cartCount    = cartItems?.[product.id] || 0;
    const isWishlisted = wishlistItems?.[product.id] > 0;

    const cartProducts = products.filter(p => cartItems[p.id] > 0);
    const totalAmount  = getTotalCartAmount();
    const totalItems   = cartProducts.reduce((t, p) => t + cartItems[p.id], 0);

    const handleInquirySubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        const inquiryData = {
            name:    e.target.name.value,
            email:   e.target.email.value,
            phone:   e.target.phone.value || 'Not Provided',
            product: `[Product Page Inquiry] ${product.name}`,
            message: e.target.message.value
        };
        try {
            const response = await fetch('https://www.neurostore.in/api/inquiry', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify(inquiryData)
            });
            if (response.ok) {
                setShowSuccess(true);
                setShowModal(false);
                e.target.reset();
            } else {
                alert('Failed to send inquiry.');
            }
        } catch (error) {
            console.error('Backend Error:', error);
            alert('Could not connect to the backend server.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const cartDrawer = createPortal(
        <>
            <div
                className={`cart-drawer-overlay ${showCartDrawer ? 'cart-drawer-overlay--open' : ''}`}
                onClick={() => setShowCartDrawer(false)}
            />
            <div className={`cart-drawer ${showCartDrawer ? 'cart-drawer--open' : ''}`}>
                <div className="cart-drawer__header">
                    <div className="cart-drawer__header-left">
                        <ShoppingCart size={20} />
                        <span>Your Cart</span>
                        {totalItems > 0 && <span className="cart-drawer__badge">{totalItems}</span>}
                    </div>
                    <button className="cart-drawer__close" onClick={() => setShowCartDrawer(false)}>
                        <X size={20} />
                    </button>
                </div>
                <div className="cart-drawer__body">
                    {cartProducts.length === 0 ? (
                        <div className="cart-drawer__empty">
                            <ShoppingCart size={48} color="#ddd" />
                            <p>Your cart is empty</p>
                        </div>
                    ) : (
                        cartProducts.map(p => (
                            <div className="cart-drawer__item" key={p.id}>
                                <div className="cart-drawer__item-img">
                                    <img src={p.image} alt={p.name} />
                                </div>
                                <div className="cart-drawer__item-info">
                                    <p className="cart-drawer__item-name">{p.name}</p>
                                    <p className="cart-drawer__item-cat">{p.category}</p>
                                    <p className="cart-drawer__item-price">
                                        ₹{(p.price * cartItems[p.id]).toLocaleString()}
                                    </p>
                                    <div className="cart-drawer__qty">
                                        <button onClick={() => removeFromCart(p.id)}>
                                            <Minus size={13} />
                                        </button>
                                        <span>{cartItems[p.id]}</span>
                                        <button onClick={() => addToCart(p.id)}>
                                            <Plus size={13} />
                                        </button>
                                        <button
                                            className="cart-drawer__remove"
                                            onClick={() => updateCartItemCount(0, p.id)}
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
                {cartProducts.length > 0 && (
                    <div className="cart-drawer__footer">
                        <div className="cart-drawer__summary">
                            <div className="cart-drawer__summary-row">
                                <span>Subtotal</span>
                                <span>₹{totalAmount.toLocaleString()}</span>
                            </div>
                            <div className="cart-drawer__summary-row">
                                <span>Tax (18%)</span>
                                <span>₹{(totalAmount * 0.18).toLocaleString()}</span>
                            </div>
                            <div className="cart-drawer__summary-row cart-drawer__summary-row--total">
                                <span>Total</span>
                                <span>₹{(totalAmount * 1.18).toLocaleString()}</span>
                            </div>
                        </div>
                        <button
                            className="cart-drawer__checkout-btn"
                            onClick={() => { setShowCartDrawer(false); navigate('/checkout'); }}
                        >
                            Proceed to Checkout <ArrowRight size={18} />
                        </button>
                        <button
                            className="cart-drawer__view-btn"
                            onClick={() => { setShowCartDrawer(false); navigate('/cart'); }}
                        >
                            View Full Cart
                        </button>
                        <div className="cart-drawer__secure">
                            <Shield size={13} /> 256-bit SSL Secure Checkout
                        </div>
                    </div>
                )}
            </div>
        </>,
        document.body
    );

    return (
        <>
            <SEO
                title={`Buy ${product.name} in India | Neurostore`}
                description={`Buy ${product.name} at Neurostore India. ${product.shortDescription || ''} Call for best price, fast delivery across India. Genuine product with warranty.`}
                keywords={`buy ${product.name} India, ${product.name} price India, ${product.name} online India, ${product.brand || ''} ${product.name}, ${product.category || ''} India, neurostore`}
                ogImage={product.image || "https://www.neurostore.in/og-image.webp"}
                ogType="product"
            />
        <div className="product-details-wrapper">
            <div className="container">

                <Link to="/products" className="back-link">
                    <ChevronLeft size={16} /> Back to Inventory
                </Link>

                <div className="pd-top-section">

                    <div className="pd-image-col">
                        <img src={product.image} alt={product.name} />
                    </div>

                    <div className="pd-info-col">

                        <div className="pd-title-row">
                            <h1 className="pd-title">{product.name}</h1>

                            {/* ── CHANGED: size 22→30, stroke #94a3b8→#475569, strokeWidth 2→2.5, button 48px→62px ── */}
                            <button
                                className={`pd-wishlist-btn ${isWishlisted ? 'pd-wishlist-btn--active' : ''} ${wishlistAnim ? 'pd-wishlist-btn--pop' : ''}`}
                                onClick={handleWishlist}
                                aria-label={isWishlisted ? 'Remove from wishlist' : 'Add to wishlist'}
                            >
                                <Heart
                                    size={30}
                                    fill={isWishlisted ? '#ef4444' : 'none'}
                                    stroke={isWishlisted ? '#ef4444' : '#475569'}
                                    strokeWidth={2.5}
                                />
                            </button>
                        </div>

                        <p className="pd-short-desc">{product.shortDescription}</p>

                        <div className="pd-action-row">
                            <a href="tel:+9104422353175" className="pd-call-btn">
                                <Phone size={16} /> Call for Price
                            </a>
                            <a
                                href={`https://wa.me/9104422353175?text=Hi, I'm interested in ${encodeURIComponent(product.name)}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="pd-call-btn pd-whatsapp-btn"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                                </svg>
                                WhatsApp
                            </a>
                            {product.moq && (
                                <span className="pd-moq-badge">MOQ: {product.moq}</span>
                            )}
                        </div>

                        <div className="pd-meta">
                            <p><strong>Category:</strong> {product.category}</p>
                            <p><strong>Brand:</strong> {product.brand}</p>
                        </div>

                        <div className="pd-features">
                            <span><CheckCircle2 size={16} color="#10b981" /> 100% Genuine</span>
                            <span><Truck        size={16} color="#10b981" /> Fast Delivery</span>
                            <span><Package      size={16} color="#10b981" /> Bulk Discount</span>
                            <span><ShieldCheck  size={16} color="#10b981" /> Secure Checkout</span>
                        </div>

                        <button
                            onClick={handleAddToCart}
                            className={`pd-cart-btn ${justAdded ? 'pd-cart-btn--added' : ''} ${inCart ? 'pd-cart-btn--in-cart' : ''}`}
                        >
                            {justAdded ? (
                                <><Check size={18} /> Added to Cart!</>
                            ) : inCart ? (
                                <><ShoppingCart size={18} /> Add More ({cartCount} in cart)</>
                            ) : (
                                <><ShoppingCart size={18} /> ADD TO CART</>
                            )}
                        </button>

                        <button onClick={() => setShowModal(true)} className="pd-inquiry-btn">
                            <Mail size={18} /> SEND INQUIRY
                        </button>

                        <div className="pd-logistics">
                            <div className="pd-logistic-item">
                                <strong>PAYMENT:</strong>
                                <div className="logistic-icons">💳 PayPal 💳 Visa 💳 Mastercard</div>
                            </div>
                            <div className="pd-logistic-item">
                                <strong>SHIPPING:</strong>
                                <div className="logistic-icons">✈️ DHL ✈️ FedEx ✈️ UPS</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="pd-bottom-section">
                    <div className="pd-tabs-header">
                        <button className={`pd-tab-btn ${activeTab === 'description' ? 'active' : ''}`} onClick={() => setActiveTab('description')}>Description</button>
                        <button className={`pd-tab-btn ${activeTab === 'additional'  ? 'active' : ''}`} onClick={() => setActiveTab('additional')}>Additional Information</button>
                        <button className={`pd-tab-btn ${activeTab === 'warranty'    ? 'active' : ''}`} onClick={() => setActiveTab('warranty')}>Warranty</button>
                    </div>
                    <div className="pd-tab-content">
                        {activeTab === 'description' && (
                            <div className="tab-pane">
                                <h2>Product Description</h2>
                                <p>{product.description || 'No detailed description available.'}</p>
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
                                ) : <p>No additional info provided.</p>}
                            </div>
                        )}
                        {activeTab === 'warranty' && (
                            <div className="tab-pane">
                                <h2>Warranty</h2>
                                <p>{product.warranty || 'Please contact support for warranty details.'}</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {cartDrawer}

            {showModal && (
                <div className="pd-modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="pd-modal-box" onClick={(e) => e.stopPropagation()}>
                        <button className="pd-modal-close" onClick={() => setShowModal(false)}>✕</button>
                        <h2 className="pd-modal-title">Product Inquiry</h2>
                        <p className="pd-modal-subtitle">
                            You are inquiring about: <br /><strong>{product.name}</strong>
                        </p>
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

            {showSuccess && (
                <div className="pd-modal-overlay" onClick={() => setShowSuccess(false)}>
                    <div className="pd-modal-box pd-success-box" onClick={(e) => e.stopPropagation()}>
                        <button className="pd-modal-close" onClick={() => setShowSuccess(false)}>✕</button>
                        <div className="pd-success-icon">✓</div>
                        <h2 className="pd-modal-title">Inquiry Sent!</h2>
                        <p className="pd-modal-subtitle">
                            We've received your request regarding <strong>{product.name}</strong>.
                            Our sales team will email you shortly.
                        </p>
                        <button className="pd-modal-submit-btn" onClick={() => setShowSuccess(false)}>Close</button>
                    </div>
                </div>
            )}

        </div>
        </>
    );
};

export default ProductDetails;