import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../components/policy-pages.css';

const Disclaimer = () => {
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
          <h1>Disclaimer</h1>
        </div>

        <div className="last-updated">
          Last updated on: 8th August 2025.
        </div>

        <div className="content-body">
          <div className="highlight">
            <strong>Effective Date:</strong> 1st January 2006<br />
          </div>

          <div className="warning">
            <strong>Important Notice:</strong> Please read this disclaimer carefully before using our website and services. This disclaimer outlines the limitations of our liability and your responsibilities as a user.
          </div>

          <h2>1. No Warranty</h2>
          <p>The information on the Staunch Technologies website (<a href="https://staunchtec.com" target="_blank" rel="noreferrer">https://staunchtec.com</a>) is provided for general informational purposes only. We make no representations or warranties of any kind, express or implied, about:</p>
          <ul>
            <li>The completeness, accuracy, reliability, or suitability of the information</li>
            <li>The availability or functionality of our website</li>
            <li>The performance of our products or services</li>
            <li>The fitness of our solutions for any particular purpose</li>
          </ul>
          <p>Any reliance you place on such information is strictly at your own risk.</p>

          <h2>2. Limitation of Liability</h2>
          <p>Staunch Technologies shall not be liable for any losses or damages, including but not limited to:</p>
          <ul>
            <li>Direct, indirect, incidental, or consequential damages</li>
            <li>Loss of profits, data, or business opportunities</li>
            <li>Damages resulting from system downtime or technical failures</li>
            <li>Losses arising from your use or inability to use our website or services</li>
            <li>Any errors, omissions, or inaccuracies in the content</li>
          </ul>
          <p>This limitation applies regardless of whether we have been advised of the possibility of such damages.</p>

          <h2>3. Third-Party Links and Content</h2>
          <p>Our website may contain links to external websites or reference third-party products and services. We do not:</p>
          <ul>
            <li>Endorse or recommend any third-party websites, products, or services</li>
            <li>Take responsibility for the content, privacy practices, or policies of external sites</li>
            <li>Guarantee the accuracy or reliability of third-party information</li>
            <li>Accept liability for any damages resulting from your use of external links</li>
          </ul>
          <p>You access third-party websites at your own risk and should review their terms and conditions.</p>

          <h2>4. Professional Advice</h2>
          <p>The content on our website, including technical specifications, recommendations, and guidance:</p>
          <ul>
            <li>Should not be considered as professional advice for your specific situation</li>
            <li>Is not a substitute for consultation with qualified IT professionals</li>
            <li>May not be applicable to all business environments or requirements</li>
            <li>Should be verified independently before implementation</li>
          </ul>
          <p>We strongly recommend consulting with appropriate professionals before making any business or technical decisions based on our content.</p>

          <h2>5. Technical Information</h2>
          <p>While we strive to provide accurate technical information:</p>
          <ul>
            <li>Technology specifications and capabilities may change without notice</li>
            <li>Performance metrics are estimates and may vary in different environments</li>
            <li>Compatibility information may become outdated</li>
            <li>Security recommendations reflect current best practices but cannot guarantee absolute protection</li>
          </ul>

          <h2>6. Service Availability</h2>
          <p>We do not guarantee that our website or services will be:</p>
          <ul>
            <li>Available at all times without interruption</li>
            <li>Free from errors, bugs, or technical issues</li>
            <li>Compatible with all devices, browsers, or operating systems</li>
            <li>Secure from unauthorized access or cyber threats</li>
          </ul>
          <p>We reserve the right to modify, suspend, or discontinue any part of our website or services without prior notice.</p>

          <h2>7. User Responsibilities</h2>
          <p>As a user of our website and services, you are responsible for:</p>
          <ul>
            <li>Verifying the accuracy of information before acting upon it</li>
            <li>Maintaining the confidentiality of your account credentials</li>
            <li>Using our services in accordance with applicable laws and regulations</li>
            <li>Implementing appropriate security measures for your systems</li>
            <li>Creating regular backups of your important data</li>
          </ul>

          <h2>8. Force Majeure</h2>
          <p>Staunch Technologies shall not be liable for any failure or delay in performance due to circumstances beyond our reasonable control, including but not limited to:</p>
          <ul>
            <li>Natural disasters, pandemics, or acts of God</li>
            <li>Government actions, regulations, or sanctions</li>
            <li>Internet service provider failures or network outages</li>
            <li>Cyber attacks, hacking attempts, or security breaches</li>
            <li>Supplier or vendor failures</li>
          </ul>

          <h2>9. Intellectual Property</h2>
          <p>While we respect intellectual property rights:</p>
          <ul>
            <li>We do not guarantee that our content is free from copyright or trademark infringement claims</li>
            <li>Users are responsible for ensuring their use of our content complies with applicable IP laws</li>
            <li>We disclaim liability for any IP infringement arising from user modifications or implementations</li>
          </ul>

          <h2>10. Data Security</h2>
          <p>Despite our security measures:</p>
          <ul>
            <li>We cannot guarantee absolute security of data transmission over the internet</li>
            <li>Users are responsible for implementing their own security measures</li>
            <li>We disclaim liability for data breaches beyond our reasonable control</li>
            <li>Users should regularly update their security software and practices</li>
          </ul>

          <h2>11. Changes to Disclaimer</h2>
          <p>We reserve the right to modify this Disclaimer at any time without prior notice. Changes will be effective immediately upon posting on our website. Your continued use of our website after changes constitutes acceptance of the modified Disclaimer.</p>

          <h2>12. Governing Law</h2>
          <p>This Disclaimer shall be governed by and construed in accordance with the laws of India. Any disputes arising from this Disclaimer shall be subject to the exclusive jurisdiction of the courts in Chennai, Tamil Nadu, India.</p>

          <h2>13. Contact Information</h2>
          <p>If you have any questions about this Disclaimer, please contact us at:</p>
          <ul>
            <li><strong>Email:</strong> info@staunchtec.com</li>
            <li><strong>Phone:</strong> +91 (044) 22353175</li>
            <li><strong>Address:</strong> Staunch Technologies Pvt Ltd, No.18 (Old No. 166-A), 2nd Floor, Standard House, Mount Road, Little Mount, Chennai-600015</li>
          </ul>

          <div className="warning">
            <strong>Final Note:</strong> This disclaimer is designed to inform users of the limitations of our liability. By using our website and services, you acknowledge that you have read, understood, and agree to be bound by this disclaimer.
          </div>
        </div>
      </main>
    </div>
  );
};

export default Disclaimer;
