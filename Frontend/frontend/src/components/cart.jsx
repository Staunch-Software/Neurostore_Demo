import React, { useContext } from 'react';
import { ShopContext } from './context/ShopContext';
import { useNavigate } from 'react-router-dom';
import { Trash2, Plus, Minus, ArrowRight, ShieldCheck, ShoppingBag } from 'lucide-react';
import './cart.css';

const Cart = () => {
    const { cartItems, products, addToCart, removeFromCart, updateCartItemCount, getTotalCartAmount } = useContext(ShopContext);
    const totalAmount = getTotalCartAmount();
    const navigate = useNavigate();

    return (
        <div className="cart-page-wrapper">
            <div className="cart-container">
                <h1 className="cart-page-title">Shopping Cart</h1>

                {totalAmount > 0 ? (
                    <div className="cart-layout-grid">
                        {/* Items List */}
                        <div className="cart-main-content">
                            <div className="cart-table-labels">
                                <span className="label-prod">Item Details</span>
                                <span className="label-qty">Quantity</span>
                                <span className="label-price">Subtotal</span>
                            </div>

                            <div className="cart-items-list">
                                {products.map((product) => {
                                    if (cartItems[product.id] > 0) {
                                        return (
                                            <div className="cart-grid-row" key={product.id}>
                                                {/* Info */}
                                                <div className="item-info-box">
                                                    <img src={product.image} alt={product.name} />
                                                    <div className="item-text">
                                                        <h3>{product.name}</h3>
                                                        <p>{product.category}</p>
                                                        <button onClick={() => updateCartItemCount(0, product.id)} className="remove-btn">
                                                            <Trash2 size={14} /> Remove
                                                        </button>
                                                    </div>
                                                </div>

                                                {/* Quantity (FIXED ICON COLOR) */}
                                                <div className="item-qty-box">
                                                    <div className="qty-pill">
                                                        <button onClick={() => removeFromCart(product.id)}>
                                                            <Minus size={16} color="white" strokeWidth={3} />
                                                        </button>
                                                        <span>{cartItems[product.id]}</span>
                                                        <button onClick={() => addToCart(product.id)}>
                                                            <Plus size={16} color="white" strokeWidth={3} />
                                                        </button>
                                                    </div>
                                                </div>

                                                {/* Price */}
                                                <div className="item-total-box">
                                                    ₹{(product.price * cartItems[product.id]).toLocaleString()}
                                                </div>
                                            </div>
                                        );
                                    }
                                    return null;
                                })}
                            </div>
                        </div>

                        {/* Summary Sidebar */}
                        <div className="cart-sidebar">
                            <div className="summary-card-neuro">
                                <h2>Summary</h2>
                                <div className="sum-row">
                                    <span>Subtotal</span>
                                    <span>₹{totalAmount.toLocaleString()}</span>
                                </div>
                                <div className="sum-row">
                                    <span>Shipping</span>
                                    <span style={{color:'#10b981', fontWeight:'600'}}>Free</span>
                                </div>
                                <div className="sum-row">
                                    <span>Tax (18%)</span>
                                    <span>₹{(totalAmount * 0.18).toLocaleString()}</span>
                                </div>

                                <div className="sum-divider"></div>

                                <div className="sum-total">
                                    <span>Total</span>
                                    <span>₹{(totalAmount * 1.18).toLocaleString()}</span>
                                </div>

                                <button className="checkout-btn-neuro" onClick={() => navigate('/checkout')}>
                                    Proceed to Checkout <ArrowRight size={18}/>
                                </button>
                                <div className="secure-tag">
                                    <ShieldCheck size={14}/> 256-bit SSL Secure
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    /* Empty State */
                    <div className="empty-state-neuro">
                        <ShoppingBag size={64} color="#ccc" style={{marginBottom:'20px'}}/>
                        <h2>Your cart is empty</h2>
                        <button onClick={() => navigate("/products")}>Start Shopping</button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Cart;