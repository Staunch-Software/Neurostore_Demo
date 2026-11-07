import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import '../pages/ProductDetails.css';

const QuoteRequestModal = ({ items, onClose, onSent }) => {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [sent, setSent] = useState(false);

    const productList = items.map((i) => `${i.name} (x${i.qty})`).join(', ');

    const handleSubmit = async (e) => {
        e.preventDefault();
        const form = e.target;
        setIsSubmitting(true);
        try {
            const response = await fetch('/api/inquiry', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: form.name.value,
                    email: form.email.value,
                    phone: form.phone.value || 'Not Provided',
                    product: `[Cart Quote Request] ${productList}`,
                    message: form.message.value || `Please share a quote for: ${productList}`,
                }),
            });
            if (response.ok) {
                setSent(true);
                onSent?.();
            } else {
                alert('Failed to send quote request.');
            }
        } catch {
            alert('Could not connect to the server. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return createPortal(
        <div className="pd-modal-overlay" onClick={onClose}>
            <div className="pd-modal-box" onClick={(e) => e.stopPropagation()}>
                <button className="pd-modal-close" onClick={onClose}>✕</button>
                {sent ? (
                    <>
                        <div className="pd-success-icon">✓</div>
                        <h2 className="pd-modal-title">Quote Request Sent!</h2>
                        <p className="pd-modal-subtitle">
                            Our sales team will email you the pricing shortly.
                        </p>
                        <button className="pd-modal-submit-btn" onClick={onClose}>Close</button>
                    </>
                ) : (
                    <>
                        <h2 className="pd-modal-title">Request a Quote</h2>
                        <p className="pd-modal-subtitle">
                            Pricing is shared on request for:<br /><strong>{productList}</strong>
                        </p>
                        <form onSubmit={handleSubmit} className="pd-modal-form">
                            <div className="pd-form-group">
                                <label>Full Name *</label>
                                <input type="text" name="name" required placeholder="John Doe" />
                            </div>
                            <div className="pd-form-group">
                                <label>Email Address *</label>
                                <input type="email" name="email" required placeholder="john@example.com" />
                            </div>
                            <div className="pd-form-group">
                                <label>Phone Number</label>
                                <input type="tel" name="phone" placeholder="+91 98765 43210" />
                            </div>
                            <div className="pd-form-group">
                                <label>Message</label>
                                <textarea name="message" rows="3" placeholder="Quantity, requirements, etc."></textarea>
                            </div>
                            <button type="submit" className="pd-modal-submit-btn" disabled={isSubmitting}>
                                {isSubmitting ? 'Sending...' : 'Request Quote'}
                            </button>
                        </form>
                    </>
                )}
            </div>
        </div>,
        document.body
    );
};

export default QuoteRequestModal;
