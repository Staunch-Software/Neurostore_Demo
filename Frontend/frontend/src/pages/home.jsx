import React, { useContext, useEffect, useState } from 'react';
import SEO from '../components/SEO';
import { Link } from 'react-router-dom';
import { ArrowRight, BadgeCheck, Headphones, Search, ShieldCheck, Truck } from 'lucide-react';
import '../pages/home.css';
import BookService from '../components/bookservice';
import { ShopContext } from '../components/context/ShopContext';
import heroBanner from '../assets/hero-banner-1.jpg';

const backendUrl = import.meta.env.VITE_API_URL || "";

const generateSlug = (text) => text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');

const enquiryMessages = [
    "Can't find the product you're looking for?",
    'Need help choosing the right technology?',
    'Looking for a product that is not listed?',
    'Need a custom quote for your business?',
    'Unsure which license fits your team?',
];

const Home = () => {
    const { products } = useContext(ShopContext);
    const [bookingOpen, setBookingOpen] = useState(false);
    const [selectedService, setSelectedService] = useState('');

    const [thankYouOpen, setThankYouOpen] = useState(false);

    const featuredProducts = products
        .filter((product) => product.price && product.image)
        .slice(0, 8);

    const shopCategories = [
        { label: 'Microsoft Software', detail: 'Licenses, servers & productivity', to: '/products?brand=Microsoft', mark: 'MS' },
        { label: 'Cyber Protection', detail: 'Backup, security & recovery', to: '/products?brand=Acronis', mark: 'AC' },
        { label: 'AI Workstations', detail: 'Purpose-built systems for AI', to: '/products?brand=AI%20PC', mark: 'AI' },
        { label: 'All Products', detail: 'Browse the complete catalog', to: '/products', mark: 'ALL' },
    ];

    const services = [
        { title: 'Acronis Cybersecurity', icon: (<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>), color: 'gradient-primary-secondary' },
        { title: 'VAPT Services', icon: (<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.35-4.35"></path></svg>), color: 'gradient-secondary-accent' },
        { title: 'Endpoint Security', icon: (<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>), color: 'gradient-accent-primary' },
        { title: 'Threat Hunting', icon: (<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m8 2 1.88 1.88"></path><path d="M14.12 3.88 16 2"></path><path d="M9 7.13v-1a3.003 3.003 0 1 1 6 0v1"></path><path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6"></path><path d="M12 20v-9"></path><path d="M6.53 9C4.6 8.8 3 7.1 3 5"></path><path d="M6 13H2"></path><path d="M3 21c0-2.1 1.7-3.9 3.8-4"></path><path d="M20.97 5c0 2.1-1.6 3.8-3.5 4"></path><path d="M22 13h-4"></path><path d="M17.2 17c2.1.1 3.8 1.9 3.8 4"></path></svg>), color: 'gradient-primary-accent' },
        { title: 'SOC as a Service', icon: (<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>), color: 'gradient-secondary-primary' },
        { title: 'Compliance & Audit', icon: (<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>), color: 'gradient-accent-secondary' }
    ];

    const handleBookNow = (serviceName) => {
        setSelectedService(serviceName);
        setBookingOpen(true);
    };

    useEffect(() => {
        const observerOptions = { threshold: 0.1, rootMargin: '-100px' };
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-view');
                }
            });
        }, observerOptions);

        document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));

        return () => {
            observer.disconnect();
        };
    }, []);

    // ===== SEND INQUIRY TO UNIFIED PYTHON BACKEND =====
    const handleFormSubmit = async (e) => {
        e.preventDefault();

        const inquiryData = {
            name: e.target.name.value,
            email: e.target.email.value,
            phone: e.target.phone.value,
            product: e.target.product.value,
            message: e.target.message.value
        };

        try {
            // Python Backend handles this natively now
            const response = await fetch(`${backendUrl || 'https://neurostore.in'}/api/inquiry`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(inquiryData)
            });

            if (response.ok) {
                setThankYouOpen(true);
                e.target.reset();
            } else {
                alert("Sorry, there was an issue sending your inquiry to the server.");
            }
        } catch (error) {
            console.error("Backend Server Error:", error);
            alert("Could not connect to the backend server. Please ensure app.py is running!");
        }
    };

    return (
        <>
            <SEO
                title="Buy AI Cameras, GPU Servers & AI Hardware in India | Neurostore"
                description="Neurostore is India's trusted AI hardware store. Buy AI cameras, GPU workstations, NVIDIA graphics cards, Raspberry Pi, developer kits and cybersecurity solutions. Fast delivery across India."
                keywords="buy AI camera India, AI hardware store India, GPU server price India, NVIDIA RTX 5090 buy India, Raspberry Pi 5 buy India, AI workstation India, neurostore"
                ogImage="https://neurostore.in/og-image.webp"
                ogType="website"
            />
            <main className="storefront-home">
                <section className="storefront-hero" style={{ backgroundImage: `url(${heroBanner})` }}>
                    <div className="storefront-hero-shade" />
                    <div className="container storefront-hero-content">
                        <p className="storefront-kicker">India&apos;s AI technology marketplace</p>
                        <h1>NeuroStore</h1>
                        <p className="storefront-hero-copy">
                            Enterprise software, AI workstations, cybersecurity and infrastructure products,
                            sourced for teams that need technology to work from day one.
                        </p>
                        <div className="storefront-hero-actions">
                            <Link to="/products" className="storefront-primary-btn">
                                Shop all products <ArrowRight size={18} />
                            </Link>
                            <Link to="/contact" className="storefront-secondary-btn">Talk to a specialist</Link>
                        </div>
                        <Link to="/products" className="storefront-search-prompt" aria-label="Search the NeuroStore catalog">
                            <Search size={20} />
                            <span>What technology are you looking for?</span>
                            <strong>Search catalog</strong>
                        </Link>
                    </div>
                </section>

                <div className="enquiry-ticker-wrapper" aria-label="Product enquiry contact">
                    <div className="enquiry-ticker-track">
                        {[...enquiryMessages, ...enquiryMessages].map((message, index) => (
                            <span key={index} className="enquiry-ticker-item">
                                {message}&nbsp;
                                <strong>Enquire now:</strong>&nbsp;
                                <a href="tel:+919384813815" className="ticker-phone">+91 93848 13815</a>
                                <span className="ticker-sep">✦</span>
                            </span>
                        ))}
                    </div>
                </div>

                <section className="storefront-benefits" aria-label="Shopping benefits">
                    <div className="container storefront-benefits-grid">
                        <div><BadgeCheck size={22} /><span><strong>Genuine products</strong>Authorized commercial licensing</span></div>
                        <div><ShieldCheck size={22} /><span><strong>Secure checkout</strong>Protected ordering and payment</span></div>
                        <div><Truck size={22} /><span><strong>India-wide delivery</strong>Digital and physical fulfillment</span></div>
                        <div><Headphones size={22} /><span><strong>Expert assistance</strong>Pre-sales and deployment support</span></div>
                    </div>
                </section>

                <section className="storefront-categories">
                    <div className="container">
                        <div className="storefront-section-heading animate-on-scroll">
                            <div>
                                <span>Shop by department</span>
                                <h2>Find the right technology faster</h2>
                            </div>
                            <Link to="/products">View all departments <ArrowRight size={17} /></Link>
                        </div>
                        <div className="storefront-category-grid">
                            {shopCategories.map((category) => (
                                <Link to={category.to} className="storefront-category-item animate-on-scroll" key={category.label}>
                                    <span className="storefront-category-mark">{category.mark}</span>
                                    <span><strong>{category.label}</strong><small>{category.detail}</small></span>
                                    <ArrowRight size={18} />
                                </Link>
                            ))}
                        </div>
                    </div>
                </section>

                <section className="storefront-products">
                    <div className="container">
                        <div className="storefront-section-heading animate-on-scroll">
                            <div>
                                <span>Featured products</span>
                                <h2>Popular for business</h2>
                            </div>
                            <Link to="/products">Shop the full catalog <ArrowRight size={17} /></Link>
                        </div>
                        <div className="storefront-product-grid">
                            {featuredProducts.map((product) => (
                                <Link
                                    to={`/products/${generateSlug(product.name)}`}
                                    className="storefront-product-card animate-on-scroll"
                                    key={product.id}
                                >
                                    <div className="storefront-product-image">
                                        <img src={product.image} alt={product.name} loading="lazy" />
                                        {product.badge && <span>{product.badge}</span>}
                                    </div>
                                    <div className="storefront-product-info">
                                        <small>{product.brand || product.category}</small>
                                        <h3>{product.name}</h3>
                                        <p>{product.shortDescription || product.category}</p>
                                        <div className="storefront-product-buy-row">
                                            <strong>₹{Number(product.price).toLocaleString('en-IN')}</strong>
                                            <span>View product <ArrowRight size={15} /></span>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </div>
                </section>
            </main>


            {/* CATEGORIES SECTION - Commented out & Hidden
            <section className="categories-section">
                <div className="container categories-container">
                    <div className="categories-header animate-on-scroll">
                        <span className="categories-badge">Browse Categories</span>
                        <h2 className="categories-title">Shop by <span className="text-gradient">Category</span></h2>
                        <p className="categories-description">Explore our wide range of AI-powered products across every category.</p>
                    </div>
                    <div className="categories-grid">
                        <a href="/products/ai-vision-security" className="category-card animate-on-scroll"><img src={aiCameras} alt="AI Cameras" className="category-image" /><div className="category-overlay" /><div className="category-content"><h3 className="category-name">AI Cameras</h3></div></a>
                        <a href="/products/ai-networking-storage" className="category-card animate-on-scroll"><img src={aiServers} alt="AI Servers" className="category-image" /><div className="category-overlay" /><div className="category-content"><h3 className="category-name">AI Storage</h3></div></a>
                        <a href="/products/ai-workstations-and-servers" className="category-card animate-on-scroll"><img src={aiWorkstation} alt="Workstations" className="category-image" /><div className="category-overlay" /><div className="category-content"><h3 className="category-name">AI Workstations & Servers</h3></div></a>
                        <a href="/products/ai-dev-boards" className="category-card animate-on-scroll"><img src={developerKit} alt="Developer Kits" className="category-image" /><div className="category-overlay" /><div className="category-content"><h3 className="category-name">AI Developer Kits</h3></div></a>
                        <a href="/products/ai-vision-security" className="category-card animate-on-scroll"><img src={robotics} alt="Robotics" className="category-image" /><div className="category-overlay" /><div className="category-content"><h3 className="category-name">AI Vision Modules</h3></div></a>
                        <a href="/products/ai-software" className="category-card animate-on-scroll"><img src={software} alt="Software" className="category-image" /><div className="category-overlay" /><div className="category-content"><h3 className="category-name">AI Software</h3></div></a>
                        <a href="/products/ai-graphics-cards" className="category-card animate-on-scroll"><img src={components} alt="Components" className="category-image" /><div className="category-overlay" /><div className="category-content"><h3 className="category-name">AI Graphics Card</h3></div></a>
                        <a href="/products/ai-accessories" className="category-card animate-on-scroll"><img src={quantum} alt="Quantum Computing" className="category-image" /><div className="category-overlay" /><div className="category-content"><h3 className="category-name">AI Accessories</h3></div></a>
                    </div>
                </div>
            </section>
            */}

            {/* CYBERSECURITY SERVICES SECTION */}
            <section id="services" className="services-section">
                <div className="container">
                    <div className="section-header animate-on-scroll">
                        <span className="section-badge">Our Services</span>
                        <h2>NeuroStore <span className="text-gradient">Services</span></h2>
                        <p className="services-description">Safeguard your digital assets with our comprehensive cybersecurity solutions – from Acronis protection to advanced penetration testing.</p>
                    </div>

                    <div className="services-grid">
                        {/* Service Card 1 - Acronis Cybersecurity */}
                        <div className="service-card animate-on-scroll" data-color="primary-secondary">
                            <div className="service-gradient-bar gradient-primary-secondary" />
                            <div className="service-glow-effect" />
                            <div className="service-content">
                                <div className="service-header-row">
                                    <div className="service-icon-box gradient-primary-secondary">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                                        </svg>
                                    </div>
                                    <div>
                                        <h3 className="service-title">Acronis Cybersecurity</h3>
                                        <p className="service-tagline">Complete Cyber Protection</p>
                                    </div>
                                </div>
                                <p className="service-description">
                                    Enterprise-grade backup, disaster recovery, and anti-malware powered by Acronis. Protect your data, applications, and systems from every threat.
                                </p>
                                <button className="service-btn" onClick={() => handleBookNow('Acronis Cybersecurity')}>
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                        <line x1="16" y1="2" x2="16" y2="6"></line>
                                        <line x1="8" y1="2" x2="8" y2="6"></line>
                                        <line x1="3" y1="10" x2="21" y2="10"></line>
                                    </svg>
                                    Book Now
                                </button>
                            </div>
                        </div>

                        {/* Service Card 2 - VAPT Services */}
                        <div className="service-card animate-on-scroll" data-color="secondary-accent">
                            <div className="service-gradient-bar gradient-secondary-accent" />
                            <div className="service-glow-effect" />
                            <div className="service-content">
                                <div className="service-header-row">
                                    <div className="service-icon-box gradient-secondary-accent">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <circle cx="11" cy="11" r="8"></circle>
                                            <path d="m21 21-4.35-4.35"></path>
                                        </svg>
                                    </div>
                                    <div>
                                        <h3 className="service-title">VAPT Services</h3>
                                        <p className="service-tagline">Vulnerability Assessment & Penetration Testing</p>
                                    </div>
                                </div>
                                <p className="service-description">
                                    Comprehensive security auditing to identify and exploit vulnerabilities before attackers do. We simulate real-world attacks to fortify your defenses.
                                </p>
                                <button className="service-btn" onClick={() => handleBookNow('VAPT Services')}>
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                        <line x1="16" y1="2" x2="16" y2="6"></line>
                                        <line x1="8" y1="2" x2="8" y2="6"></line>
                                        <line x1="3" y1="10" x2="21" y2="10"></line>
                                    </svg>
                                    Book Now
                                </button>
                            </div>
                        </div>

                        {/* Service Card 3 - Endpoint Security */}
                        <div className="service-card animate-on-scroll" data-color="accent-primary">
                            <div className="service-gradient-bar gradient-accent-primary" />
                            <div className="service-glow-effect" />
                            <div className="service-content">
                                <div className="service-header-row">
                                    <div className="service-icon-box gradient-accent-primary">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                                        </svg>
                                    </div>
                                    <div>
                                        <h3 className="service-title">Endpoint Security</h3>
                                        <p className="service-tagline">Zero-Trust Architecture</p>
                                    </div>
                                </div>
                                <p className="service-description">
                                    Advanced endpoint detection and response (EDR) solutions that monitor, detect, and neutralize threats across all your devices in real time.
                                </p>
                                <button className="service-btn" onClick={() => handleBookNow('Endpoint Security')}>
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                        <line x1="16" y1="2" x2="16" y2="6"></line>
                                        <line x1="8" y1="2" x2="8" y2="6"></line>
                                        <line x1="3" y1="10" x2="21" y2="10"></line>
                                    </svg>
                                    Book Now
                                </button>
                            </div>
                        </div>

                        {/* Service Card 4 - Threat Hunting */}
                        <div className="service-card animate-on-scroll" data-color="primary-accent">
                            <div className="service-gradient-bar gradient-primary-accent" />
                            <div className="service-glow-effect" />
                            <div className="service-content">
                                <div className="service-header-row">
                                    <div className="service-icon-box gradient-primary-accent">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="m8 2 1.88 1.88"></path>
                                            <path d="M14.12 3.88 16 2"></path>
                                            <path d="M9 7.13v-1a3.003 3.003 0 1 1 6 0v1"></path>
                                            <path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6"></path>
                                            <path d="M12 20v-9"></path>
                                            <path d="M6.53 9C4.6 8.8 3 7.1 3 5"></path>
                                            <path d="M6 13H2"></path>
                                            <path d="M3 21c0-2.1 1.7-3.9 3.8-4"></path>
                                            <path d="M20.97 5c0 2.1-1.6 3.8-3.5 4"></path>
                                            <path d="M22 13h-4"></path>
                                            <path d="M17.2 17c2.1.1 3.8 1.9 3.8 4"></path>
                                        </svg>
                                    </div>
                                    <div>
                                        <h3 className="service-title">Threat Hunting</h3>
                                        <p className="service-tagline">Proactive Defense</p>
                                    </div>
                                </div>
                                <p className="service-description">
                                    Our expert analysts proactively search for hidden threats in your network using advanced AI-driven tools and behavioral analytics.
                                </p>
                                <button className="service-btn" onClick={() => handleBookNow('Threat Hunting')}>
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                        <line x1="16" y1="2" x2="16" y2="6"></line>
                                        <line x1="8" y1="2" x2="8" y2="6"></line>
                                        <line x1="3" y1="10" x2="21" y2="10"></line>
                                    </svg>
                                    Book Now
                                </button>
                            </div>
                        </div>

                        {/* Service Card 5 - SOC as a Service */}
                        <div className="service-card animate-on-scroll" data-color="secondary-primary">
                            <div className="service-gradient-bar gradient-secondary-primary" />
                            <div className="service-glow-effect" />
                            <div className="service-content">
                                <div className="service-header-row">
                                    <div className="service-icon-box gradient-secondary-primary">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
                                            <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
                                            <line x1="6" y1="6" x2="6.01" y2="6"></line>
                                            <line x1="6" y1="18" x2="6.01" y2="18"></line>
                                        </svg>
                                    </div>
                                    <div>
                                        <h3 className="service-title">SOC as a Service</h3>
                                        <p className="service-tagline">Security Operations Center</p>
                                    </div>
                                </div>
                                <p className="service-description">
                                    Fully managed Security Operations Center providing round-the-clock monitoring, alerting, and incident management for your infrastructure.
                                </p>
                                <button className="service-btn" onClick={() => handleBookNow('SOC as a Service')}>
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                        <line x1="16" y1="2" x2="16" y2="6"></line>
                                        <line x1="8" y1="2" x2="8" y2="6"></line>
                                        <line x1="3" y1="10" x2="21" y2="10"></line>
                                    </svg>
                                    Book Now
                                </button>
                            </div>
                        </div>

                        {/* Service Card 6 - Compliance & Audit */}
                        <div className="service-card animate-on-scroll" data-color="accent-secondary">
                            <div className="service-gradient-bar gradient-accent-secondary" />
                            <div className="service-glow-effect" />
                            <div className="service-content">
                                <div className="service-header-row">
                                    <div className="service-icon-box gradient-accent-secondary">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                            <polyline points="14 2 14 8 20 8"></polyline>
                                            <line x1="16" y1="13" x2="8" y2="13"></line>
                                            <line x1="16" y1="17" x2="8" y2="17"></line>
                                            <polyline points="10 9 9 9 8 9"></polyline>
                                        </svg>
                                    </div>
                                    <div>
                                        <h3 className="service-title">Compliance & Audit</h3>
                                        <p className="service-tagline">Regulatory Readiness</p>
                                    </div>
                                </div>
                                <p className="service-description">
                                    Navigate complex compliance landscapes with our audit services covering ISO 27001, GDPR, HIPAA, PCI-DSS, and industry-specific regulations.
                                </p>
                                <button className="service-btn" onClick={() => handleBookNow('Compliance & Audit')}>
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                        <line x1="16" y1="2" x2="16" y2="6"></line>
                                        <line x1="8" y1="2" x2="8" y2="6"></line>
                                        <line x1="3" y1="10" x2="21" y2="10"></line>
                                    </svg>
                                    Book Now
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* INQUIRY FORM SECTION */}
            <section className="inquiry-section">
                <div className="container inquiry-container">
                    <div className="section-header">
                        <h2>Get in Touch</h2>
                        <p>Have questions about our AI products? Fill out the form below and our team will get back to you shortly.</p>
                    </div>
                    <form className="inquiry-form" onSubmit={handleFormSubmit}>
                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="name">Full Name *</label>
                                <input type="text" id="name" name="name" required />
                            </div>
                            <div className="form-group">
                                <label htmlFor="email">Email Address *</label>
                                <input type="email" id="email" name="email" required />
                            </div>
                        </div>
                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="phone">Phone Number *</label>
                                <input type="tel" id="phone" name="phone" required />
                            </div>
                            <div className="form-group">
                                <label htmlFor="product">Product Interest</label>
                                <select id="product" name="product">
                                    <option value="">Select a product</option>
                                    <option value="ai-camera">AI Cameras</option>
                                    <option value="ai-server">AI Servers</option>
                                    <option value="ai-workstation">AI Workstations</option>
                                    <option value="ai-books">AI Learning Resources</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>
                        </div>
                        <div className="form-group">
                            <label htmlFor="message">Your Message *</label>
                            <textarea id="message" name="message" required></textarea>
                        </div>
                        <button type="submit" className="submit-btn">Send Inquiry</button>
                    </form>
                </div>
            </section>

            {/* THANK YOU MODAL */}
            {thankYouOpen && (
                <div className="thankyou-overlay">
                    <div className="thankyou-modal">
                        <button className="thankyou-close-x" onClick={() => setThankYouOpen(false)}>✕</button>
                        <h2 className="thankyou-title">Thank You!</h2>
                        <p className="thankyou-message">
                            We have received your message. Our team will reach out to you soon!
                        </p>
                        <button className="thankyou-btn" onClick={() => setThankYouOpen(false)}>
                            Close
                        </button>
                    </div>
                </div>
            )}

            {/* Booking Dialog Component */}
            <BookService
                open={bookingOpen}
                onClose={() => setBookingOpen(false)}
                serviceName={selectedService}
                services={services}
            />
        </>
    );
};

export default Home;