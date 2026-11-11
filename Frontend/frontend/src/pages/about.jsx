import React, { useEffect } from 'react';
import SEO from '../components/SEO';
import './about.css'; // Fixed import path to point to current directory

// All entries below are quoted from staunchtec.com (signature-projects, Client, Alliance pages).
const projects = [
    { name: 'NLC India Limited', detail: 'Associated for the past 20 years. Supplied link load balancers, storage and servers to the corporate office.' },
    { name: 'Nuclear Power Corporation of India Ltd', detail: 'Kudankulam Power Project, associated since 2005.' },
    { name: 'Airport Authority of India, Chennai', detail: 'IT solutions including desktops, laptops and office software, provided since 2009-10.' },
    { name: 'Canara Bank', detail: 'Associated since 2013, with more than 5 crore worth of computing products supplied.' },
    { name: 'Annamalai University', detail: 'Supplied and maintained campus-wide Wi-Fi, including hotspot areas in all 13 hostels.' },
    { name: 'HLL Biotech Limited, Chengalpet', detail: 'Government of India vaccine manufacturing unit; delivered as a turnkey project.' },
];

const clientGroups = [
    { sector: 'Aviation & Space', names: 'Adani Airports Holding Limited, ISRO, Airport Authority of India, AAICLAS' },
    { sector: 'Power', names: 'NTPC, Nuclear Power Corporation of India Ltd, NLC India Ltd' },
    { sector: 'Defence & Public Sector', names: 'Indian Navy, Bharat Dynamics Limited, Tamilnadu Police Academy' },
    { sector: 'Banking', names: 'Canara Bank, AHAM Housing Finance' },
    { sector: 'Education', names: 'Indian Institute of Technology Madras, Annamalai University, Atomic Energy Education Society' },
    { sector: 'Manufacturing', names: 'Ashok Leyland, KIA, Sunfab, Stedman Pharmaceuticals Private Limited' },
];

