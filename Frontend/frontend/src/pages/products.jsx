import React, { useContext, useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { createPortal } from 'react-dom';
import SEO from '../components/SEO';
import { ShopContext } from '../components/context/ShopContext';
import { ShoppingCart, ChevronRight, Phone, ChevronLeft, Check, X, Plus, Minus, Trash2, ArrowRight, ShieldCheck as Shield } from 'lucide-react';
import './products.css';
import './ProductDetails.css';

const generateSlug = (text) => {
    if (!text) return '';
    return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');
};

const Products = () => {
    const { products, cartItems, addToCart, removeFromCart, updateCartItemCount, getTotalCartAmount } = useContext(ShopContext);
    const navigate = useNavigate();

    const [justAdded, setJustAdded] = useState({});
    const [showCartDrawer, setShowCartDrawer] = useState(false);

    // No category filtering anymore — show all products
    const filtered = products;

    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 9;

    useEffect(() => {
        if (showCartDrawer) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
        return () => { document.body.style.overflow = ''; };
    }, [showCartDrawer]);

    const indexOfLastItem  = currentPage * itemsPerPage;
    const indexOfFirstItem = indexOfLastItem - itemsPerPage;
    const currentItems     = filtered.slice(indexOfFirstItem, indexOfLastItem);
    const totalPages       = Math.ceil(filtered.length / itemsPerPage);

    const paginate = (pageNumber) => {
        if (pageNumber < 1 || pageNumber > totalPages) return;
        setCurrentPage(pageNumber);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const getPaginationItems = () => {
        if (totalPages <= 7) {
            return Array.from({ length: totalPages }, (_, i) => ({
                type: 'page',
                page: i + 1,
                key: `page-${i + 1}`
            }));
        }

        const items = [];
        items.push({ type: 'page', page: 1, key: 'page-1' });

        const showLeftDots = currentPage > 4;
        const showRightDots = currentPage < totalPages - 3;

        if (!showLeftDots && showRightDots) {
            for (let i = 2; i <= 5; i++) {
                items.push({ type: 'page', page: i, key: `page-${i}` });
            }
            items.push({
                type: 'dots',
                page: Math.min(totalPages, currentPage + 4),
                key: 'dots-right',
                label: 'Jump 4 pages forward'
            });
            items.push({ type: 'page', page: totalPages, key: `page-${totalPages}` });
        } else if (showLeftDots && !showRightDots) {
            items.push({
                type: 'dots',
                page: Math.max(1, currentPage - 4),
                key: 'dots-left',
                label: 'Jump 4 pages backward'
            });
            for (let i = totalPages - 4; i <= totalPages; i++) {
                items.push({ type: 'page', page: i, key: `page-${i}` });
            }
        } else {
            items.push({
                type: 'dots',
                page: Math.max(1, currentPage - 3),
                key: 'dots-left',
                label: 'Jump 3 pages backward'
            });
            for (let i = currentPage - 1; i <= currentPage + 1; i++) {
                items.push({ type: 'page', page: i, key: `page-${i}` });
            }
            items.push({
                type: 'dots',
                page: Math.min(totalPages, currentPage + 3),
                key: 'dots-right',
                label: 'Jump 3 pages forward'
            });
            items.push({ type: 'page', page: totalPages, key: `page-${totalPages}` });
        }

        return items;
    };

    const handleAddToCart = (product) => {
        addToCart(product.id);
        setJustAdded(prev => ({ ...prev, [product.id]: true }));
        setShowCartDrawer(true);
        setTimeout(() => setJustAdded(prev => ({ ...prev, [product.id]: false })), 1500);
    };

    const cartProducts = products.filter(p => (cartItems?.[p.id] || 0) > 0);
    const totalAmount  = getTotalCartAmount();
    const totalItems   = cartProducts.reduce((t, p) => t + (cartItems?.[p.id] || 0), 0);

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
                                        ₹{(p.price * (cartItems?.[p.id] || 0)).toLocaleString()}
                                    </p>
                                    <div className="cart-drawer__qty">
                                        <button onClick={() => removeFromCart(p.id)}>
                                            <Minus size={13} />
                                        </button>
                                        <span>{cartItems?.[p.id] || 0}</span>
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

    // Single static SEO block — no per-category SEO needed anymore
    const currentSEO = {
        title: "Buy AI Hardware & Technology Products Online India | Neurostore",
        description: "Shop AI cameras, GPU servers, AI workstations, developer kits, graphics cards and cybersecurity software at Neurostore India. Best prices with fast delivery.",
        keywords: "buy AI hardware India, AI products online India, GPU server buy India, AI camera price India, AI workstation buy, NVIDIA GPU India, developer kit buy India, AI tech store India"
    };

    return (
        <>
            <SEO
                title={currentSEO.title}
                description={currentSEO.description}
                keywords={currentSEO.keywords}
                ogImage="https://neurostore.in/og-image.webp"
                ogType="website"
            />
        <div className="products-page-wrapper">
            <main className="neuro-products-content">
                <div className="neuro-products-header">
                    <div>
                        <h2>Inventory</h2>
                        <p className="inventory-subtitle">Security, IT operations, and backup solutions</p>
                    </div>
                    <span className="result-indicator">
                        Showing <strong>{filtered.length === 0 ? 0 : indexOfFirstItem + 1}-{Math.min(indexOfLastItem, filtered.length)}</strong> of <strong>{filtered.length}</strong> results
                    </span>
                </div>

                <div className="neuro-products-grid">
                    {currentItems.map(p => {
                        const inCart = cartItems && cartItems[p.id] > 0;
                        const added  = justAdded[p.id];
                        const productUrl = `/products/${generateSlug(p.name)}`;

                        return (
                            <div
                                className="product-card"
                                key={p.id}
                                onClick={() => navigate(productUrl)}
                                role="button"
                                tabIndex={0}
                                onKeyDown={(e) => { if (e.key === 'Enter') navigate(productUrl); }}
                            >
                                <Link to={productUrl} className="product-image-box" onClick={(e) => e.stopPropagation()}>
                                    <img src={p.image} alt={p.name} className="product-image" />
                                    {inCart && (
                                        <span className="cart-count-badge">{cartItems[p.id]}</span>
                                    )}
                                    {p.badge && <span className="p-badge">{p.badge}</span>}
                                </Link>

                                <div className="product-details">
                                    <div className="p-category-row">
                                        <span className="p-category">{p.category}</span>
                                        {p.brand && <span className="p-brand-tag">{p.brand}</span>}
                                    </div>
                                    <h3 className="p-name">
                                        <Link to={productUrl} className="p-name-link" onClick={(e) => e.stopPropagation()}>
                                            {p.name}
                                        </Link>
                                    </h3>

                                    {p.shortDescription && (
                                        <p className="p-card-desc">{p.shortDescription}</p>
                                    )}

                                    {p.features && p.features.length > 0 && (
                                        <ul className="p-card-features">
                                            {p.features.slice(0, 3).map((feat, idx) => (
                                                <li key={idx}><span className="feature-dot">✦</span> {feat}</li>
                                            ))}
                                        </ul>
                                    )}

                                    <div className="p-card-price-row">
                                        <div className="p-card-price">
                                            {!p.enquiryOnly && p.price ? (
                                                <>
                                                    <span className="price-currency">₹</span>
                                                    <span className="price-val">{p.price.toLocaleString()}</span>
                                                    <span className="price-tax">+ 18% GST</span>
                                                </>
                                            ) : (
                                                <span className="price-val" style={{ fontSize: '0.92rem', color: '#6a4c93' }}>Price on Request</span>
                                            )}
                                        </div>
                                        <span className="p-delivery-tag">
                                            {!p.enquiryOnly ? '⚡ Instant Delivery' : 'Enquiry Only'}
                                        </span>
                                    </div>

                                    {!p.enquiryOnly && (
                                        <button
                                            className={`action-btn btn-cart btn-cart--full ${added ? 'btn-cart--added' : ''}`}
                                            onClick={(e) => { e.stopPropagation(); handleAddToCart(p); }}
                                            title={inCart ? `${cartItems[p.id]} in cart` : 'Add to Cart'}
                                        >
                                            {added
                                                ? <><Check size={14} /> Added!</>
                                                : <><ShoppingCart size={14} /> {inCart ? `+1 (${cartItems[p.id]} in cart)` : 'Add to Cart'}</>
                                            }
                                        </button>
                                    )}

                                    <div className="p-action-buttons" onClick={(e) => e.stopPropagation()}>
                                        <a href="tel:+9104422353175" className="action-btn btn-call">
                                            <Phone size={14} /> {p.enquiryOnly ? 'Call' : 'Call for Price'}
                                        </a>

                                        <Link to={productUrl} className="action-btn btn-view">
                                            VIEW
                                        </Link>

                                        <a
                                            href={`https://wa.me/9104422353175?text=Hi, I'm interested in ${encodeURIComponent(p.name)}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="action-btn btn-whatsapp"
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                                                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                                            </svg>
                                            WhatsApp
                                        </a>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {totalPages > 1 && (
                    <div className="pagination-wrapper">
                        <div className="pagination-container">
                            <button
                                className="page-btn nav-btn"
                                onClick={() => paginate(currentPage - 1)}
                                disabled={currentPage === 1}
                                aria-label="Previous Page"
                            >
                                <ChevronLeft size={16} /> Prev
                            </button>

                            <div className="pagination-track">
                                {getPaginationItems().map((item) => {
                                    if (item.type === 'dots') {
                                        return (
                                            <button
                                                key={item.key}
                                                className="page-btn ellipsis-btn"
                                                onClick={() => paginate(item.page)}
                                                title={item.label || 'Jump pages'}
                                                aria-label={item.label || 'Jump pages'}
                                            >
                                                •••
                                            </button>
                                        );
                                    }

                                    return (
                                        <button
                                            key={item.key}
                                            onClick={() => paginate(item.page)}
                                            className={`page-btn number-btn ${currentPage === item.page ? 'active' : ''}`}
                                            aria-label={`Page ${item.page}`}
                                            aria-current={currentPage === item.page ? 'page' : undefined}
                                        >
                                            {item.page}
                                        </button>
                                    );
                                })}
                            </div>

                            <button
                                className="page-btn nav-btn"
                                onClick={() => paginate(currentPage + 1)}
                                disabled={currentPage === totalPages}
                                aria-label="Next Page"
                            >
                                Next <ChevronRight size={16} />
                            </button>
                        </div>
                    </div>
                )}
            </main>

            {cartDrawer}
        </div>
        </>
    );
};

export default Products;



