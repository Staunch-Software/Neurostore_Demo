import React, { useContext } from 'react';
import { ShopContext } from './context/ShopContext';
import { useNavigate } from 'react-router-dom';
import { ShoppingCart, ShoppingBag } from 'lucide-react';
import './wishlist.css';

const Wishlist = () => {
    const { wishlistItems, addToCart, removeFromWishlist, products } = useContext(ShopContext);
    const navigate = useNavigate();

    // Check if there are any items with value > 0
    const hasItems = products.some(p => wishlistItems[p.id] > 0);

    return (
        <div className="wishlist-page-wrapper">
            <div className="wishlist-container">
                <div className="wishlist-header">
                    <h1>My Wishlist</h1>
                </div>

                {hasItems ? (
                    <div className="wishlist-grid">
                        {products.map((product) => {
                            if (wishlistItems[product.id] > 0) {
                                return (
                                    <div className="wishlist-card" key={product.id}>
                                        <div className="wishlist-image-box">
                                            <img src={product.image} alt={product.name} />

                                            {/* FIXED REMOVE BUTTON */}
                                            <button
                                                className="btn-remove-wishlist"
                                                onClick={(e) => {
                                                    e.preventDefault();
                                                    // This calls the function from ShopContext
                                                    removeFromWishlist(product.id);
                                                }}
                                            >
                                                {/* Hardcoded SVG to guarantee X visibility */}
                                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                                </svg>
                                            </button>
                                        </div>

                                        <div className="wishlist-content">
                                            <div className="wishlist-info">
                                                <h3>{product.name}</h3>
                                                <p className="w-category">{product.category}</p>
                                                <div className="w-price">₹{product.price.toLocaleString()}</div>
                                            </div>

                                            <button
                                                className="btn-move-cart"
                                                onClick={() => addToCart(product.id)}
                                            >
                                                <ShoppingCart size={16} /> Add to Cart
                                            </button>
                                        </div>
                                    </div>
                                );
                            }
                            return null;
                        })}
                    </div>
                ) : (
                    <div className="wishlist-empty">
                        <ShoppingBag size={64} strokeWidth={1} color="#ccc" />
                        <h2>Your wishlist is empty</h2>
                        <button onClick={() => navigate("/products")}>
                            Explore Products
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Wishlist;