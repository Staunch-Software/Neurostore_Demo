import React, { createContext, useState, useEffect } from "react";
// We import local products ONLY to match the local Webpack images to the database data!
import { products as localImageMap } from "../../assets/products";

export const ShopContext = createContext(null);

export const ShopContextProvider = (props) => {

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

    // ── helper: fetch cart+wishlist for a given email and merge into state ──────
    const loadUserData = async (email, finalProducts) => {

        const headers = email
            ? { "User-Email": email }
            : {};

        const [cartRes, wishRes] = await Promise.all([
            fetch("https://www.neurostore.in/api/cart", { headers }),
            fetch("https://www.neurostore.in/api/wishlist", { headers }),
        ]);

        const cartData = await cartRes.json();
        const wishlistData = await wishRes.json();

        const newCart = {};
        const newWish = {};

        finalProducts.forEach((p) => {
            newCart[p.id] = cartData[p.id] || 0;
            newWish[p.id] = wishlistData[p.id] || 0;
        });

        setCartItems(newCart);
        setWishlistItems(newWish);
    };

    // ── FETCH PRODUCTS + LOAD USER/GUEST DATA ─────────────────────
    useEffect(() => {

        const fetchDatabase = async () => {

            try {

                const productsResponse = await fetch(
                    "https://www.neurostore.in/api/products"
                );

                if (!productsResponse.ok) {
                    throw new Error("Backend offline");
                }

                const backendProducts = await productsResponse.json();

                const finalProducts = backendProducts.map((dbItem) => {

                    const localItem = localImageMap.find(
                        (loc) => loc.id === dbItem.id
                    );

                    return {
                        ...dbItem,
                        image: localItem
                            ? localItem.image
                            : dbItem.image
                    };
                });

                setProducts(finalProducts);

                // ── CHECK LOGGED-IN USER ──
                let storedUser = null;

                try {
                    storedUser = JSON.parse(
                        localStorage.getItem("neuroUser")
                    );
                } catch {
                    storedUser = null;
                }

                // ── LOGGED-IN USER DATA ──
                if (storedUser?.email) {

                    await loadUserData(
                        storedUser.email,
                        finalProducts
                    );

                } else {

                    // ── GUEST CART/WISHLIST ──
                    let guestCart = {};
                    let guestWishlist = {};

                    try {
                        guestCart = JSON.parse(
                            localStorage.getItem("guestCart")
                        ) || {};
                    } catch {
                        guestCart = {};
                    }

                    try {
                        guestWishlist = JSON.parse(
                            localStorage.getItem("guestWishlist")
                        ) || {};
                    } catch {
                        guestWishlist = {};
                    }

                    const formattedCart = {};
                    const formattedWishlist = {};

                    finalProducts.forEach((p) => {

                        formattedCart[p.id] =
                            guestCart[p.id] || 0;

                        formattedWishlist[p.id] =
                            guestWishlist[p.id] || 0;
                    });

                    setCartItems(formattedCart);
                    setWishlistItems(formattedWishlist);
                }

                setIsLoaded(true);

            } catch (error) {

                console.error(
                    "CRITICAL ERROR: Backend (app.py) is offline!"
                );

                setServerError(true);
                setIsLoaded(true);
            }
        };

        fetchDatabase();

    }, []);

    // ── RELOAD WHEN USER CHANGES ──────────────────────────────────
    useEffect(() => {

        if (
            isLoaded &&
            !serverError &&
            products.length > 0
        ) {

            // ── LOGGED-IN USER ──
            if (user?.email) {

                loadUserData(user.email, products);

            } else {

                // ── GUEST USER ──
                let guestCart = {};
                let guestWishlist = {};

                try {
                    guestCart = JSON.parse(
                        localStorage.getItem("guestCart")
                    ) || {};
                } catch {
                    guestCart = {};
                }

                try {
                    guestWishlist = JSON.parse(
                        localStorage.getItem("guestWishlist")
                    ) || {};
                } catch {
                    guestWishlist = {};
                }

                // ✅ FIXED SECTION
                const formattedCart = {};
                const formattedWishlist = {};

                products.forEach((p) => {

                    formattedCart[p.id] =
                        guestCart[p.id] || 0;

                    formattedWishlist[p.id] =
                        guestWishlist[p.id] || 0;
                });

                setCartItems(formattedCart);
                setWishlistItems(formattedWishlist);
            }
        }

    }, [user, isLoaded, serverError, products]);

    // ── SAVE GUEST CART ───────────────────────────────────────────
    useEffect(() => {

        if (!user) {

            localStorage.setItem(
                "guestCart",
                JSON.stringify(cartItems)
            );
        }

    }, [cartItems, user]);

    // ── SAVE GUEST WISHLIST ───────────────────────────────────────
    useEffect(() => {

        if (!user) {

            localStorage.setItem(
                "guestWishlist",
                JSON.stringify(wishlistItems)
            );
        }

    }, [wishlistItems, user]);

    // ── SYNC CART TO BACKEND (ONLY LOGGED-IN USERS) ──────────────
    useEffect(() => {

        if (
            isLoaded &&
            !serverError &&
            user
        ) {

            fetch("https://www.neurostore.in/api/cart", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    ...(user?.email
                        ? { "User-Email": user.email }
                        : {}),
                },

                body: JSON.stringify({
                    cart: cartItems
                })

            }).catch((err) =>
                console.error("Error syncing cart:", err)
            );
        }

    }, [cartItems, isLoaded, serverError, user]);

    // ── SYNC WISHLIST TO BACKEND (ONLY LOGGED-IN USERS) ──────────
    useEffect(() => {

        if (
            isLoaded &&
            !serverError &&
            user
        ) {

            fetch("https://www.neurostore.in/api/wishlist", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    ...(user?.email
                        ? { "User-Email": user.email }
                        : {}),
                },

                body: JSON.stringify({
                    wishlist: wishlistItems
                })

            }).catch((err) =>
                console.error("Error syncing wishlist:", err)
            );
        }

    }, [wishlistItems, isLoaded, serverError, user]);

    // ── TOTAL CART AMOUNT ─────────────────────────────────────────
    const getTotalCartAmount = () => {

        let totalAmount = 0;

        for (const item in cartItems) {

            if (cartItems[item] > 0) {

                let itemInfo = products.find(
                    (product) =>
                        product.id === Number(item)
                );

                if (itemInfo) {

                    totalAmount +=
                        cartItems[item] * itemInfo.price;
                }
            }
        }

        return totalAmount;
    };

    // ── TOTAL CART ITEMS ──────────────────────────────────────────
    const getTotalCartItems = () => {

        let totalItems = 0;

        for (const item in cartItems) {

            totalItems += (cartItems[item] || 0);
        }

        return totalItems;
    };

    // ── CART FUNCTIONS ────────────────────────────────────────────
    const addToCart = (itemId) => {

        setCartItems((prev) => ({
            ...prev,
            [itemId]: (prev[itemId] || 0) + 1
        }));
    };

    const removeFromCart = (itemId) => {

        setCartItems((prev) => ({
            ...prev,
            [itemId]: Math.max(
                (prev[itemId] || 0) - 1,
                0
            )
        }));
    };

    const updateCartItemCount = (
        newAmount,
        itemId
    ) => {

        setCartItems((prev) => ({
            ...prev,
            [itemId]: newAmount
        }));
    };

    const clearCart = () => {

        const empty = {};

        products.forEach((p) => {
            empty[p.id] = 0;
        });

        setCartItems(empty);
    };

    // ── WISHLIST FUNCTIONS ────────────────────────────────────────
    const addToWishlist = (itemId) => {

        setWishlistItems((prev) => ({
            ...prev,
            [itemId]: 1
        }));
    };

    const removeFromWishlist = (itemId) => {

        setWishlistItems((prev) => ({
            ...prev,
            [itemId]: 0
        }));
    };

    const toggleWishlist = (itemId) => {

        setWishlistItems((prev) => ({
            ...prev,
            [itemId]:
                prev[itemId] > 0 ? 0 : 1
        }));
    };

    const getTotalWishlistItems = () => {

        let total = 0;

        for (const item in wishlistItems) {

            if (wishlistItems[item] > 0) {
                total += 1;
            }
        }

        return total;
    };

    // ── CONTEXT VALUE ─────────────────────────────────────────────
    const contextValue = {

        cartItems,
        wishlistItems,

        // CART
        addToCart,
        removeFromCart,
        updateCartItemCount,
        clearCart,

        // WISHLIST
        addToWishlist,
        removeFromWishlist,
        toggleWishlist,
        toggleWishlistUnguarded: toggleWishlist,

        // TOTALS
        getTotalCartAmount,
        getTotalCartItems,
        getTotalWishlistItems,

        // PRODUCTS
        products,

        // USER
        user,
        setUser,
        logout,
    };

    // ── SERVER ERROR SCREEN ───────────────────────────────────────
    if (serverError) {

        return (
            <div
                style={{
                    height: "100vh",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    fontFamily: "Inter",
                    background: "#f8f9fb",
                    color: "#1a1a1a"
                }}
            >
                <h2
                    style={{
                        fontSize: "2rem",
                        margin: "0"
                    }}
                >
                    ⚠️ Database Offline
                </h2>
            </div>
        );
    }

    // ── LOADING ───────────────────────────────────────────────────
    if (!isLoaded) {
        return null;
    }

    // ── PROVIDER ──────────────────────────────────────────────────
    return (
        <ShopContext.Provider value={contextValue}>
            {props.children}
        </ShopContext.Provider>
    );
};