import React, { useContext } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ShopContextProvider, ShopContext } from './components/context/ShopContext';

import Navbar from './components/nav';
import Footer from './components/footer';
import ScrollToTop from './components/scrolltotop';
import Home from './pages/home';
import Products from './pages/products';
import ProductDetails from './pages/ProductDetails';
import About from './pages/about';
import Brands from './components/Brandcomponents';
import Wishlist from './components/wishlist';
import Cart from './components/cart';
import Contact from './components/contact';
import TermsAndConditions from './pages/TermsAndConditions';
import PrivacyPolicy from './pages/PrivacyPolicy';
import Disclaimer from './pages/Disclaimer';
import ShippingPolicy from './pages/ShippingPolicy';
import CustomerAuth from './pages/CustomerAuth';
import Profile from './pages/Profile';
import Checkout from './pages/Checkout';
import Payment from './pages/Payment';
import OrderSuccess from './pages/Ordersuccess';
import FloatingReachUs from './components/floatingreachus';
import AdminLogin from './pages/AdminLogin';
import AdminDashboard from './pages/AdminDashboard';

// ── Protected Route — only for pages that truly require login (e.g. Profile) ──
const ProtectedRoute = ({ children }) => {
  const { user } = useContext(ShopContext);
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  return children;
};

// Admin routes render without Navbar/Footer
const AdminRoute = ({ children }) => (
  <div className="App">{children}</div>
);

function App() {
  return (
    <div className="App">
      <Routes>
        {/* Admin — standalone layout, no Navbar/Footer */}
        <Route path="/admin" element={<AdminRoute><AdminLogin /></AdminRoute>} />
        <Route path="/admin/dashboard" element={<AdminRoute><AdminDashboard /></AdminRoute>} />

        {/* All customer routes wrapped in ShopContextProvider */}
        <Route path="/*" element={
          <ShopContextProvider>
            <ScrollToTop />
            <Navbar />
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/products" element={<Products />} />
              <Route path="/products/:category" element={<Products />} />
              <Route path="/products/:category/:productName" element={<ProductDetails />} />
              <Route path="/about" element={<About />} />
              <Route path="/brands" element={<Brands />} />

              <Route path="/wishlist" element={<Wishlist />} />
              <Route path="/cart" element={<Cart />} />

              <Route path="/contact" element={<Contact />} />
              <Route path="/terms-and-conditions" element={<TermsAndConditions />} />
              <Route path="/privacy-policy" element={<PrivacyPolicy />} />
              <Route path="/disclaimer" element={<Disclaimer />} />
              <Route path="/shipping-policy" element={<ShippingPolicy />} />
              <Route path="/login" element={<CustomerAuth />} />

              {/* Profile - open access */}
              <Route path="/profile" element={<Profile />} />

              {/* Checkout & Payment — open to guests, no login required */}
              <Route path="/checkout" element={<Checkout />} />
              <Route path="/payment" element={<Payment />} />

              <Route path="/order-success" element={<OrderSuccess />} />
            </Routes>
            <Footer />
            <FloatingReachUs />
          </ShopContextProvider>
        } />
      </Routes>
    </div>



  );
}

export default App;