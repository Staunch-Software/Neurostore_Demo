import React, { useContext, useState, useMemo, useEffect } from 'react';
import { Link, useNavigate, useParams, useLocation } from 'react-router-dom';
import { createPortal } from 'react-dom';
import SEO from '../components/SEO';
import { ShopContext } from '../components/context/ShopContext';
import { ShoppingCart, SlidersHorizontal, ChevronRight, Phone, ChevronLeft, Check, X, Plus, Minus, Trash2, ArrowRight, ShieldCheck as Shield } from 'lucide-react';
import './products.css';
import './ProductDetails.css';

const generateSlug = (text) => {
    if (!text) return '';
    return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');
};

const Products = () => {
    const { products, cartItems, addToCart, removeFromCart, updateCartItemCount, getTotalCartAmount } = useContext(ShopContext);
    const [selectedCategory, setSelectedCategory] = useState("All");
    const [justAdded, setJustAdded] = useState({});
    const [showCartDrawer, setShowCartDrawer] = useState(false);
    const { category } = useParams();
    const navigate = useNavigate();
    const { pathname } = useLocation(); 

    useEffect(() => {
        if (category) {
            const matched = products.find(p => generateSlug(p.category) === category);
            setSelectedCategory(matched ? matched.category : "All");
        } else {
            setSelectedCategory("All");
        }
    }, [category, products]);

    const [priceRange, setPriceRange] = useState(600000);
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 9;

    const categories = useMemo(() => ["All", ...new Set(products.map(p => p.category))], [products]);

    const filtered = products.filter(p =>
        (selectedCategory === "All" || p.category === selectedCategory) && p.price <= priceRange
    );

    useEffect(() => {
        setCurrentPage(1);
    }, [selectedCategory, priceRange]);

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
        setCurrentPage(pageNumber);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const handleAddToCart = (product) => {
        addToCart(product.id);
        setJustAdded(prev => ({ ...prev, [product.id]: true }));
        setShowCartDrawer(true);
        setTimeout(() => setJustAdded(prev => ({ ...prev, [product.id]: false })), 1500);
    };

    const cartProducts = products.filter(p => cartItems[p.id] > 0);
    const totalAmount  = getTotalCartAmount();
    const totalItems   = cartProducts.reduce((t, p) => t + cartItems[p.id], 0);

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


    const categorySEO = {
  "All": {
    title: "Buy AI Hardware & Technology Products Online India | Neurostore",
    description: "Shop AI cameras, GPU servers, AI workstations, developer kits, graphics cards and cybersecurity software at Neurostore India. Best prices with fast delivery.",
    keywords: "buy AI hardware India, AI products online India, GPU server buy India, AI camera price India, AI workstation buy, NVIDIA GPU India, developer kit buy India, AI tech store India"
  },
  "AI Vision Security": {
    title: "Buy AI Security Cameras & Vision Systems India | Neurostore",
    description: "Buy AI-powered security cameras, UniFi cameras and intelligent vision systems at Neurostore India. Best prices on AI surveillance cameras with fast delivery.",
    keywords: "buy AI security camera India, UniFi camera price India, AI surveillance camera India, intelligent vision system India, IP camera buy India, AI CCTV India"
  },
  "AI Networking Storage": {
    title: "Buy AI Networking & Storage Solutions India | Neurostore",
    description: "Buy AI networking equipment and enterprise storage solutions at Neurostore India. High performance NAS, switches and AI-ready network infrastructure.",
    keywords: "buy AI storage India, AI networking India, enterprise NAS India, AI network switch India, storage server India, AI infrastructure India"
  },
  "AI Workstations And Servers": {
    title: "Buy AI Workstations & GPU Servers India | Neurostore",
    description: "Buy high-performance AI workstations and GPU servers for deep learning and machine learning at Neurostore India. NVIDIA powered, India delivery.",
    keywords: "buy AI workstation India, GPU server price India, deep learning workstation India, ML server buy India, AI compute server India, NVIDIA workstation India"
  },
  "AI Dev Boards": {
    title: "Buy AI Developer Kits & Dev Boards India | Neurostore",
    description: "Buy Raspberry Pi 5, Jetson Nano, AI dev boards and embedded AI kits at Neurostore India. Best prices on AI developer hardware with fast shipping.",
    keywords: "buy Raspberry Pi 5 India, Jetson Nano price India, AI dev board India, embedded AI kit India, developer board buy India, AI hardware kit India"
  },
  "AI Graphics Cards": {
    title: "Buy NVIDIA & AMD AI Graphics Cards India | Neurostore",
    description: "Buy NVIDIA RTX 5090, RTX 4070 Ti and latest AI graphics cards at Neurostore India. Best GPU prices for gaming, AI training and deep learning workloads.",
    keywords: "buy NVIDIA RTX 5090 India, GPU price India, buy RTX 4070 Ti India, AI graphics card India, NVIDIA GPU buy India, AMD GPU India, best GPU price India"
  },
  "AI Software": {
    title: "Buy AI Software & Machine Learning Tools India | Neurostore",
    description: "Buy AI software, machine learning tools and deep learning frameworks at Neurostore India. Licensed AI software at best prices for enterprise and developers.",
    keywords: "buy AI software India, machine learning tools India, deep learning software India, AI framework license India, enterprise AI software India"
  },
  "AI Accessories": {
    title: "Buy AI Accessories & Peripheral Devices India | Neurostore",
    description: "Buy AI accessories, cables, cooling solutions and peripheral devices for your AI setup at Neurostore India. Fast delivery across India.",
    keywords: "buy AI accessories India, AI peripheral devices India, GPU cooling India, AI setup accessories India, tech accessories India"
  }
};

const currentSEO = categorySEO[selectedCategory] || categorySEO["All"];


    return (
        <>
            <SEO
                title={currentSEO.title}
                description={currentSEO.description}
                keywords={currentSEO.keywords}
                ogImage="https://www.neurostore.in/og-image.webp"
                ogType="website"
            />
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
                        <span className="price-tag">₹{(priceRange / 1000).toFixed(0)}k</span>
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
                    {currentItems.map(p => {
                        const inCart = cartItems && cartItems[p.id] > 0;
                        const added  = justAdded[p.id];
                        return (
                            <div className="product-card" key={p.id}>
                                <div className="product-image-box">
                                    <img src={p.image} alt={p.name} className="product-image" />
                                    {inCart && (
                                        <span className="cart-count-badge">{cartItems[p.id]}</span>
                                    )}
                                    {p.badge && <span className="p-badge">{p.badge}</span>}
                                </div>

                                <div className="product-details">
                                    <span className="p-category">{p.category}</span>
                                    <h3 className="p-name">{p.name}</h3>

                                    <button
                                        className={`action-btn btn-cart btn-cart--full ${added ? 'btn-cart--added' : ''}`}
                                        onClick={() => handleAddToCart(p)}
                                        title={inCart ? `${cartItems[p.id]} in cart` : 'Add to Cart'}
                                    >
                                        {added
                                            ? <><Check size={14} /> Added!</>
                                            : <><ShoppingCart size={14} /> {inCart ? `+1 (${cartItems[p.id]} in cart)` : 'Add to Cart'}</>
                                        }
                                    </button>

                                    <div className="p-action-buttons">
                                        <a href="tel:+9104422353175" className="action-btn btn-call">
                                            <Phone size={14} /> Call for Price
                                        </a>

                                        <Link to={`/products/${generateSlug(p.category)}/${generateSlug(p.name)}`} className="action-btn btn-view">
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

            {cartDrawer}
        </div>
        </>
    );
};

export default Products;