import React, { useEffect, useRef, useState, useCallback } from 'react';
import SEO from '../components/SEO';
import './contact.css';

// ===== CAPTCHA COMPONENT =====
const generateCaptchaText = (length = 6) => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
};

const Captcha = ({ onVerified }) => {
    const canvasRef = useRef(null);
    const [captchaText, setCaptchaText] = useState('');
    const [userInput, setUserInput] = useState('');
    const [error, setError] = useState(false);
    const [verified, setVerified] = useState(false);

    const drawCaptcha = useCallback((text) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const w = canvas.width;
        const h = canvas.height;

        ctx.fillStyle = 'hsl(240, 10%, 96%)';
        ctx.fillRect(0, 0, w, h);

        // Noise dots
        for (let i = 0; i < 150; i++) {
            ctx.fillStyle = `hsl(${Math.random() * 360}, 40%, ${50 + Math.random() * 30}%)`;
            ctx.beginPath();
            ctx.arc(Math.random() * w, Math.random() * h, Math.random() * 2 + 0.5, 0, Math.PI * 2);
            ctx.fill();
        }

        // Distortion lines
        for (let i = 0; i < 6; i++) {
            ctx.strokeStyle = `hsl(${Math.random() * 360}, 30%, ${60 + Math.random() * 20}%)`;
            ctx.lineWidth = Math.random() * 1.5 + 0.5;
            ctx.beginPath();
            ctx.moveTo(Math.random() * w, Math.random() * h);
            ctx.bezierCurveTo(Math.random() * w, Math.random() * h, Math.random() * w, Math.random() * h, Math.random() * w, Math.random() * h);
            ctx.stroke();
        }

        const fonts = ['Georgia', 'Arial', 'Verdana'];
        const spacing = (w - 40) / text.length;

        text.split('').forEach((char, i) => {
            ctx.save();
            const x = 20 + i * spacing + Math.random() * 8 - 4;
            const y = h / 2 + Math.random() * 14 - 7;
            const angle = (Math.random() - 0.5) * 0.6;
            ctx.translate(x, y);
            ctx.rotate(angle);
            ctx.font = `bold ${24 + Math.random() * 8}px ${fonts[Math.floor(Math.random() * fonts.length)]}`;
            ctx.fillStyle = `hsl(${220 + Math.random() * 60}, 40%, 20%)`;
            ctx.fillText(char, 0, 0);
            ctx.restore();
        });
    }, []);

    const regenerate = useCallback(() => {
        const text = generateCaptchaText();
        setCaptchaText(text);
        setUserInput('');
        setError(false);
        setVerified(false);
        onVerified(false);
        setTimeout(() => drawCaptcha(text), 0);
    }, [drawCaptcha, onVerified]);

    useEffect(() => {
        regenerate();
    }, [regenerate]);

   const handleVerify = () => {
    if (userInput.toLowerCase() === captchaText.toLowerCase()) {
        setVerified(true);
        setError(false);
        onVerified(true);
    } else {
        setVerified(false);
        setError(true);
        onVerified(false);
        setTimeout(() => { regenerate(); }, 2000);
    }
};

    if (verified) {
        return (
            <div className="contact-page-captcha-wrapper contact-page-captcha-verified">
                <span className="contact-page-captcha-check">✓</span>
                <span>Verification successful</span>
            </div>
        );
    }

    return (
        <div className="contact-page-captcha-wrapper">
            <label className="contact-page-captcha-label">Security Verification *</label>
            <div className="contact-page-captcha-canvas-row">
                <canvas ref={canvasRef} width={220} height={60} className="contact-page-captcha-canvas" />
                <button type="button" onClick={regenerate} className="contact-page-captcha-refresh" title="New code">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="23 4 23 10 17 10"></polyline>
                        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                    </svg>
                </button>
            </div>
            <div className="contact-page-captcha-input-row">
                <input
                    type="text"
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder="Type the characters above"
                    className="contact-page-captcha-input"
                />
                <button type="button" onClick={handleVerify} className="contact-page-captcha-verify-btn">
                    Verify
                </button>
            </div>
            {error && <p className="contact-page-captcha-error">Incorrect code. Please try again.</p>}
        </div>
    );
};

