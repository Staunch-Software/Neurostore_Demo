import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../pages/home.css';
import BookService from '../components/bookservice';

import aiCameras from '../assets/AI Cameras.jpg.jpeg';
import aiServers from '../assets/AI Server.webp';
import aiWorkstation from '../assets/AI Workstation.webp';
import developerKit from '../assets/AI Developer kit.jpg.jpeg';
import robotics from '../assets/AI Vision module.jpg.jpeg';
import software from '../assets/AI Software.webp';
import components from '../assets/AI Chips.jpg.jpeg';
import quantum from '../assets/AI Books.jpeg';
import bannerAllProducts from '../assets/hero-banner-1.jpg';
import bannerOffers from '../assets/banner-offers.jpg';
import bannerAiTech from '../assets/banner-ai-tech.jpg';
import bannerWorkspace from '../assets/banner-workspace.jpg';

import msiRTX5090 from "../assets/MSI GeForce RTX™ 5090 Lightning Z 32GB GDDR7.webp";
import nvidiaRTXPro6000MaxQ from "../assets/NVIDIA RTX Pro 6000 Blackwell Max-Q.webp";
import raspberryPi5 from "../assets/Raspberry Pi 5 Development Board.webp";
import ubiquitiG4Bullet from "../assets/Ubiquiti UniFi Protect G4 Bullet.webp";
import embeddedAIBundle from "../assets/Embedded & AI Dev Boards Bundle.webp";
import msiRTX4070Ti from "../assets/MSI RTX 4070 Ti Gaming X Trio 12GB.webp";

const backendUrl = import.meta.env.VITE_API_URL || "";

const bannerImages = [
    { src: bannerAllProducts, alt: "NeuroStore AI Products Collection", title: "Explore All Products", subtitle: "Discover our complete AI-powered collection", link: "/products", buttonText: "Shop Now" },
    { src: bannerOffers, alt: "Special Offers and Deals", title: "Exclusive Offers", subtitle: "Up to 40% off on selected neural devices", link: "/products", buttonText: "View Deals" },
    { src: bannerAiTech, alt: "AI Neural Technology", title: "Next-Gen AI Tech", subtitle: "Experience the future of neural computing", link: "/products", buttonText: "Learn More" },
    { src: bannerWorkspace, alt: "AI Developer Workspace", title: "Developer Workspace", subtitle: "Tools built for the AI-first creator", link: "/products", buttonText: "Get Started" },
];

