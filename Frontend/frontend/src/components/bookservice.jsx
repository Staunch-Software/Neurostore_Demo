import React, { useState } from 'react';
import '../pages/bookservice.css';

const BookService = ({ open, onClose, serviceName, services }) => {
  const [selectedService, setSelectedService] = useState(serviceName || '');

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    message: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedService) {
      alert("Please select a service");
      return;
    }

    setIsSubmitting(true);

    const bookingData = {
      name: formData.name,
      email: formData.email,
      phone: formData.phone,
      company: formData.company,
      message: formData.message,
      service: selectedService,
    };

    try {
      // Pointing to the unified Python Backend
      const response = await fetch("http://localhost:5000/api/book-service", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(bookingData),
      });

      const data = await response.json();

      if (data.status === "success") {
        setFormData({
          name: "",
          email: "",
          phone: "",
          company: "",
          message: "",
        });
        setSelectedService("");
        setShowSuccess(true);
      } else {
        alert("Failed to submit booking.");
      }
    } catch (error) {
      console.error(error);
      alert("Server error. Please ensure the backend is running!");
    }

    setIsSubmitting(false);
  };

  const updateField = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSuccessClose = () => {
    setShowSuccess(false);
    onClose();
  };

  if (!open) return null;

  return (
    <div
      className={`booking-dialog-overlay ${open ? 'booking-dialog-overlay-active' : ''}`}
      onClick={onClose}
    >
      <div
        className={`booking-dialog-content ${open ? 'booking-dialog-content-active' : ''}`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="booking-dialog-header">
          <div>
            <h2 className="booking-dialog-title">Book a Service</h2>
            <p className="booking-dialog-subtitle">Fill in your details and we'll get back to you</p>
          </div>
          <button
            onClick={onClose}
            className="booking-dialog-close"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="booking-dialog-form">
          {/* Service Selection */}
          <div className="booking-form-section">
            <label className="booking-form-label">
              Select Service
            </label>
            <div className="booking-service-grid">
              {services && services.map((service) => {
                const isSelected = selectedService === service.title;
                return (
                  <button
                    key={service.title}
                    type="button"
                    onClick={() => setSelectedService(service.title)}
                    className={`booking-service-option ${isSelected ? 'booking-service-option-selected' : ''}`}
                  >
                    <div className={`booking-service-icon ${service.color}`}>
                      {service.icon}
                    </div>
                    <span className="booking-service-name">
                      {service.title}
                    </span>
                    {isSelected && (
                      <div className="booking-service-check">
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Contact Fields */}
          <div className="booking-form-grid">
            <div className="booking-form-field">
              <label className="booking-input-label">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
                Full Name
              </label>
              <input
                required
                type="text"
                placeholder="John Doe"
                value={formData.name}
                onChange={(e) => updateField('name', e.target.value)}
                maxLength={100}
                className="booking-input"
              />
            </div>
            <div className="booking-form-field">
              <label className="booking-input-label">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="2"></rect>
                  <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
                </svg>
                Email
              </label>
              <input
                required
                type="email"
                placeholder="john@company.com"
                value={formData.email}
                onChange={(e) => updateField('email', e.target.value)}
                maxLength={255}
                className="booking-input"
              />
            </div>
            <div className="booking-form-field">
              <label className="booking-input-label">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                </svg>
                Phone
              </label>
              <input
                type="tel"
                placeholder="+91 98765 43210"
                value={formData.phone}
                onChange={(e) => updateField('phone', e.target.value)}
                maxLength={20}
                className="booking-input"
              />
            </div>
            <div className="booking-form-field">
              <label className="booking-input-label">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                  <polyline points="9 22 9 12 15 12 15 22"></polyline>
                </svg>
                Company
              </label>
              <input
                type="text"
                placeholder="Your Company"
                value={formData.company}
                onChange={(e) => updateField('company', e.target.value)}
                maxLength={100}
                className="booking-input"
              />
            </div>
          </div>

          <div className="booking-form-field">
            <label className="booking-input-label">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
              Message (optional)
            </label>
            <textarea
              placeholder="Tell us about your requirements..."
              rows={3}
              value={formData.message}
              onChange={(e) => updateField('message', e.target.value)}
              maxLength={1000}
              className="booking-textarea"
            />
          </div>

          {/* Submit */}
          <div className="booking-form-actions">
            <button
              type="submit"
              className="booking-submit-btn"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <div className="booking-spinner" />
              ) : (
                <>
                  Submit Booking Request
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                  </svg>
                </>
              )}
            </button>
            <button
              type="button"
              className="booking-cancel-btn"
              onClick={onClose}
            >
              Cancel
            </button>
          </div>
        </form>

      {/* Success Modal */}
      {showSuccess && (
        <div
          className="booking-dialog-overlay booking-dialog-overlay-active"
          onClick={handleSuccessClose}
        >
          <div
            className="success-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <button className="booking-dialog-close" onClick={handleSuccessClose} style={{ position: 'absolute', top: '16px', right: '16px' }}>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
            <h2 className="success-title">Thank You!</h2>
            <p className="success-message">
              We have received your message. Our team will reach out to you soon!
            </p>
            <button className="success-close-btn" onClick={handleSuccessClose}>
              Close
            </button>
          </div>
        </div>
      )}
      </div>
    </div>
  );
};

export default BookService;