const partnerGroups = [
    { category: 'Cybersecurity', names: 'Acronis, Broadcom, Fortinet, Sophos, Rapid7' },
    { category: 'Cloud & Productivity', names: 'Microsoft Azure, Microsoft Copilot, ManageEngine, Foxit' },
    { category: 'Enterprise Solutions', names: 'Microsoft, HP, Dell, Juniper, CommScope, Legrand, Poly, Yealink' },
    { category: 'Backup', names: 'Acronis, Commvault, Veeam' },
    { category: 'Surveillance & Security Equipment', names: 'Avigilon, Matrix, Tyco, Vehant, Magtech' },
    { category: 'PCs & Digital Signage', names: 'Dell, HP, Acer, Samsung, LG' },
];
const SourceLinks = ({ links }) => (
    <div className="verified-source">
        <span className="verified-source-label">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                <polyline points="9 12 11 14 15 10"></polyline>
            </svg>
            Verify on Staunch
        </span>
        {links.map((link) => (
            <a className="verified-source-link" href={link.href} target="_blank" rel="noopener noreferrer" key={link.href}>
                {link.label}
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M7 17 17 7"></path>
                    <path d="M8 7h9v9"></path>
                </svg>
            </a>
        ))}
    </div>
);

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
        <SEO
            title="About NeuroStore | Backed by Staunch Technologies, Chennai"
            description="NeuroStore is the online store of Staunch Technologies Pvt Ltd, a GeM-registered enterprise IT and cybersecurity provider based in Chennai with an office in Singapore. See documented projects, clients and technology alliances."
            keywords="about neurostore, Staunch Technologies, GeM registered IT company, enterprise IT Chennai, cybersecurity solutions India, Acronis authorised partner, IT AMC services, neurostore about us"
            ogImage="https://neurostore.in/og-image.webp"
            ogType="website"
        />
            {/* ABOUT SECTION */}
            <section id="about" className="about-section">
                <div className="container about-container">
                    <div className="about-content">
                        {/* Two Column Layout */}
                        <div className="about-grid">
                            {/* Left - Content */}
                            <div className="about-text animate-on-scroll">
                                <span className="about-badge">About NeuroStore</span>
                                
                                
                             
                                <h2 className="about-title">
                                    Enterprise IT Expertise,
                                    <span className="text-gradient"> Now Online</span>
                                    
                                </h2>
                             
                                <p className="about-description">
                                    NeuroStore is the online store of Staunch Technologies Pvt Ltd, an
                                    enterprise IT infrastructure and cybersecurity provider headquartered
                                    in Chennai, with an office in Singapore. We supply software licences,
                                    cybersecurity and backup solutions, and AI computing hardware to
                                    businesses, institutions and government buyers.
                                </p>
                                <p className="about-subdescription">
                                    Staunch Technologies is registered on the Government e-Marketplace
                                    (GeM) and has supplied and supported IT systems for public sector
                                    and enterprise customers in India for many years.
                                </p>
                                <p className="about-note">
                                    The NeuroStore online store is a recent launch. The delivery history,
                                    clients and credentials below belong to Staunch Technologies and are
                                    published on staunchtec.com.
                                </p>

                                {/* CTA Buttons */}
                                <div className="about-buttons">
                                    <a href="#why-us" className="btn btn-primary">
                                        View Credentials
                                    </a>
                                    <a href="/contact" className="btn btn-secondary">
                                        Contact Us
                                    </a>
                                </div>
                            </div>

                            {/* Right - Verified facts */}
                            <div className="stats-grid animate-on-scroll">
                                <div className="stat-card">
                                    <div className="stat-value">20+ Years</div>
                                    <div className="stat-label">Enterprise IT delivery by Staunch Technologies</div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-value">GeM</div>
                                    <div className="stat-label">Registered vendor on the Government e-Marketplace</div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-value">2 Offices</div>
                                    <div className="stat-label">Chennai, India and Singapore</div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-value">Since 2005</div>
                                    <div className="stat-label">Longest documented customer relationship (NPCIL, Kudankulam)</div>
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
                        <span className="why-us-badge">Staunch Credentials</span>
                        <h2 className="why-us-title">
                            Backed by <span className="text-gradient-accent">Staunch Technologies</span>
                        </h2>
                        <p className="why-us-description">
                            Every statement on this page can be checked against the Staunch
                            Technologies website or the documents published there.
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
                                    <h3 className="reason-title">GeM Registered Vendor</h3>
                                    <p className="reason-description">Staunch Technologies is registered on the Government e-Marketplace, supporting compliant procurement for government departments and PSUs.</p>
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
                                    <h3 className="reason-title">Documented Projects</h3>
                                    <p className="reason-description">Infrastructure, networking and computing deployments for public sector, education, banking and enterprise customers.</p>
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
                                    <h3 className="reason-title">Named Leadership</h3>
                                    <p className="reason-description">Led by Mr. P. Mariappan, Managing Director, and Mr. V. Sudhakar, Chief Executive Officer.</p>
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
                                    <h3 className="reason-title">OEM Authorisation</h3>
                                    <p className="reason-description">A Certificate of Authorisation from Acronis is published on the Staunch accreditations page.</p>
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
                                    <h3 className="reason-title">AMC & Managed Support</h3>
                                    <p className="reason-description">Annual maintenance contracts, managed IT and post-deployment support for long-term reliability.</p>
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
                                    <h3 className="reason-title">India & Singapore</h3>
                                    <p className="reason-description">Headquartered in Chennai, Tamil Nadu, with an office in Singapore.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* DOCUMENTED PROJECTS */}
            <section id="projects" className="verified-section">
                <div className="container">
                    <div className="why-us-header animate-on-scroll">
                        <span className="why-us-badge">Documented Projects</span>
                        <h2 className="why-us-title">
                            Delivery <span className="text-gradient-accent">Track Record</span>
                        </h2>
                        <p className="why-us-description">
                            Selected projects published by Staunch Technologies. Dates and scope
                            are quoted from the Staunch signature projects page.
                        </p>
                    </div>
                    <div className="verified-grid">
                        {projects.map((project) => (
                            <div className="verified-card animate-on-scroll" key={project.name}>
                                <h3 className="verified-card-title">{project.name}</h3>
                                <p className="verified-card-text">{project.detail}</p>
                            </div>
                        ))}
                    </div>
                    <SourceLinks links={[{ href: 'https://staunchtec.com/signature-projects', label: 'staunchtec.com/signature-projects' }]} />
                </div>
            </section>

            {/* CLIENTS */}
            <section id="clients" className="verified-section verified-section--alt">
                <div className="container">
                    <div className="why-us-header animate-on-scroll">
                        <span className="why-us-badge">Customers of Staunch</span>
                        <h2 className="why-us-title">
                            Organisations We Have <span className="text-gradient-accent">Served</span>
                        </h2>
                        <p className="why-us-description">
                            Customers listed on the Staunch clients page. Listing does not imply
                            endorsement of NeuroStore products.
                        </p>
                    </div>
                    <div className="verified-grid">
                        {clientGroups.map((group) => (
                            <div className="verified-card animate-on-scroll" key={group.sector}>
                                <h3 className="verified-card-title">{group.sector}</h3>
                                <p className="verified-card-text">{group.names}</p>
                            </div>
                        ))}
                    </div>
                    <SourceLinks links={[{ href: 'https://staunchtec.com/Client', label: 'staunchtec.com/Client' }]} />
                </div>
            </section>

            {/* OEM PARTNERSHIPS */}
            <section id="partners" className="verified-section">
                <div className="container">
                    <div className="why-us-header animate-on-scroll">
                        <span className="why-us-badge">Technology Alliances</span>
                        <h2 className="why-us-title">
                            OEM and <span className="text-gradient-accent">Technology Partners</span>
                        </h2>
                        <p className="why-us-description">
                            Technology partners listed by Staunch Technologies. Only the Acronis
                            Certificate of Authorisation is published as a certificate; other
                            partner listings are alliances, not certifications.
                        </p>
                    </div>
                    <div className="verified-grid">
                        {partnerGroups.map((group) => (
                            <div className="verified-card animate-on-scroll" key={group.category}>
                                <h3 className="verified-card-title">{group.category}</h3>
                                <p className="verified-card-text">{group.names}</p>
                            </div>
                        ))}
                    </div>
                    <SourceLinks links={[
                        { href: 'https://staunchtec.com/Alliance', label: 'staunchtec.com/Alliance' },
                        { href: 'https://staunchtec.com/Certificate', label: 'staunchtec.com/Certificate' },
                    ]} />
                </div>
            </section>

            {/* COMPANY DETAILS */}
            <section id="company" className="verified-section verified-section--alt">
                <div className="container">
                    <div className="why-us-header animate-on-scroll">
                        <span className="why-us-badge">Company Details</span>
                        <h2 className="why-us-title">
                            Who Is <span className="text-gradient-accent">Behind NeuroStore</span>
                        </h2>
                    </div>
                    <div className="verified-grid">
                        <div className="verified-card animate-on-scroll">
                            <h3 className="verified-card-title">India Office</h3>
                            <p className="verified-card-text">
                                Staunch Technologies Pvt Ltd, No.18 (Old No. 166-A), 2nd Floor,
                                Standard House, Mount Road, Little Mount, Chennai - 600015.<br />
                                Phone: +91 (044) 22353175<br />
                                Email: <a href="mailto:info@staunchtec.com">info@staunchtec.com</a>
                            </p>
                        </div>
                        <div className="verified-card animate-on-scroll">
                            <h3 className="verified-card-title">Singapore Office</h3>
                            <p className="verified-card-text">
                                Staunch Tec Pte Ltd, 10 Jalan Besar, #15-09, Sim Lim Tower,
                                Singapore 208787.
                            </p>
                        </div>
                        <div className="verified-card animate-on-scroll">
                            <h3 className="verified-card-title">Leadership</h3>
                            <p className="verified-card-text">
                                Mr. P. Mariappan, Managing Director<br />
                                Mr. V. Sudhakar, Chief Executive Officer
                            </p>
                        </div>
                    </div>
                    <div className="about-buttons verified-actions">
                        <a href="https://staunchtec.com/about-us" className="btn btn-primary" target="_blank" rel="noopener noreferrer">
                            About Staunch Technologies
                        </a>
                        <a href="https://staunchtec.com/Certificate" className="btn btn-secondary" target="_blank" rel="noopener noreferrer">
                            View Accreditations
                        </a>
                    </div>
                </div>
            </section>
        </>
    );
};

export default About;