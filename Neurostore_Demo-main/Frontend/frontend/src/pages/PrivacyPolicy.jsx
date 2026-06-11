import React from 'react';
import { Helmet } from 'react-helmet-async';
import { Link, useLocation } from 'react-router-dom';
import '../components/policy-pages.css';

const PrivacyPolicy = () => {
  const location = useLocation();

  return (
    <>
        <Helmet>
        <link rel="canonical" href="https://www.neurostore.in/privacy-policy" />
        </Helmet>
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
          <h1>Privacy Policy</h1>
        </div>

        <div className="last-updated">
          Last updated on: 8th August 2025.
        </div>

        <div className="content-body">
          <div className="highlight">
            <strong>Effective Date:</strong> 1st January 2006<br />
          </div>

          <p>Staunch Technologies respects your privacy and is committed to protecting your personal information in compliance with the Information Technology Act, 2000 and related Rules.</p>

          <h2>1. Information We Collect</h2>
          <p>We collect the following types of information:</p>
          <ul>
            <li><strong>Personal Details:</strong> Name, email address, phone number</li>
            <li><strong>Sensitive Personal Data:</strong> Passwords, financial details (collected only with explicit consent)</li>
            <li><strong>Non-Personal Information:</strong> IP address, browser type, device information for analytics purposes</li>
          </ul>

          <h2>2. How We Use Your Information</h2>
          <p>We use the collected information to:</p>
          <ul>
            <li>Provide and improve our services</li>
            <li>Respond to inquiries and customer support requests</li>
            <li>Send updates, notices, and marketing communications</li>
            <li>Ensure security and prevent fraud</li>
            <li>Comply with legal obligations</li>
          </ul>

          <h2>3. Data Security</h2>
          <p>We implement robust security measures to protect your data, including:</p>
          <ul>
            <li>End-to-end encryption for sensitive data transmission</li>
            <li>Role-based access controls</li>
            <li>Continuous security monitoring and threat detection</li>
            <li>Regular security audits and updates</li>
            <li>Secure data storage with industry-standard protocols</li>
          </ul>

          <h2>4. Data Sharing</h2>
          <p>We share your data only in the following circumstances:</p>
          <ul>
            <li>With trusted partners and service providers who assist in our operations</li>
            <li>When required for legal compliance or court orders</li>
            <li>To protect our rights, property, or safety</li>
            <li>In case of business transfers or mergers (with prior notification)</li>
          </ul>
          <p>We do not sell, rent, or trade your personal information to third parties for marketing purposes.</p>

          <h2>5. Your Rights</h2>
          <p>Under Indian privacy laws, you have the following rights:</p>
          <ul>
            <li><strong>Right to Access:</strong> Request copies of your personal data</li>
            <li><strong>Right to Correct:</strong> Request correction of inaccurate or incomplete data</li>
            <li><strong>Right to Delete:</strong> Request deletion of your personal data</li>
            <li><strong>Right to Withdraw Consent:</strong> Withdraw consent for data processing</li>
            <li><strong>Right to Data Portability:</strong> Request transfer of your data</li>
          </ul>

          <h2>6. Cookies &amp; Tracking Technologies</h2>
          <p>We use cookies and similar tracking technologies to:</p>
          <ul>
            <li>Enhance user experience and website functionality</li>
            <li>Analyze website traffic and usage patterns</li>
            <li>Remember your preferences and settings</li>
            <li>Provide personalized content and advertisements</li>
          </ul>
          <p>You can control cookie settings through your browser preferences.</p>

          <h2>7. Data Retention</h2>
          <p>We retain your personal data only for as long as necessary to fulfill the purposes outlined in this policy or as required by applicable laws. Data is securely deleted or anonymized when no longer needed.</p>

          <h2>8. International Data Transfers</h2>
          <p>If we transfer your data outside India, we ensure appropriate safeguards are in place to protect your information in accordance with Indian data protection laws.</p>

          <h2>9. Children's Privacy</h2>
          <p>Our services are not intended for children under 18 years of age. We do not knowingly collect personal information from children without parental consent.</p>

          <h2>10. Grievance Officer</h2>
          <p>As per IT Rules, 2011, we have appointed a Grievance Officer to address privacy concerns and complaints. Contact details for grievance redressal are provided on our website at <a href="https://staunchtec.com/contact" target="_blank" rel="noreferrer">https://staunchtec.com/contact</a>.</p>

          <h2>11. Updates to Privacy Policy</h2>
          <p>We may update this Privacy Policy from time to time. We will notify you of any material changes by posting the updated policy on our website with a revised effective date.</p>

          <h2>12. Contact Information</h2>
          <p>If you have any questions about this Privacy Policy, please contact us at:</p>
          <ul>
            <li>Email: info@staunchtec.com</li>
            <li>Phone: +91 (044) 22353175</li>
            <li>Address: Staunch Technologies Pvt Ltd, No.18 (Old No. 166-A), 2nd Floor, Standard House, Mount Road, Little Mount, Chennai-600015</li>
          </ul>
        </div>
      </main>
    </div>
    </>
  );
};

export default PrivacyPolicy;
