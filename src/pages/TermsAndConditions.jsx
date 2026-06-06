import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../components/policy-pages.css';

const TermsAndConditions = () => {
  const location = useLocation();

  return (
    <div className="policy-page">
      {/* Sidebar */}
      <aside className="sidebar">
        <ul className="sidebar-nav">
          <li>
            <Link to="/terms-and-conditions" className={location.pathname === '/terms-and-conditions' ? 'active' : ''}>
              Terms and Conditions
            </Link>
          </li>
          <li>
            <Link to="/privacy-policy" className={location.pathname === '/privacy-policy' ? 'active' : ''}>
              Privacy Policy
            </Link>
          </li>
          <li>
            <Link to="/disclaimer" className={location.pathname === '/disclaimer' ? 'active' : ''}>
              Disclaimer
            </Link>
          </li>
          <li>
            <Link to="/shipping-policy" className={location.pathname === '/shipping-policy' ? 'active' : ''}>
              Shipping Policies
            </Link>
          </li>
        </ul>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <div className="content-header">
          <h1>Terms and Conditions</h1>
        </div>

        <div className="last-updated">
          Last updated on: 8th August 2025.
        </div>

        <div className="content-body">
          <div className="highlight">
            <strong>Effective Date:</strong> 1st January 2006<br />
          </div>

          <p>Welcome to Staunch Technologies. These Terms &amp; Conditions ("Terms") govern your access to and use of our website, products, and services. By using our website, you acknowledge that you have read, understood, and agree to be bound by these Terms and our Privacy Policy.</p>

          <p>If you do not agree to these Terms, please discontinue using our website and services immediately.</p>

          <h2>1. Introduction</h2>
          <p>Staunch Technologies is an IT solutions provider specializing in cybersecurity, intelligent surveillance, IT infrastructure, and AI-powered applications. These Terms outline your rights and obligations when using our website <a href="https://staunchtec.com" target="_blank" rel="noreferrer">https://staunchtec.com</a> and any associated services we offer.</p>

          <h2>2. Legal Compliance</h2>
          <p>We operate in accordance with Indian laws and governance, including but not limited to:</p>
          <ul>
            <li>The Information Technology Act, 2000</li>
            <li>IT (Reasonable Security Practices and Procedures and Sensitive Personal Data or Information) Rules, 2011</li>
            <li>Applicable intellectual property and contract laws in India</li>
          </ul>
          <p>You agree not to use our website or services for any unlawful purpose or in a manner that violates any applicable law.</p>

          <h2>3. Eligibility to Use</h2>
          <p>By using our website or services, you confirm that you:</p>
          <ul>
            <li>Are at least 18 years of age or the legal age of majority in your jurisdiction</li>
            <li>Have the legal capacity to enter into a binding agreement</li>
            <li>Will use the website in accordance with these Terms</li>
          </ul>

          <h2>4. Use of Website &amp; Services</h2>
          <p>When using our website, you agree to:</p>
          <ul>
            <li>Use it only for legitimate and lawful purposes</li>
            <li>Not attempt to gain unauthorized access to any part of our systems or data</li>
            <li>Not engage in activities that could damage, disable, or impair our website</li>
            <li>Provide accurate and truthful information when required</li>
          </ul>
          <p>We reserve the right to restrict access or terminate services for users who violate these Terms.</p>

          <h2>5. Intellectual Property</h2>
          <p>All content, designs, logos, graphics, text, code, and software on our website are the intellectual property of Staunch Technologies, protected by the Indian Copyright Act, 1957 and other applicable laws. Unauthorized use may result in legal action.</p>

          <h2>6. Data Privacy &amp; Security</h2>
          <p>We are committed to protecting your data in compliance with the IT Act, 2000 and related privacy rules.</p>

          <h2>7. Third-Party Services &amp; Links</h2>
          <p>Our website may contain links to third-party websites for your convenience. We are not responsible for the content or practices of such sites.</p>

          <h2>8. Limitation of Liability</h2>
          <p>To the fullest extent permitted by Indian law, Staunch Technologies shall not be liable for any indirect, incidental, or consequential damages arising from your use of our website or services.</p>

          <h2>9. Indemnification</h2>
          <p>You agree to indemnify and hold harmless Staunch Technologies from any claims or damages resulting from your violation of these Terms or applicable laws.</p>

          <h2>10. Changes to Terms</h2>
          <p>We may update these Terms at any time. Continued use of our website constitutes acceptance of the updated Terms.</p>

          <h2>11. Grievance Redressal</h2>
          <p>As per Rule 5(9) of the IT Rules, 2011, we have appointed a Grievance Officer to handle complaints regarding data protection or policy violations.</p>
        </div>
      </main>
    </div>
  );
};

export default TermsAndConditions;
