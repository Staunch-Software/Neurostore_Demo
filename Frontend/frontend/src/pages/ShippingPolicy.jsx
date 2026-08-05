import React from 'react';
import SEO from '../components/SEO';
import { Link, useLocation } from 'react-router-dom';
import '../components/policy-pages.css';

const ShippingPolicy = () => {
  const location = useLocation();

  return (
    <>
      <SEO
        title="Shipping Policy | Neurostore"
        description="Read Neurostore's shipping policy, refund and cancellation terms. Orders cancelled within 7 days. Refunds processed within 15 days. Fast delivery across India via DHL, FedEx and UPS."
        keywords="neurostore shipping policy, AI hardware delivery India, neurostore refund policy, neurostore cancellation policy, AI hardware shipping India"
        ogImage="https://www.neurostore.in/og-image.webp"
        ogType="website"
      />
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
          <h1>Shipping Policies - Staunch Technologies</h1>
        </div>

        <div className="last-updated">
          Last updated on: 26th August 2025
        </div>

        <div className="content-body">

          {/* Terms & Conditions Section */}
          <div className="policy-section" id="terms">
            <h1 className="section-title">Terms &amp; Conditions</h1>

            <div className="highlight">
              <strong>Electronic Record:</strong> This document is an electronic record under the Information Technology Act, 2000<br />
              <strong>Effective Date:</strong> Published in accordance with Rule 3(1) of IT Rules, 2011
            </div>

            <p>This document is an electronic record in terms of Information Technology Act, 2000 and rules there under as applicable and the amended provisions pertaining to electronic records in various statutes as amended by the Information Technology Act, 2000.</p>

            <p>This document is published in accordance with the provisions of Rule 3 (1) of the Information Technology (Intermediaries guidelines) Rules, 2011 that require publishing the rules and regulations, privacy policy and Terms of Use for access or usage of domain name <a href="https://staunchtec.com" target="_blank" rel="noreferrer" style={{ color: '#1a73e8' }}>https://staunchtec.com</a> (hereinafter referred to as 'Platform').</p>

            <div style={{ background: '#f8f9fa', padding: '15px', borderRadius: '5px', margin: '20px 0', borderLeft: '4px solid #1a73e8' }}>
              <strong>Platform Owner:</strong> Staunch Technologies Private Limited<br />
              <strong>Registration:</strong> Company incorporated under the Companies Act, 1956<br />
              <strong>Registered Office:</strong> F3, BAID MEHTA COMPLEX, 16, MOUNT ROAD LITTLE MOUNT, CHENNAI 600 015, Tamil Nadu, India - 600015
            </div>

            <h2>Agreement and Acceptance</h2>
            <p>Your use of the Platform and services and tools are governed by the following terms and conditions ("Terms of Use") as applicable to the Platform. By mere use of the Platform, You shall be contracting with the Platform Owner and these terms and conditions including the policies constitute Your binding obligations, with Platform Owner.</p>

            <p><strong style={{ color: '#d32f2f' }}>ACCESSING, BROWSING OR OTHERWISE USING THE PLATFORM INDICATES YOUR AGREEMENT TO ALL THE TERMS AND CONDITIONS UNDER THESE TERMS OF USE, SO PLEASE READ THE TERMS OF USE CAREFULLY BEFORE PROCEEDING.</strong></p>

            <h2>Terms of Use</h2>
            <ol>
              <li>To access and use the Services, you agree to provide true, accurate and complete information to us during and after registration.</li>
              <li>Neither we nor any third parties provide any warranty or guarantee as to the accuracy, timeliness, performance, completeness or suitability of the information and materials offered on this website or through the Services.</li>
              <li>Your use of our Services and the Platform is solely and entirely at your own risk and discretion for which we shall not be liable to you in any manner.</li>
              <li>The contents of the Platform and the Services are proprietary to us and are licensed to us. You will not have any authority to claim any intellectual property rights, title, or interest in its contents.</li>
              <li>You acknowledge that unauthorized use of the Platform and/or the Services may lead to action against you as per these Terms of Use and/or applicable laws.</li>
              <li>You agree to pay us the charges associated with availing the Services.</li>
              <li>You agree not to use the Platform and/or Services for any purpose that is unlawful, illegal or forbidden by these Terms, or Indian or local laws that might apply to you.</li>
              <li>You agree and acknowledge that website and the Services may contain links to other third party websites.</li>
              <li>You understand that upon initiating a transaction for availing the Services you are entering into a legally binding and enforceable contract with the Platform Owner for the Services.</li>
            </ol>

            <h2>Indemnification</h2>
            <p>You shall indemnify and hold harmless Platform Owner, its affiliates, group companies and their respective officers, directors, agents, and employees, from any claim or demand made by any third party or penalty imposed due to or arising out of Your breach of this Terms of Use, privacy Policy and other Policies, or Your violation of any law, rules or regulations or the rights of a third party.</p>

            <h2>Force Majeure</h2>
            <p>Notwithstanding anything contained in these Terms of Use, the parties shall not be liable for any failure to perform an obligation under these Terms if performance is prevented or delayed by a force majeure event.</p>

            <h2>Governing Law and Jurisdiction</h2>
            <p>These Terms and any dispute or claim relating to it shall be governed by and construed in accordance with the laws of India. All disputes arising out of or in connection with these Terms shall be subject to the exclusive jurisdiction of the courts in Chennai, Tamil Nadu.</p>

            <h2>Contact Information</h2>
            <p>All concerns or communications relating to these Terms must be communicated to us using the contact information provided on this website.</p>
          </div>

          {/* Privacy Policy Section */}
          <div className="policy-section" id="privacy">
            <h1 className="section-title">Privacy Policy</h1>

            <div className="highlight">
              <strong>Data Protection:</strong> In accordance with IT Act, 2000 and applicable privacy laws<br />
              <strong>Scope:</strong> Applies to all users of https://staunchtec.com
            </div>

            <h2>Introduction</h2>
            <p>This Privacy Policy describes how <strong>Staunch Technologies Private Limited</strong> and its affiliates collect, use, share, protect or otherwise process your information/ personal data through our website <a href="https://staunchtec.com" target="_blank" rel="noreferrer" style={{ color: '#1a73e8' }}>https://staunchtec.com</a>.</p>

            <h2>Collection of Information</h2>
            <p>We collect your personal data when you use our Platform. Some of the information that we may collect includes:</p>
            <ul>
              <li>Name</li>
              <li>Date of birth</li>
              <li>Address</li>
              <li>Telephone/mobile number</li>
              <li>Email ID</li>
              <li>Any such information shared as proof of identity or address</li>
            </ul>

            <p><strong style={{ color: '#d32f2f' }}>Security Alert:</strong> If you receive an email, a call from a person/association claiming to be Staunch Technologies Private Limited seeking any personal data like debit/credit card PIN, net-banking or mobile banking password, we request you to never provide such information.</p>

            <h2>Grievance Officer</h2>
            <div style={{ background: '#f8f9fa', padding: '15px', borderRadius: '5px', margin: '20px 0', borderLeft: '4px solid #1a73e8' }}>
              <p><strong>Mr. V. Sudhakar</strong><br />
                <strong>Chief Executive Officer</strong><br />
                <strong>Staunch Technologies Private Limited<br />F3, BAID MEHTA COMPLEX<br />16, MOUNT ROAD LITTLE MOUNT, CHENNAI 600 015<br />Tamil Nadu, India - 600015</strong>
              </p>
              <p><strong>Contact us: info@staunchtec.com</strong><br />
                <strong>Phone: +91 98405 52326</strong><br />
                <strong>Time:</strong> Monday - Friday (9:30 - 18:30)
              </p>
            </div>
          </div>

          {/* Refund & Cancellation Section */}
          <div className="policy-section" id="refund">
            <h1 className="section-title">Refund and Cancellation Policy</h1>

            <div className="highlight">
              <strong>Policy Scope:</strong> Applies to all products/services purchased through our Platform<br />
              <strong>Processing Time:</strong> Refunds processed within 15 days of approval
            </div>

            <h2>Cancellation Policy</h2>
            <ol>
              <li>Cancellations will only be considered if the request is made <strong>within 7 days</strong> of placing the order.</li>
              <li>In case you feel that the product received is not as shown on the site or as per your expectations, you must bring it to the notice of our customer service <strong>within 7 days</strong> of receiving the product.</li>
              <li>In case of complaints regarding the products that come with a warranty from the manufacturers, please refer the issue to them.</li>
            </ol>

            <h2>Refund Processing</h2>
            <p>In case of any refunds approved by <strong>Staunch Technologies Private Limited</strong>, it will take <strong>15 days</strong> for the refund to be processed to you.</p>

            <h2>Important Notes</h2>
            <ul>
              <li>All refund and cancellation requests must be made through our official customer service channels</li>
              <li>Original proof of purchase must be provided for all refund requests</li>
              <li>Refunds will be processed through the same payment method used for the original purchase</li>
              <li>Service charges or processing fees may be deducted from the refund amount as applicable</li>
            </ul>
          </div>

        </div>
      </main>
    </div>
    </>
  );
};

export default ShippingPolicy;