// ===== PRODUCT DROPDOWN COMPONENT =====
const ProductDropdown = ({ selected, setSelected }) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

    const options = [
        { value: 'ai-chatbots', label: 'AI Chatbots' },
        { value: 'machine-learning', label: 'Machine Learning Solutions' },
        { value: 'computer-vision', label: 'Computer Vision' },
        { value: 'nlp', label: 'Natural Language Processing' },
        { value: 'data-analytics', label: 'Data Analytics' },
        { value: 'automation', label: 'AI Automation' },
        { value: 'consulting', label: 'Consulting Services' },
        { value: 'other', label: 'Other' }
    ];

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <div className="contact-page-form-group">
            <label>Product Interest</label>
            <div className="contact-page-dropdown-wrapper" ref={dropdownRef}>
                <div
                    className={`contact-page-dropdown-selected ${isOpen ? 'active' : ''}`}
                    onClick={() => setIsOpen(!isOpen)}
                >
                    <span className={selected ? '' : 'contact-page-dropdown-placeholder'}>
                        {selected || 'Select a product category'}
                    </span>
                    <svg
                        className={`contact-page-dropdown-arrow ${isOpen ? 'open' : ''}`}
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                    >
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </div>
                <div className={`contact-page-dropdown-list ${isOpen ? 'open' : ''}`}>
                    {options.map((option) => (
                        <div
                            key={option.value}
                            className="contact-page-dropdown-item"
                            onClick={() => {
                                setSelected(option.label);
                                setIsOpen(false);
                            }}
                        >
                            {option.label}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

// ===== MAIN CONTACT PAGE =====
const Contact = () => {
    const contactFormRef = useRef(null);
    const [isCaptchaVerified, setIsCaptchaVerified] = useState(false);
    const [showModal, setShowModal] = useState(false);
    const [captchaKey, setCaptchaKey] = useState(0);
    const [selectedProduct, setSelectedProduct] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        const observerOptions = { threshold: 0.1, rootMargin: '-50px' };
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) entry.target.classList.add('contact-page-in-view');
            });
        }, observerOptions);

        document.querySelectorAll('.contact-page-animate-on-scroll').forEach(el => observer.observe(el));
        const contactCards = document.querySelectorAll('.contact-page-contact-card');
        contactCards.forEach((card, index) => {
            card.style.transitionDelay = `${index * 0.15}s`;
            observer.observe(card);
        });

        return () => observer.disconnect();
    }, []);

    const handleSubmit = async (e) => {
      e.preventDefault();

      if (!isCaptchaVerified) {
        alert("Please complete the captcha verification first.");
        return;
      }

      setIsSubmitting(true);
      const form = e.target;

      const formData = {
        name: form.name.value,
        email: form.email.value,
        phone: form.phone.value,
        product: selectedProduct || "General Inquiry",
        message: form.message.value
      };

      try {
        // Connected to Python unified backend /api/inquiry
        const response = await fetch("https://www.neurostore.in/api/inquiry", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(formData),
        });

        const data = await response.json();

        if (data.status === "success") {
          setShowModal(true);
          form.reset();
          setIsCaptchaVerified(false);
          setSelectedProduct('');
          setCaptchaKey(prev => prev + 1);
        } else {
          alert("Failed to send message.");
        }

      } catch (error) {
        console.error(error);
        alert("Server error. Please ensure the backend (app.py) is running!");
      } finally {
        setIsSubmitting(false);
      }
    };

    return (
        <>
<SEO
  title="Contact Neurostore | AI Hardware Sales & Support India"
  description="Contact Neurostore for AI hardware sales, GPU pricing, bulk orders and technical support. Reach us at our Chennai office or via WhatsApp, email and phone."
  keywords="contact neurostore, AI hardware support India, GPU sales inquiry India, bulk AI hardware order India, neurostore Chennai"
  ogImage="https://www.neurostore.in/og-image.webp"
  ogType="website"
/>
        <section id="contact" className="contact-page-contact-section">
            <div className="contact-page-container contact-page-contact-container">
                <div className="contact-page-contact-header contact-page-animate-on-scroll">
                    <span className="contact-page-contact-badge">Get in Touch</span>
                    <h2 className="contact-page-contact-title">
                        We're Here to <span className="contact-page-text-gradient">Help You</span>
                    </h2>
                    <p className="contact-page-contact-description">
                        Have questions about our AI products and solutions? Our team is ready to assist you. Reach out through any of the channels below.
                    </p>
                </div>

                <div className="contact-page-contact-info-grid">
                    <div className="contact-page-contact-card contact-page-animate-on-scroll">
                        <div className="contact-page-contact-icon-wrapper">
                            <div className="contact-page-contact-icon">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                                    <circle cx="12" cy="10" r="3"></circle>
                                </svg>
                            </div>
                        </div>
                        <div className="contact-page-contact-details">
                            <h3 className="contact-page-contact-label">Address</h3>
                            <p className="contact-page-contact-value">Staunch Technologies Pvt Ltd<br/>No.18 (Old No. 166-A),<br/>2nd Floor, STANDARD HOUSE,<br/>Mount Road, Little Mount,<br/>Chennai-600015.</p>
                        </div>
                    </div>

                    <div className="contact-page-contact-card contact-page-animate-on-scroll">
                        <div className="contact-page-contact-icon-wrapper">
                            <div className="contact-page-contact-icon">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                                </svg>
                            </div>
                        </div>
                        <div className="contact-page-contact-details">
                            <h3 className="contact-page-contact-label">Phone</h3>
                            <a href="tel:+9104422353175" className="contact-page-contact-link">+91 (044) 22353175</a>
                        </div>
                    </div>

                    <div className="contact-page-contact-card contact-page-animate-on-scroll">
                        <div className="contact-page-contact-icon-wrapper">
                            <div className="contact-page-contact-icon">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                                    <polyline points="22,6 12,13 2,6"></polyline>
                                </svg>
                            </div>
                        </div>
                        <div className="contact-page-contact-details">
                            <h3 className="contact-page-contact-label">Email</h3>
                            <a href="mailto:info@staunchtec.com" className="contact-page-contact-link">info@staunchtec.com</a>
                        </div>
                    </div>

                    <div className="contact-page-contact-card contact-page-animate-on-scroll">
                        <div className="contact-page-contact-icon-wrapper">
                            <div className="contact-page-contact-icon">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <line x1="2" y1="12" x2="22" y2="12"></line>
                                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                                </svg>
                            </div>
                        </div>
                        <div className="contact-page-contact-details">
                            <h3 className="contact-page-contact-label">Website</h3>
                            <a href="https://www.neurostore.in" className="contact-page-contact-link" target="_blank" rel="noopener noreferrer">
                                neurostore.in
                            </a>
                        </div>
                    </div>
                </div>

                <div className="contact-page-form-map-wrapper contact-page-animate-on-scroll">
                    <div className="contact-page-contact-form-wrapper">
                        <h3 className="contact-page-form-title">Send Us a Message</h3>
                        <p className="contact-page-form-subtitle">Fill out the form below and we'll get back to you within 24 hours</p>
                        <form className="contact-page-contact-form" ref={contactFormRef} onSubmit={handleSubmit}>
                            <div className="contact-page-form-group">
                                <label>Full Name *</label>
                                <input type="text" name="name" placeholder="Enter your full name" required />
                            </div>

                            <div className="contact-page-form-group">
                                <label>Email Address *</label>
                                <input type="email" name="email" placeholder="your.email@example.com" required />
                            </div>

                            <div className="contact-page-form-group">
                                <label>Phone Number *</label>
                                <input type="tel" name="phone" placeholder="+1 (555) 000-0000" required />
                            </div>

                            <ProductDropdown
                                selected={selectedProduct}
                                setSelected={setSelectedProduct}
                            />

                            <div className="contact-page-form-group">
                                <label>Your Message *</label>
                                <textarea name="message" rows="4" placeholder="Tell us about your project or inquiry..." required></textarea>
                            </div>

                            <Captcha key={captchaKey} onVerified={setIsCaptchaVerified} />

                            <button
                                type="submit"
                                className="contact-page-submit-btn"
                                style={{ opacity: isCaptchaVerified && !isSubmitting ? 1 : 0.7 }}
                                disabled={!isCaptchaVerified || isSubmitting}
                            >
                                <span>{isSubmitting ? 'Sending...' : 'Send Message'}</span>
                                {!isSubmitting && (
                                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                      <line x1="22" y1="2" x2="11" y2="13"></line>
                                      <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                                  </svg>
                                )}
                            </button>
                        </form>

                        {showModal && (
                            <div className="contact-modal-overlay">
                                <div className="contact-modal-box">
                                    <button
                                        className="contact-modal-close-icon"
                                        onClick={() => {
                                            setShowModal(false);
                                            setCaptchaKey(prev => prev + 1);
                                        }}
                                    >
                                        ✕
                                    </button>
                                    <div className="contact-modal-content">
                                        <h2>Thank You!</h2>
                                        <p>
                                            We have received your message.
                                            Our team will reach out to you soon!
                                        </p>
                                        <button
                                            className="contact-modal-close-btn"
                                            onClick={() => {
                                                setShowModal(false);
                                                setCaptchaKey(prev => prev + 1);
                                            }}
                                        >
                                            Close
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="contact-page-map-section">
                        <div className="contact-page-map-container">
                            <iframe
                                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3517.8349334176096!2d80.22052097454721!3d13.014373613940123!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3a52670040382487%3A0x260c45d05d175ea3!2sStaunch%20Technologies%20Private%20Limited!5e1!3m2!1sen!2sin!4v1772020248602!5m2!1sen!2sin"
                                width="100%"
                                height="100%"
                                style={{ border: 0 }}
                                allowFullScreen=""
                                loading="lazy"
                                referrerPolicy="no-referrer-when-downgrade"
                                title="Staunch Technologies Location"
                            ></iframe>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        </>
    );
};

export default Contact;
