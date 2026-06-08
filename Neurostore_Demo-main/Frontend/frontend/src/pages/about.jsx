import React, { useEffect } from 'react';
import './about.css'; // Fixed import path to point to current directory

const About = () => {
    useEffect(() => {
        // Intersection Observer for scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '-100px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-view');
                }
            });
        }, observerOptions);

        // Observe all animate-on-scroll elements
        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            observer.observe(el);
        });

        // Observe stat cards individually for stagger effect
        const statCards = document.querySelectorAll('.stat-card');
        statCards.forEach((card, index) => {
            card.style.transitionDelay = `${index * 0.15}s`;
            observer.observe(card);
        });

        // Observe reason cards individually for stagger effect
        const reasonCards = document.querySelectorAll('.reason-card');
        reasonCards.forEach((card, index) => {
            card.style.transitionDelay = `${index * 0.1}s`;
            observer.observe(card);
        });

        // Cleanup
        return () => {
            observer.disconnect();
        };
    }, []);

    return (
        <>
            {/* ABOUT SECTION */}
            <section id="about" className="about-section">
                <div className="container about-container">
                    <div className="about-content">
                        {/* Two Column Layout */}
                        <div className="about-grid">
                            {/* Left - Content */}
                            <div className="about-text animate-on-scroll">
                                <span className="about-badge">About NeuroStore</span>
                                <span className="about-badge">About NeuroStore</span>
                                
                             
                                <h2 className="about-title">
                                    Empowering Businesses with
                                    <span className="text-gradient"> AI Innovation</span>
                                </h2>
                             
                                <p className="about-description">
                                    Since 2018, NeuroStore has been at the forefront of AI hardware
                                    and solutions. We bridge the gap between cutting-edge technology
                                    and practical business applications, helping enterprises worldwide
                                    unlock their full potential.
                                </p>
                                <p className="about-subdescription">
                                    From intelligent surveillance systems to enterprise-grade servers,
                                    we deliver comprehensive AI solutions that drive efficiency, enhance
                                    security, and transform operations. Our commitment to excellence has
                                    made us a trusted partner for businesses across 50+ countries.
                                </p>

                                {/* CTA Buttons */}
                                <div className="about-buttons">
                                    <a href="#specializations" className="btn btn-primary">
                                        Explore Solutions
                                    </a>
                                    <a href="#brands" className="btn btn-secondary">
                                        Our Brands
                                    </a>
                                </div>
                            </div>

                            {/* Right - Stats Grid */}
                            <div className="stats-grid animate-on-scroll">
                                <div className="stat-card">
                                    <div className="stat-icon">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                                            <circle cx="9" cy="7" r="4"></circle>
                                            <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                                            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                                        </svg>
                                    </div>
                                    <div className="stat-value">500+</div>
                                    <div className="stat-label">Enterprise Clients</div>
                                </div>

                                <div className="stat-card">
                                    <div className="stat-icon">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <circle cx="12" cy="12" r="10"></circle>
                                            <line x1="2" y1="12" x2="22" y2="12"></line>
                                            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                                        </svg>
                                    </div>
                                    <div className="stat-value">50+</div>
                                    <div className="stat-label">Countries Served</div>
                                </div>

                                <div className="stat-card">
                                    <div className="stat-icon">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <circle cx="12" cy="8" r="6"></circle>
                                            <path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"></path>
                                        </svg>
                                    </div>
                                    <div className="stat-value">25+</div>
                                    <div className="stat-label">Industry Awards</div>
                                </div>

                                <div className="stat-card">
                                    <div className="stat-icon">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                                        </svg>
                                    </div>
                                    <div className="stat-value">99.9%</div>
                                    <div className="stat-label">Uptime Guarantee</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* WHY CHOOSE US SECTION */}
            <section id="why-us" className="why-us-section">
                <div className="container">
                    <div className="why-us-header animate-on-scroll">
                        <span className="why-us-badge">Why Choose Us</span>
                        <h2 className="why-us-title">
                            The NeuroStore <span className="text-gradient-accent">Advantage</span>
                        </h2>
                        <p className="why-us-description">
                            We don't just sell products—we deliver transformative solutions backed by
                            world-class support and continuous innovation.
                        </p>
                    </div>

                    <div className="reasons-grid">
                        <div className="reason-card animate-on-scroll">
                            <div className="reason-content">
                                <div className="reason-icon">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                                    </svg>
                                </div>
                                <div className="reason-text">
                                    <h3 className="reason-title">Enterprise Security</h3>
                                    <p className="reason-description">Bank-grade encryption and compliance with GDPR, HIPAA, and SOC 2 standards.</p>
                                </div>
                            </div>
                        </div>

                        <div className="reason-card animate-on-scroll">
                            <div className="reason-content">
                                <div className="reason-icon">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                                    </svg>
                                </div>
                                <div className="reason-text">
                                    <h3 className="reason-title">Lightning Fast</h3>
                                    <p className="reason-description">Our AI processors deliver up to 10x faster inference speeds than competitors.</p>
                                </div>
                            </div>
                        </div>

                        <div className="reason-card animate-on-scroll">
                            <div className="reason-content">
                                <div className="reason-icon">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                                        <circle cx="9" cy="7" r="4"></circle>
                                        <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                                        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                                    </svg>
                                </div>
                                <div className="reason-text">
                                    <h3 className="reason-title">Expert Team</h3>
                                    <p className="reason-description">200+ engineers and AI specialists with decades of combined experience.</p>
                                </div>
                            </div>
                        </div>

                        <div className="reason-card animate-on-scroll">
                            <div className="reason-content">
                                <div className="reason-icon">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <circle cx="12" cy="8" r="6"></circle>
                                        <path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"></path>
                                    </svg>
                                </div>
                                <div className="reason-text">
                                    <h3 className="reason-title">Award-Winning</h3>
                                    <p className="reason-description">Recognized by Gartner, Forbes, and CES for innovation and excellence.</p>
                                </div>
                            </div>
                        </div>

                        <div className="reason-card animate-on-scroll">
                            <div className="reason-content">
                                <div className="reason-icon">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M3 11h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-5Zm0 0a9 9 0 1 1 18 0m0 0v5a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3Z"></path>
                                    </svg>
                                </div>
                                <div className="reason-text">
                                    <h3 className="reason-title">24/7 Support</h3>
                                    <p className="reason-description">Round-the-clock technical support with average response time under 15 minutes.</p>
                                </div>
                            </div>
                        </div>

                        <div className="reason-card animate-on-scroll">
                            <div className="reason-content">
                                <div className="reason-icon">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                                        <polyline points="17 6 23 6 23 12"></polyline>
                                    </svg>
                                </div>
                                <div className="reason-text">
                                    <h3 className="reason-title">Scalable Solutions</h3>
                                    <p className="reason-description">From startup to enterprise, our solutions grow seamlessly with your business.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </>
    );
};

export default About;