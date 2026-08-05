import React, { useState } from 'react';
import { MessageCircle, Send, RefreshCw, Sparkles } from 'lucide-react';
import '../pages/floatingreachus.css';

const FloatingReachUs = () => {
  const [open, setOpen] = useState(false);
  const [captchaVerified, setCaptchaVerified] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Simple inline captcha checkbox
  const handleCaptchaChange = (e) => {
    setCaptchaVerified(e.target.checked);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!captchaVerified) {
      alert('Please complete the CAPTCHA verification before sending.');
      return;
    }

    setIsSubmitting(true);

    const formData = {
        name: e.target.name.value,
        email: e.target.email.value,
        phone: e.target.phone.value || "Not Provided",
        product: e.target.product.value || "Floating Quick Inquiry",
        message: e.target.message.value
    };

    try {
        // Connected to Python Unified Backend
        const response = await fetch("https://www.neurostore.in/api/inquiry", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.status === "success") {
            setSubmitted(true);
            setTimeout(() => {
                setSubmitted(false);
                setCaptchaVerified(false);
                setOpen(false);
                e.target.reset();
            }, 2800);
        } else {
            alert("Failed to send inquiry.");
        }
    } catch (error) {
        console.error("Backend Error:", error);
        alert("Could not connect to the backend server. Please ensure app.py is running!");
    } finally {
        setIsSubmitting(false);
    }
  };

  return (
    <>
      {/* VISIBILITY FIX:
        Added strict inline styling to guarantee it is permanently fixed above all UI elements
      */}
      <div
        className="fru-floating-container"
        style={{ position: 'fixed', bottom: '30px', right: '30px', zIndex: 999999, display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}
      >
        {/* Tooltip label */}
        <div className={`fru-tooltip ${open ? 'fru-tooltip--hidden' : ''}`}>
          <span className="fru-tooltip-label">Reach Us</span>
        </div>

        {/* Button */}
        <button
          onClick={() => setOpen(true)}
          aria-label="Open enquiry form"
          className="fru-floating-btn"
        >
          <span className="fru-pulse-ring" />
          <MessageCircle size={24} className="fru-btn-icon" />
        </button>
      </div>

      {/* Backdrop */}
      {open && <div className="fru-backdrop" style={{ zIndex: 999998 }} onClick={() => setOpen(false)} />}

      {/* Dialog */}
      {open && (
        <div className="fru-dialog" style={{ zIndex: 999999 }}>
          {/* Gradient Header */}
          <div className="fru-dialog-header">
            <div className="fru-header-circle fru-header-circle--top" />
            <div className="fru-header-circle fru-header-circle--bottom" />
            <div className="fru-dialog-title-row">
              <div className="fru-title-icon">
                <MessageCircle size={16} color="white" />
              </div>
              <span className="fru-dialog-title">Enquiry Form</span>
            </div>
            <p className="fru-dialog-subtitle">
              Fill in your details and we'll get back to you within 24 hours.
            </p>
            <button className="fru-close-btn" onClick={() => setOpen(false)} aria-label="Close">
              ✕
            </button>
          </div>

          {submitted ? (
            <div className="fru-success">
              <div className="fru-success-icon">
                <Sparkles size={32} color="white" />
              </div>
              <div className="fru-success-text">
                <h3 className="fru-success-title">Message Sent!</h3>
                <p className="fru-success-desc">
                  Thank you for reaching out. Our team will contact you shortly.
                </p>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="fru-form">
              <div className="fru-form-row">
                <div className="fru-form-group">
                  <label htmlFor="reach-name" className="fru-label">
                    Full Name <span className="fru-required">*</span>
                  </label>
                  <input id="reach-name" name="name" type="text" required placeholder="Your full name" className="fru-input" />
                </div>
                <div className="fru-form-group">
                  <label htmlFor="reach-email" className="fru-label">
                    Email <span className="fru-required">*</span>
                  </label>
                  <input id="reach-email" name="email" type="email" required placeholder="your@email.com" className="fru-input" />
                </div>
              </div>

              <div className="fru-form-group">
                <label htmlFor="reach-phone" className="fru-label">Phone Number</label>
                <input id="reach-phone" name="phone" type="tel" placeholder="+1 (555) 000-0000" className="fru-input" />
              </div>

              <div className="fru-form-group">
                <label htmlFor="reach-product" className="fru-label">Product Interest</label>
                <select id="reach-product" name="product" className="fru-input fru-select">
                  <option value="">Select a product category</option>
                  <option value="ai-cameras">AI Cameras &amp; Surveillance</option>
                  <option value="ai-servers">AI Servers &amp; Hardware</option>
                  <option value="ai-workstations">AI Workstations</option>
                  <option value="software">AI Software Solutions</option>
                  <option value="consulting">Consulting Services</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div className="fru-form-group">
                <label htmlFor="reach-message" className="fru-label">
                  Message <span className="fru-required">*</span>
                </label>
                <textarea id="reach-message" name="message" rows={3} required placeholder="Tell us about your inquiry..." className="fru-input fru-textarea" />
              </div>

              <div className="fru-captcha">
                <label className="fru-captcha-label">
                  <input type="checkbox" onChange={handleCaptchaChange} checked={captchaVerified} className="fru-captcha-checkbox" />
                  I'm not a robot
                </label>
              </div>

              <div className="fru-divider" />

              <button type="submit" disabled={isSubmitting} className={`fru-submit-btn ${isSubmitting ? 'fru-submit-btn--loading' : ''}`}>
                {isSubmitting ? (
                  <>
                    <RefreshCw size={16} className="fru-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send size={16} />
                    Send Enquiry
                  </>
                )}
              </button>
            </form>
          )}
        </div>
      )}
    </>
  );
};

export default FloatingReachUs;
