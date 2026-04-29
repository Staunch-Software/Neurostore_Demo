import React, { createContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
// We import local products ONLY to match the local Webpack images to the database data!
import { products as localImageMap } from "../../assets/products";

export const ShopContext = createContext(null);

export const ShopContextProvider = (props) => {
    const navigate = useNavigate();

    const [products, setProducts] = useState([]);
    const [cartItems, setCartItems] = useState({});
    const [wishlistItems, setWishlistItems] = useState({});
    const [isLoaded, setIsLoaded] = useState(false);
    const [serverError, setServerError] = useState(false);

    // ── USER STATE: read from localStorage on startup ──────────────
    const [user, setUser] = useState(() => {
        try {
            const stored = localStorage.getItem('neuroUser');
            return stored ? JSON.parse(stored) : null;
        } catch {
            return null;
        }
    });

    const logout = () => {
        localStorage.removeItem('neuroUser');
        setUser(null);
    };

    // ── Auth guard: redirects to /login (with return path) if not signed in ──
    const withAuth = (fn) => (...args) => {
        if (!user) {
            navigate('/login', { state: { from: window.location.pathname } });
            return;
        }
        return fn(...args);
    };
    // ───────────────────────────────────────────────────────────────

    // ── helper: fetch cart+wishlist for a given email and merge into state ──────
    const loadUserData = async (email, finalProducts) => {
        const headers = email ? { "User-Email": email } : {};
        const [cartRes, wishRes] = await Promise.all([
            fetch("http://localhost:5000/api/cart",     { headers }),
            fetch("http://localhost:5000/api/wishlist", { headers }),
        ]);
        const cartData     = await cartRes.json();
        const wishlistData = await wishRes.json();

        const newCart = {};
        const newWish = {};
        finalProducts.forEach(p => {
            newCart[p.id] = cartData[p.id]     || 0;
            newWish[p.id] = wishlistData[p.id] || 0;
        });
        setCartItems(newCart);
        setWishlistItems(newWish);
    };

    // 1. FETCH PRODUCTS on page load, then load cart/wishlist for current user
    useEffect(() => {
        const fetchDatabase = async () => {
            try {
                const productsResponse = await fetch("http://localhost:5000/api/products");
                if (!productsResponse.ok) throw new Error("Backend offline");
                const backendProducts = await productsResponse.json();

                const finalProducts = backendProducts.map(dbItem => {
                    const localItem = localImageMap.find(loc => loc.id === dbItem.id);
                    return { ...dbItem, image: localItem ? localItem.image : dbItem.image };
                });
                setProducts(finalProducts);

                // Read user directly from localStorage so this effect stays dep-free
                const storedUser = (() => {
                    try { return JSON.parse(localStorage.getItem('neuroUser')); } catch { return null; }
                })();
                await loadUserData(storedUser?.email || null, finalProducts);
                setIsLoaded(true);

            } catch (error) {
                console.error("CRITICAL ERROR: Backend (app.py) is offline! Site will not load data.");
                setServerError(true);
                setIsLoaded(true);
            }
        };

        fetchDatabase();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // 1b. Re-load cart/wishlist whenever the logged-in user changes
    useEffect(() => {
        if (isLoaded && !serverError && products.length > 0) {
            loadUserData(user?.email || null, products);
        }
    }, [user]); // eslint-disable-line react-hooks/exhaustive-deps

    // 2. SYNC CART TO BACKEND whenever it changes
    useEffect(() => {
        if (isLoaded && !serverError) {
            fetch("http://localhost:5000/api/cart", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...(user?.email ? { "User-Email": user.email } : {}),
                },
                body: JSON.stringify({ cart: cartItems })
            }).catch(err => console.error("Error syncing cart:", err));
        }
    }, [cartItems, isLoaded, serverError]); // eslint-disable-line react-hooks/exhaustive-deps

    // 3. SYNC WISHLIST TO BACKEND whenever it changes
    useEffect(() => {
        if (isLoaded && !serverError) {
            fetch("http://localhost:5000/api/wishlist", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...(user?.email ? { "User-Email": user.email } : {}),
                },
                body: JSON.stringify({ wishlist: wishlistItems })
            }).catch(err => console.error("Error syncing wishlist:", err));
        }
    }, [wishlistItems, isLoaded, serverError]); // eslint-disable-line react-hooks/exhaustive-deps

    // --- CALCULATIONS ---
    const getTotalCartAmount = () => {
        let totalAmount = 0;
        for (const item in cartItems) {
            if (cartItems[item] > 0) {
                let itemInfo = products.find((product) => product.id === Number(item));
                if (itemInfo) totalAmount += cartItems[item] * itemInfo.price;
            }
        }
        return totalAmount;
    };

    const getTotalCartItems = () => {
        let totalItems = 0;
        for (const item in cartItems) {
            totalItems += (cartItems[item] || 0);
        }
        return totalItems;
    };

    const addToCart = (itemId) => {
        setCartItems((prev) => ({ ...prev, [itemId]: (prev[itemId] || 0) + 1 }));
    };

    const removeFromCart = (itemId) => {
        setCartItems((prev) => ({ ...prev, [itemId]: Math.max((prev[itemId] || 0) - 1, 0) }));
    };

    const updateCartItemCount = (newAmount, itemId) => {
        setCartItems((prev) => ({ ...prev, [itemId]: newAmount }));
    };

    const clearCart = () => {
        const empty = {};
        products.forEach(p => { empty[p.id] = 0; });
        setCartItems(empty);
    };

    // --- WISHLIST LOGIC ---
    const addToWishlist = (itemId) => {
        setWishlistItems((prev) => ({ ...prev, [itemId]: 1 }));
    };

    const removeFromWishlist = (itemId) => {
        setWishlistItems((prev) => ({ ...prev, [itemId]: 0 }));
    };

    const toggleWishlist = (itemId) => {
        setWishlistItems((prev) => ({ ...prev, [itemId]: prev[itemId] > 0 ? 0 : 1 }));
    };

    const getTotalWishlistItems = () => {
        let total = 0;
        for (const item in wishlistItems) {
            if (wishlistItems[item] > 0) total += 1;
        }
        return total;
    };

    const contextValue = {
        cartItems,
        wishlistItems,
        // ── All mutation functions are auth-guarded ──
        addToCart:           withAuth(addToCart),
        removeFromCart:      withAuth(removeFromCart),
        updateCartItemCount: withAuth(updateCartItemCount),
        clearCart:           withAuth(clearCart),
        addToWishlist:           withAuth(addToWishlist),
        removeFromWishlist:      withAuth(removeFromWishlist),
        toggleWishlist:          withAuth(toggleWishlist),
        toggleWishlistUnguarded: toggleWishlist,
        // ────────────────────────────────────────────
        getTotalCartAmount,
        getTotalCartItems,
        getTotalWishlistItems,
        products,
        user,
        setUser,
        logout,
    };

    if (serverError) {
        return (
            <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontFamily: 'Inter', background: '#f8f9fb', color: '#1a1a1a' }}>
                <h2 style={{ fontSize: '2rem', margin: '0' }}>⚠️ Database Offline</h2>
            </div>
        );
    }

    if (!isLoaded) {
        return null;
    }

    return (
        <ShopContext.Provider value={contextValue}>
            {props.children}
        </ShopContext.Provider>
    );
};