const Home = () => {
    const navigate = useNavigate();
    const [currentSlide, setCurrentSlide] = useState(0);
    const [isTransitioning, setIsTransitioning] = useState(false);

    const [bookingOpen, setBookingOpen] = useState(false);
    const [selectedService, setSelectedService] = useState('');

    const [thankYouOpen, setThankYouOpen] = useState(false);

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
        const autoplayInterval = setInterval(() => {
            setIsTransitioning(true);
            setCurrentSlide((prev) => (prev + 1) % bannerImages.length);
            setTimeout(() => setIsTransitioning(false), 100);
        }, 4000);

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
            clearInterval(autoplayInterval);
            observer.disconnect();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
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
            const response = await fetch(`${backendUrl || 'http://localhost:8000'}/api/inquiry`, {
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
            {/* HERO BANNER SECTION */}
            <section className="hero-banner-wrapper">
                <div className="hero-carousel">
                    {bannerImages.map((image, index) => (
                        <Link
                            key={index}
                            to={image.link}
                            className={`hero-slide ${currentSlide === index ? 'active' : ''}`}
                            style={{ display: currentSlide === index ? 'block' : 'none' }}
                        >
                            <img src={image.src} alt={image.alt} className={`hero-image ${currentSlide === index ? 'zooming' : ''}`} loading={index === 0 ? "eager" : "lazy"} />
                            <div className="hero-gradient-overlay" />
                            <div className="hero-gradient-side" />
                            <div className="hero-content">
                                <div className={`hero-accent-line ${currentSlide === index && !isTransitioning ? 'visible' : ''}`} />
                                <h2 className={`hero-title ${currentSlide === index && !isTransitioning ? 'visible' : ''}`}>{image.title}</h2>
                                <p className={`hero-subtitle ${currentSlide === index && !isTransitioning ? 'visible' : ''}`}>{image.subtitle}</p>
                                <div className={`hero-cta ${currentSlide === index && !isTransitioning ? 'visible' : ''}`}>
                                    <button className="hero-button">
                                        {image.buttonText}
                                        <svg className="hero-arrow" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <line x1="5" y1="12" x2="19" y2="12"></line>
                                            <polyline points="12 5 19 12 12 19"></polyline>
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
                <div className="hero-indicators">
                    {bannerImages.map((_, index) => (
                        <button key={index} onClick={() => { setIsTransitioning(true); setCurrentSlide(index); setTimeout(() => setIsTransitioning(false), 100); }} className={`hero-indicator ${currentSlide === index ? 'active' : ''}`} aria-label={`Go to slide ${index + 1}`}>
                            <div className="indicator-bg" />
                            {currentSlide === index && <div className="indicator-progress" />}
                        </button>
                    ))}
                </div>
            </section>


            {/* ENQUIRY MARQUEE TICKER */}
            <div className="enquiry-ticker-wrapper">
                <div className="enquiry-ticker-track">
                    {/* Group 1 — original */}
                    {[...Array(5)].map((_, i) => (
                        <span key={`a-${i}`} className="enquiry-ticker-item">
                            Can&apos;t find the product you&apos;re looking for?&nbsp;
                            <strong>Enquire now:</strong>&nbsp;
                            <a href="tel:+919384813815" className="ticker-phone">+91 93848 13815</a>
                            <span className="ticker-sep">✦</span>
                        </span>
                    ))}
                    {/* Group 2 — exact duplicate for seamless loop */}
                    {[...Array(5)].map((_, i) => (
                        <span key={`b-${i}`} className="enquiry-ticker-item">
                            Can&apos;t find the product you&apos;re looking for?&nbsp;
                            <strong>Enquire now:</strong>&nbsp;
                            <a href="tel:+919384813815" className="ticker-phone">+91 93848 13815</a>
                            <span className="ticker-sep">✦</span>
                        </span>
                    ))}
                </div>
            </div>

            {/* CATEGORIES SECTION */}
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

            {/* FEATURED PRODUCTS SECTION */}
            <section id="featured-products" className="featured-products-section">
                <div className="container featured-products-container">
                    <div className="featured-header animate-on-scroll">
                        <span className="badge featured-badge">Featured Products</span>
                        <h2 className="featured-title">Top <span className="text-gradient">AI Products</span></h2>
                        <p className="featured-description">Discover our handpicked selection of cutting-edge AI hardware and software solutions.</p>
                    </div>
                    <div className="products-grid">
                        {/* Product 1 */}
                        <div className="product-card animate-on-scroll">
                            <div className="product-image-wrapper">
                                <img src={msiRTX5090} alt="MSI GeForce RTX 5090" className="product-image" onClick={() => navigate('/products/ai-graphics-cards/msi-geforce-rtx-5090-lightning-z-32gb-gddr7')} style={{ cursor: 'pointer' }} />
                                <span className="product-badge badge-bestseller">Flagship</span>
                                <div className="product-overlay"></div>
                            </div>
                            <div className="product-content">
                                <div className="product-category">Graphics Cards</div>
                                <h3 className="product-name" onClick={() => navigate('/products/ai-graphics-cards/msi-geforce-rtx-5090-lightning-z-32gb-gddr7')} style={{ cursor: 'pointer' }}>MSI GeForce RTX™ 5090</h3>
                                <p className="product-description">The ultimate enthusiast GPU featuring 32GB of next-gen GDDR7 memory and unmatched thermal design.</p>
                                <div className="p-action-buttons">
                                    <a href="tel:+919384813815" className="action-btn btn-call"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg> Call for Price</a>
                                    <Link to="/products/ai-graphics-cards/msi-geforce-rtx-5090-lightning-z-32gb-gddr7" className="action-btn btn-view">VIEW</Link>
                                    <a href={`https://wa.me/919384813815?text=Hi! I'm interested in the MSI GeForce RTX 5090`} target="_blank" rel="noopener noreferrer" className="action-btn btn-wa">WhatsApp</a>
                                </div>
                            </div>
                        </div>

                        {/* Product 2 */}
                        <div className="product-card animate-on-scroll">
                            <div className="product-image-wrapper">
                                <img src={nvidiaRTXPro6000MaxQ} alt="NVIDIA RTX Pro 6000 Max-Q" className="product-image" onClick={() => navigate('/products/ai-workstation-gpus/nvidia-rtx-pro-6000-blackwell-max-q')} style={{ cursor: 'pointer' }} />
                                <span className="product-badge badge-new">Pro</span>
                                <div className="product-overlay"></div>
                            </div>
                            <div className="product-content">
                                <div className="product-category">Workstation GPUs</div>
                                <h3 className="product-name" onClick={() => navigate('/products/ai-workstation-gpus/nvidia-rtx-pro-6000-blackwell-max-q')} style={{ cursor: 'pointer' }}>NVIDIA RTX Pro 6000 Max-Q</h3>
                                <p className="product-description">Mobile workstation powerhouse optimized for thin-and-light chassis without compromising AI power.</p>
                                <div className="p-action-buttons">
                                    <a href="tel:+919384813815" className="action-btn btn-call"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg> Call for Price</a>
                                    <Link to="/products/ai-workstation-gpus/nvidia-rtx-pro-6000-blackwell-max-q" className="action-btn btn-view">VIEW</Link>
                                    <a href={`https://wa.me/919384813815?text=Hi! I'm interested in the NVIDIA RTX Pro 6000 Max-Q`} target="_blank" rel="noopener noreferrer" className="action-btn btn-wa">WhatsApp</a>
                                </div>
                            </div>
                        </div>

                        {/* Product 3 */}
                        <div className="product-card animate-on-scroll">
                            <div className="product-image-wrapper">
                                <img src={raspberryPi5} alt="Raspberry Pi 5 Development Board" className="product-image" onClick={() => navigate('/products/ai-dev-boards/raspberry-pi-5-development-board')} style={{ cursor: 'pointer' }} />
                                <span className="product-badge badge-premium">Best Seller</span>
                                <div className="product-overlay"></div>
                            </div>
                            <div className="product-content">
                                <div className="product-category">Dev Boards</div>
                                <h3 className="product-name" onClick={() => navigate('/products/ai-dev-boards/raspberry-pi-5-development-board')} style={{ cursor: 'pointer' }}>Raspberry Pi 5</h3>
                                <p className="product-description">The latest generation of Raspberry Pi, delivering 2-3x the processing power of its predecessor.</p>
                                <div className="p-action-buttons">
                                    <a href="tel:+919384813815" className="action-btn btn-call"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg> Call for Price</a>
                                    <Link to="/products/ai-dev-boards/raspberry-pi-5-development-board" className="action-btn btn-view">VIEW</Link>
                                    <a href={`https://wa.me/919384813815?text=Hi! I'm interested in the Raspberry Pi 5`} target="_blank" rel="noopener noreferrer" className="action-btn btn-wa">WhatsApp</a>
                                </div>
                            </div>
                        </div>

                        {/* Product 4 */}
                        <div className="product-card animate-on-scroll">
                            <div className="product-image-wrapper">
                                <img src={ubiquitiG4Bullet} alt="Ubiquiti UniFi Protect G4 Bullet" className="product-image" onClick={() => navigate('/products/ai-vision-security/ubiquiti-unifi-protect-g4-bullet')} style={{ cursor: 'pointer' }} />
                                <div className="product-overlay"></div>
                            </div>
                            <div className="product-content">
                                <div className="product-category">Vision & Security</div>
                                <h3 className="product-name" onClick={() => navigate('/products/ai-vision-security/ubiquiti-unifi-protect-g4-bullet')} style={{ cursor: 'pointer' }}>UniFi Protect G4 Bullet</h3>
                                <p className="product-description">Versatile 4MP (1440p) indoor/outdoor bullet camera with 24 FPS video and IR LEDs.</p>
                                <div className="p-action-buttons">
                                    <a href="tel:+919384813815" className="action-btn btn-call"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg> Call for Price</a>
                                    <Link to="/products/ai-vision-security/ubiquiti-unifi-protect-g4-bullet" className="action-btn btn-view">VIEW</Link>
                                    <a href={`https://wa.me/919384813815?text=Hi! I'm interested in the UniFi Protect G4 Bullet`} target="_blank" rel="noopener noreferrer" className="action-btn btn-wa">WhatsApp</a>
                                </div>
                            </div>
                        </div>

                        {/* Product 5 */}
                        <div className="product-card animate-on-scroll">
                            <div className="product-image-wrapper">
                                <img src={embeddedAIBundle} alt="Embedded & AI Dev Boards Bundle" className="product-image" onClick={() => navigate('/products/ai-dev-boards/embedded-ai-dev-boards-bundle')} style={{ cursor: 'pointer' }} />
                                <span className="product-badge badge-popular">Bundle</span>
                                <div className="product-overlay"></div>
                            </div>
                            <div className="product-content">
                                <div className="product-category">Dev Boards</div>
                                <h3 className="product-name" onClick={() => navigate('/products/ai-dev-boards/embedded-ai-dev-boards-bundle')} style={{ cursor: 'pointer' }}>Embedded & AI Dev Boards Bundle</h3>
                                <p className="product-description">A comprehensive distributor listing bundle of essential Embedded and AI boards.</p>
                                <div className="p-action-buttons">
                                    <a href="tel:+919384813815" className="action-btn btn-call"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg> Call for Price</a>
                                    <Link to="/products/ai-dev-boards/embedded-ai-dev-boards-bundle" className="action-btn btn-view">VIEW</Link>
                                    <a href={`https://wa.me/919384813815?text=Hi! I'm interested in the Dev Boards Bundle`} target="_blank" rel="noopener noreferrer" className="action-btn btn-wa">WhatsApp</a>
                                </div>
                            </div>
                        </div>

                        {/* Product 6 */}
                        <div className="product-card animate-on-scroll">
                            <div className="product-image-wrapper">
                                <img src={msiRTX4070Ti} alt="MSI RTX 4070 Ti Gaming X Trio 12GB" className="product-image" onClick={() => navigate('/products/ai-graphics-cards/msi-rtx-4070-ti-gaming-x-trio-12gb')} style={{ cursor: 'pointer' }} />
                                <span className="product-badge badge-limited">Popular</span>
                                <div className="product-overlay"></div>
                            </div>
                            <div className="product-content">
                                <div className="product-category">Graphics Cards</div>
                                <h3 className="product-name" onClick={() => navigate('/products/ai-graphics-cards/msi-rtx-4070-ti-gaming-x-trio-12gb')} style={{ cursor: 'pointer' }}>MSI RTX 4070 Ti Gaming X Trio</h3>
                                <p className="product-description">Premium 1440p and 4K capability with whisper-quiet TRI FROZR 3 cooling and 12GB VRAM.</p>
                                <div className="p-action-buttons">
                                    <a href="tel:+919384813815" className="action-btn btn-call"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg> Call for Price</a>
                                    <Link to="/products/ai-graphics-cards/msi-rtx-4070-ti-gaming-x-trio-12gb" className="action-btn btn-view">VIEW</Link>
                                    <a href={`https://wa.me/919384813815?text=Hi! I'm interested in the MSI RTX 4070 Ti`} target="_blank" rel="noopener noreferrer" className="action-btn btn-wa">WhatsApp</a>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="featured-cta animate-on-scroll">
                        <Link to="/products" className="btn-view-all">
                            View All Products
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <line x1="5" y1="12" x2="19" y2="12"></line>
                                <polyline points="12 5 19 12 12 19"></polyline>
                            </svg>
                        </Link>
                    </div>
                </div>
            </section>

            {/* BRANDS SECTION */}
            <section id="brands" className="brands-section">
                <div className="container brands-header-container">
                    <div className="brands-header animate-on-scroll">
                        <span className="brands-badge">Trusted Partners</span>
                        <h2 className="brands-title">
                            Leading Brands <span className="text-gradient-accent">that we deal with</span>
                        </h2>
                        <p className="brands-description">
                            We collaborate with industry leaders to deliver cutting-edge AI solutions powered by the best technology.
                        </p>
                    </div>
                </div>

                {/* Marquee Container */}
                <div className="brands-marquee-wrapper animate-on-scroll">
                    {/* Gradient Overlays */}
                    <div className="brands-fade-left" />
                    <div className="brands-fade-right" />

                    {/* Scrolling Container */}
                    <div className="brands-scroll-track">
                        <div className="brands-marquee">
                            {[
                                { name: "NVIDIA", logo: "https://upload.wikimedia.org/wikipedia/sco/2/21/Nvidia_logo.svg" },
                                { name: "Intel", logo: "https://upload.wikimedia.org/wikipedia/commons/7/7d/Intel_logo_%282006-2020%29.svg" },
                                { name: "AMD", logo: "https://upload.wikimedia.org/wikipedia/commons/7/7c/AMD_Logo.svg" },
                                { name: "Microsoft", logo: "https://upload.wikimedia.org/wikipedia/commons/9/96/Microsoft_logo_%282012%29.svg" },
                                { name: "AWS", logo: "https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg" },
                                { name: "Google Cloud", logo: "https://upload.wikimedia.org/wikipedia/commons/5/51/Google_Cloud_logo.svg" },
                                { name: "IBM", logo: "https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg" },
                                { name: "Qualcomm", logo: "https://upload.wikimedia.org/wikipedia/commons/f/fc/Qualcomm-Logo.svg" },
                                { name: "NVIDIA", logo: "https://upload.wikimedia.org/wikipedia/sco/2/21/Nvidia_logo.svg" },
                                { name: "Intel", logo: "https://upload.wikimedia.org/wikipedia/commons/7/7d/Intel_logo_%282006-2020%29.svg" },
                                { name: "AMD", logo: "https://upload.wikimedia.org/wikipedia/commons/7/7c/AMD_Logo.svg" },
                                { name: "Microsoft", logo: "https://upload.wikimedia.org/wikipedia/commons/9/96/Microsoft_logo_%282012%29.svg" },
                                { name: "AWS", logo: "https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg" },
                                { name: "Google Cloud", logo: "https://upload.wikimedia.org/wikipedia/commons/5/51/Google_Cloud_logo.svg" },
                                { name: "IBM", logo: "https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg" },
                                { name: "Qualcomm", logo: "https://upload.wikimedia.org/wikipedia/commons/f/fc/Qualcomm-Logo.svg" },
                            ].map((partner, index) => (
                                <div key={`${partner.name}-${index}`} className="partner-logo">
                                    <div className="partner-logo-inner">
                                        <img
                                            src={partner.logo}
                                            alt={partner.name}
                                            className="partner-logo-img"
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* SPECIALIZATIONS SECTION */}
            <section id="specializations" className="specializations-section">
                <div className="container">
                    <div className="specializations-header animate-on-scroll">
                        <span className="specializations-badge">Our Expertise</span>
                        <h2 className="specializations-title">
                            What We <span className="text-gradient">Specialize In</span>
                        </h2>
                        <p className="specializations-description">
                            From intelligent surveillance to high-performance computing, we offer end-to-end
                            AI solutions tailored to your industry needs.
                        </p>
                    </div>

                    <div className="specializations-scroll-container">
                        <div className="specializations-grid">
                            {/* AI Cameras Card */}
                            <div className="specialization-card animate-on-scroll">
                                <div className="card-gradient-overlay"></div>
                                <div className="card-content">
                                    <div className="spec-icon">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"></path>
                                            <circle cx="12" cy="13" r="3"></circle>
                                        </svg>
                                    </div>
                                    <div className="spec-subtitle">Intelligent Surveillance</div>
                                    <h3
                                        className="spec-title"
                                        onClick={() => navigate('/products/ai-vision-security')}
                                        style={{ cursor: 'pointer' }}
                                    >AI Cameras</h3>
                                    <p className="spec-description">
                                        Advanced computer vision cameras with real-time object detection, facial recognition, and behavioral analytics for security and retail applications.
                                    </p>

                                    <a href="/products/ai-vision-security" className="learn-more-btn">
                                        Learn More
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="arrow-icon">
                                            <line x1="5" y1="12" x2="19" y2="12"></line>
                                            <polyline points="12 5 19 12 12 19"></polyline>
                                        </svg>
                                    </a>
                                </div>
                            </div>

                            {/* AI Servers Card */}
                            <div className="specialization-card animate-on-scroll">
                                <div className="card-gradient-overlay"></div>
                                <div className="card-content">
                                    <div className="spec-icon">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
                                            <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
                                            <line x1="6" y1="6" x2="6.01" y2="6"></line>
                                            <line x1="6" y1="18" x2="6.01" y2="18"></line>
                                        </svg>
                                    </div>
                                    <div className="spec-subtitle">Enterprise Compute</div>
                                    <h3
                                        className="spec-title"
                                        onClick={() => navigate('/products/ai-networking-storage')}
                                        style={{ cursor: 'pointer' }}
                                    >AI Servers</h3>
                                    <p className="spec-description">
                                        High-performance GPU servers designed for AI training, inference, and deep learning workloads. Built for 24/7 operation with maximum reliability.
                                    </p>

                                    <a href="/products/ai-networking-storage" className="learn-more-btn">
                                        Learn More
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="arrow-icon">
                                            <line x1="5" y1="12" x2="19" y2="12"></line>
                                            <polyline points="12 5 19 12 12 19"></polyline>
                                        </svg>
                                    </a>
                                </div>
                            </div>

                            {/* AI Workstations Card */}
                            <div className="specialization-card animate-on-scroll">
                                <div className="card-gradient-overlay"></div>
                                <div className="card-content">
                                    <div className="spec-icon">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                                            <line x1="8" y1="21" x2="16" y2="21"></line>
                                            <line x1="12" y1="17" x2="12" y2="21"></line>
                                        </svg>
                                    </div>
                                    <div className="spec-subtitle">Developer Power</div>
                                    <h3
                                        className="spec-title"
                                        onClick={() => navigate('/products/ai-workstation-gpus')}
                                        style={{ cursor: 'pointer' }}
                                    >AI Workstations</h3>
                                    <p className="spec-description">
                                        Professional-grade workstations for data scientists and ML engineers. Pre-configured with popular frameworks and optimized for productivity.
                                    </p>

                                    <a href="/products/ai-workstation-gpus" className="learn-more-btn">
                                        Learn More
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="arrow-icon">
                                            <line x1="5" y1="12" x2="19" y2="12"></line>
                                            <polyline points="12 5 19 12 12 19"></polyline>
                                        </svg>
                                    </a>
                                </div>
                            </div>

                            {/* AI Resources Card */}
                            <div className="specialization-card animate-on-scroll">
                                <div className="card-gradient-overlay"></div>
                                <div className="card-content">
                                    <div className="spec-icon">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                                            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                                        </svg>
                                    </div>
                                    <div className="spec-subtitle">Learning & Training</div>
                                    <h3
                                        className="spec-title"
                                        onClick={() => navigate('/products/ai-dev-boards')}
                                        style={{ cursor: 'pointer' }}
                                    >AI Resources</h3>
                                    <p className="spec-description">
                                        Comprehensive educational materials, documentation, and training programs to help your team maximize the potential of AI technology.
                                    </p>

                                    <a href="/products/ai-dev-boards" className="learn-more-btn">
                                        Learn More
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="arrow-icon">
                                            <line x1="5" y1="12" x2="19" y2="12"></line>
                                            <polyline points="12 5 19 12 12 19"></polyline>
                                        </svg>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

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
