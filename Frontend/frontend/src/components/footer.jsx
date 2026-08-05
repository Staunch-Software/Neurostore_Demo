import React from 'react';
import { Link } from 'react-router-dom';
import "../pages/footer.css";

const Footer = () => {
  return (
    <footer className="main-footer">
      <div className="footer-top">
        <div className="container">
          <div className="footer-content">
            {/* Company Info Section */}
            <div className="footer-column company-info">
              <h3 className="footer-title">Staunch Tech</h3>
              <p className="company-description">
                GeM Registered IT, Cybersecurity & Digital Solutions Provider in India
              </p>
              <a href="/about" className="read-more">
                read more →
              </a>
            </div>

            {/* Quick Links Section */}
            <div className="footer-column quick-links">
              <h3 className="footer-title">Quick Links</h3>
              <ul>
                <li>
                  <a href="/"> Home</a>
                </li>
                <li>
                  <a href="/about"> About Us</a>
                </li>
                <li>
                  <a href="/contact"> Contact</a>
                </li>
              </ul>
            </div>

            {/* Services Section */}
            <div className="footer-column quick-links">
              <h3 className="footer-title">SERVICES</h3>
              <ul>
                <li><a href="#">Software Development</a></li>
                <li><a href="#">Cybersecurity</a></li>
                <li><a href="#">Managed IT Services</a></li>
                <li><a href="#">Cloud Computing</a></li>
                <li><a href="#">AI Based Solutions</a></li>
              </ul>
            </div>

            {/* Contact Info Section */}
            <div className="footer-column contact-info">
              <h3 className="footer-title">Contact Us</h3>
              <ul>
                <li>
                  <i className="fas fa-envelope"></i>
                  <div>
                    <span className="label">Email:</span>
                    <a href="mailto:info@staunchtec.com">info@staunchtec.com</a>
                  </div>
                </li>
                <li>
                  <i className="fas fa-phone"></i>
                  <div>
                    <span className="label">Phone:</span>
                    <a href="tel:+91 (044) 22353175">+91 (044) 22353175</a>
                  </div>
                </li>
                <li>
                  <i className="fas fa-map-marker-alt"></i>
                  <div>
                    <span className="label">Address:</span>
                    <span>
                      Staunch Technologies Pvt Ltd<br />
                      No.18 (Old No. 166-A),<br />
                      2nd Floor, STANDARD HOUSE,<br />
                      Mount Road, Little Mount,<br />
                      Chennai-600015.
                    </span>
                  </div>
                </li>
              </ul>
            </div>

            {/* Social Media Section */}
            <div className="footer-column social-media">
              <h3 className="footer-title">Follow Us</h3>
              <div className="social-icons">
                <a href="https://www.facebook.com/Staunchtec/" className="social-icon facebook" aria-label="Facebook">
                  <i className="fab fa-facebook-f"></i>
                </a>
                <a href="https://www.linkedin.com/company/staunchtechnologies/" className="social-icon linkedin" aria-label="LinkedIn">
                  <i className="fab fa-linkedin-in"></i>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Bottom */}
      <div className="footer-bottom">
        <div className="container footer-bottom-container">
          <div className="footer-bottom-copyright">
            <p>&copy; Staunch Technologies Pvt Ltd. All Rights Reserved.</p>
          </div>
          <div className="footer-bottom-links">
            <Link to="/terms-and-conditions">Terms and<br />Conditions</Link>
            <span className="separator">|</span>
            <Link to="/privacy-policy">Privacy<br />Policy</Link>
            <span className="separator">|</span>
            <Link to="/disclaimer">Disclaimer</Link>
            <span className="separator">|</span>
            <Link to="/shipping-policy">Shipping<br />Policies</Link>
          </div>
          <div className="footer-bottom-motto">
            <p><i>Delivering Innovative Solutions</i></p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;