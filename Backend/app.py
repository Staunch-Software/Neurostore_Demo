import os
import json
import hmac
import random
import string
import hashlib
import smtplib
import sqlite3
import razorpay
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

load_dotenv(override=True)

app = Flask(__name__)
CORS(app)


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════════════════
def get_db_connection():
    conn = sqlite3.connect('neurostore.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            phone TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            items TEXT,
            total REAL,
            address TEXT,
            payment TEXT,
            payment_id TEXT,
            status TEXT DEFAULT 'Confirmed',
            created_at TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            user_email TEXT PRIMARY KEY,
            cart_data TEXT NOT NULL DEFAULT '{}'
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS wishlists (
            user_email TEXT PRIMARY KEY,
            wishlist_data TEXT NOT NULL DEFAULT '[]'
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS otp_verifications (
            email TEXT PRIMARY KEY,
            name TEXT,
            otp TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            attempts INTEGER DEFAULT 0
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS addresses (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            label      TEXT DEFAULT '',
            name       TEXT DEFAULT '',
            street     TEXT DEFAULT '',
            city       TEXT DEFAULT '',
            state      TEXT DEFAULT '',
            zip        TEXT DEFAULT '',
            country    TEXT DEFAULT 'India',
            is_default INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()


init_db()


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN AUTH MIDDLEWARE
# ══════════════════════════════════════════════════════════════════════════════
ADMIN_USER = os.getenv("ADMIN_USERNAME", "neuroadmin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "staunchtech2026")


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USER or auth.password != ADMIN_PASS:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL CONFIG
# ══════════════════════════════════════════════════════════════════════════════
EMAIL_USER         = os.getenv("EMAIL_USER", "staunchtech2025@gmail.com")
EMAIL_PASS         = os.getenv("EMAIL_PASS", "iureiloiizprbolo")
OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", 10))


def send_email_helper(subject, html_body, reply_to):
    try:
        msg = MIMEMultipart()
        msg['From']    = f"Website Notification <{EMAIL_USER}>"
        msg['To']      = EMAIL_USER
        msg['Subject'] = subject
        if reply_to:
            msg.add_header('reply-to', reply_to)
        msg.attach(MIMEText(html_body, 'html'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"EMAIL ERROR: {e}")
        return False


def send_otp_email(to_email, name, otp_code):
    try:
        html_body = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;background:#f9fafb;padding:40px 20px;">
          <div style="background:#fff;border-radius:16px;padding:40px;border:1px solid #e2e8f0;text-align:center;">
            <h2 style="color:#0f172a;margin:0 0 8px;">NeuroStore</h2>
            <p style="color:#64748b;margin:0 0 32px;">Email Verification</p>
            <p style="color:#0f172a;font-size:16px;margin:0 0 24px;">
              Hi <strong>{name}</strong>, here is your verification code:
            </p>
            <div style="background:#f1f5f9;border-radius:12px;padding:20px;margin:0 0 24px;
                        letter-spacing:12px;font-size:36px;font-weight:700;color:#1e1b4b;font-family:monospace;">
              {otp_code}
            </div>
            <p style="color:#64748b;font-size:14px;margin:0 0 8px;">
              This code expires in <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.
            </p>
            <p style="color:#94a3b8;font-size:12px;margin:0;">
              If you did not request this, please ignore this email.
            </p>
          </div>
        </div>"""

        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Your NeuroStore Verification Code'
        msg['From']    = f'NeuroStore <{EMAIL_USER}>'
        msg['To']      = to_email
        msg.attach(MIMEText(html_body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"OTP EMAIL ERROR: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTS DATA
# ══════════════════════════════════════════════════════════════════════════════
std_hw = {"Condition": "Brand New / Sealed", "Availability": "In Stock", "Delivery": "3-5 Business Days",
          "Return Policy": "7 Days Replacement", "Support": "Lifetime Email Support",
          "Packaging": "Official Retail Box", "Certifications": "ISO, CE, RoHS Compliant"}
std_sw = {"Condition": "Digital License", "Availability": "Instant Activation", "Delivery": "Immediate via Email",
          "Updates": "Free Automatic Updates", "Support": "24/7 Priority Support",
          "Training": "Documentation & Guides Included", "Platform": "Cloud / Web Based"}

products = [
    {"id": 1, "name": "MSI GeForce RTX™ 5090 Lightning Z 32GB GDDR7", "category": "AI Graphics Cards", "brand": "MSI",
     "price": 250000, "badge": "Flagship", "moq": "1 pc",
     "shortDescription": "The ultimate enthusiast GPU featuring 32GB of next-gen GDDR7 memory.",
     "description": "The MSI GeForce RTX™ 5090 Lightning Z redefines ultra-high-performance gaming and rendering. Powered by the latest NVIDIA architecture.",
     "additionalInfo": {**{"Brand": "MSI", "CUDA Cores": "24576", "Memory": "32GB GDDR7", "Memory Interface": "512-bit",
                           "Boost Clock": "2.9 GHz", "TDP": "600W", "Recommended PSU": "1000W+",
                           "Outputs": "3x DisplayPort 2.1, 1x HDMI 2.1"}, **std_hw},
     "warranty": "3 Year Manufacturer Warranty."},
    {"id": 2, "name": "NVIDIA RTX Pro 6000 Blackwell Max-Q", "category": "AI Workstation GPUs", "brand": "NVIDIA",
     "price": 450000, "badge": "Pro", "moq": "1 pc",
     "shortDescription": "Mobile workstation powerhouse optimized for thin-and-light chassis.",
     "description": "The NVIDIA RTX Pro 6000 Blackwell Max-Q Workstation Edition brings desktop-class rendering and AI capabilities to mobile form factors.",
     "additionalInfo": {
         **{"Brand": "NVIDIA", "Architecture": "Blackwell Mobile", "CUDA Cores": "9728", "Memory": "16GB GDDR6 ECC",
            "TDP": "80W - 115W", "Interface": "Mobile MXM / PCIe 4.0", "Compute Performance": "35.5 TFLOPS",
            "ISV Certified": "Yes"}, **std_hw}, "warranty": "3 Year Enterprise Warranty."},
    {"id": 3, "name": "NVIDIA RTX Pro 6000 Blackwell Workstation Edition", "category": "AI Workstation GPUs",
     "brand": "NVIDIA", "price": 550000, "badge": "Enterprise", "moq": "1 pc",
     "shortDescription": "The definitive desktop workstation GPU for massive datasets.",
     "description": "Designed for the most demanding professional workflows, the desktop RTX Pro 6000 Blackwell provides immense VRAM and CUDA core counts.",
     "additionalInfo": {**{"Brand": "NVIDIA", "CUDA Cores": "18176", "Memory": "48GB GDDR6 ECC", "TDP": "300W",
                           "Interface": "PCIe 4.0 x16", "Display Connectors": "4x DisplayPort 1.4a",
                           "NVLink": "Supported", "Form Factor": "Dual Slot"}, **std_hw},
     "warranty": "3 Year Enterprise Warranty."},
    {"id": 4, "name": "ASRock AMD Radeon RX 9070 XT Challenger 16GB", "category": "AI Graphics Cards",
     "brand": "ASRock", "price": 95000, "badge": "Value", "moq": "2 pcs",
     "shortDescription": "High-end 4K gaming and compute performance with 16GB GDDR6 memory.",
     "description": "The ASRock Radeon RX 9070 XT Challenger offers incredible rasterization performance and 16GB of GDDR6 memory.",
     "additionalInfo": {
         **{"Brand": "ASRock", "Stream Processors": "6144", "Memory": "16GB GDDR6", "Boost Clock": "2.6 GHz",
            "TDP": "300W", "PSU Required": "750W", "Interface": "PCIe 5.0", "Outputs": "DP 2.1, HDMI 2.1"}, **std_hw},
     "warranty": "3 Year Manufacturer Warranty."},
    {"id": 5, "name": "Asus Dual RX 9060 XT 16GB GDDR6", "category": "AI Graphics Cards", "brand": "ASUS",
     "price": 75000, "badge": "New", "moq": "2 pcs",
     "shortDescription": "Excellent 1440p performance featuring ASUS's renowned Dual cooling.",
     "description": "The ASUS Dual RX 9060 XT 16GB delivers the latest AMD architecture in its purest form.",
     "additionalInfo": {
         **{"Brand": "ASUS", "Stream Processors": "4096", "Memory": "16GB GDDR6", "Boost Clock": "2.5 GHz",
            "TDP": "200W", "PSU Required": "600W", "Cooling": "Dual Axial-tech Fans",
            "Outputs": "3x DP 2.1, 1x HDMI 2.1"}, **std_hw}, "warranty": "3 Year ASUS Warranty."},
    {"id": 6, "name": "Raspberry Pi 5 Development Board", "category": "AI Dev Boards", "brand": "Raspberry Pi",
     "price": 8500, "badge": "Best Seller", "moq": "10 pcs",
     "shortDescription": "The latest generation of Raspberry Pi, delivering 2-3x the processing power.",
     "description": "The Raspberry Pi 5 features a 64-bit quad-core Arm Cortex-A76 processor running at 2.4GHz.",
     "additionalInfo": {**{"Processor": "Quad-core ARM Cortex-A76 @ 2.4GHz", "Memory": "4GB/8GB LPDDR4X",
                           "Connectivity": "Wi-Fi 5, BT 5.0", "Ports": "2x USB 3.0, 2x USB 2.0",
                           "Display": "2x micro-HDMI", "Storage": "MicroSD slot", "GPIO": "40-pin header",
                           "Power": "5V/5A DC Type-C"}, **std_hw}, "warranty": "1 Year Standard Warranty."},
    {"id": 7, "name": "Raspberry Pi 4 Development Board", "category": "AI Dev Boards", "brand": "Raspberry Pi",
     "price": 5500, "moq": "20 pcs",
     "shortDescription": "The classic, highly reliable SBC featuring a quad-core processor.",
     "description": "A staple in the maker community, the Raspberry Pi 4 Model B offers groundbreaking increases in processor speed.",
     "additionalInfo": {**{"Processor": "Quad-core ARM Cortex-A72 @ 1.5GHz", "Memory": "2GB/4GB/8GB LPDDR4",
                           "Connectivity": "Wi-Fi 5, BT 5.0", "Ports": "2x USB 3.0, 2x USB 2.0",
                           "Display": "2x micro-HDMI", "Storage": "MicroSD slot", "GPIO": "40-pin header",
                           "Power": "5V/3A DC Type-C"}, **std_hw}, "warranty": "1 Year Standard Warranty."},
    {"id": 8, "name": "Raspberry Pi Camera V2 (8MP)", "category": "AI Vision & Security", "brand": "Raspberry Pi",
     "price": 2500, "moq": "25 pcs", "shortDescription": "High-quality 8 megapixel Sony IMX219 image sensor.",
     "description": "The Raspberry Pi Camera Module v2 is a high quality 8 megapixel Sony IMX219 image sensor custom designed add-on.",
     "additionalInfo": {
         **{"Sensor": "Sony IMX219", "Resolution": "8 Megapixels", "Video Modes": "1080p30, 720p60", "Interface": "CSI",
            "Lens": "Fixed focus", "FOV": "62.2 degrees", "Dimensions": "25 x 24 x 9 mm",
            "Supported OS": "Raspberry Pi OS"}, **std_hw}, "warranty": "1 Year Standard Warranty."},
    {"id": 9, "name": "Raspberry Pi Pico (RP2040)", "category": "AI Dev Boards", "brand": "Raspberry Pi", "price": 500,
     "badge": "Budget", "moq": "50 pcs",
     "shortDescription": "A fast, versatile, and incredibly affordable microcontroller board.",
     "description": "Built using the RP2040 microcontroller chip designed by Raspberry Pi.", "additionalInfo": {
        **{"Microcontroller": "RP2040", "Processor": "Dual-core ARM Cortex M0+", "Clock Speed": "133 MHz",
           "SRAM": "264KB", "Flash Memory": "2MB", "GPIO": "26 multi-function pins",
           "Inputs": "2x SPI, 2x I2C, 2x UART", "Power": "1.8-5.5V DC"}, **std_hw},
     "warranty": "1 Year Standard Warranty."},
    {"id": 10, "name": "Ubiquiti UniFi Protect G4 Bullet", "category": "AI Vision & Security", "brand": "Ubiquiti",
     "price": 18000, "badge": "Pro", "moq": "5 pcs",
     "shortDescription": "Versatile 4MP (1440p) indoor/outdoor bullet camera.",
     "description": "The UniFi Protect G4 Bullet Camera delivers clear 4MP, 24 fps video over Gigabit Ethernet.",
     "additionalInfo": {**{"Sensor": "4 MP CMOS", "Resolution": "2688 x 1520 (24 FPS)", "Lens": "Fixed focal length",
                           "Viewing Angle": "H: 86°, V: 60°", "Night Vision": "Built-in IR LEDs",
                           "Networking": "Gigabit Ethernet", "Power Method": "802.3af PoE",
                           "Durability": "IP67 Weatherproof"}, **std_hw}, "warranty": "1 Year Ubiquiti Warranty."},
    {"id": 11, "name": "Ubiquiti UNVR (Network Video Recorder)", "category": "AI Networking & Storage",
     "brand": "Ubiquiti", "price": 35000, "moq": "1 pc",
     "shortDescription": "Enterprise network video recorder with 4 drive bays.",
     "description": "The UniFi Network Video Recorder (UNVR) is an enterprise NVR that provides automated redundant storage.",
     "additionalInfo": {
         **{"Drive Bays": "4x 2.5/3.5-inch SATA", "Processor": "Quad-core ARM Cortex-A57", "Memory": "4 GB",
            "Network Interface": "1x 10G SFP+, 1x GbE RJ45", "Max Cameras": "Up to 50 HD cameras",
            "RAID Support": "RAID 1, 5", "Power Supply": "100W Internal", "Rackmountable": "1U"}, **std_hw},
     "warranty": "1 Year Ubiquiti Warranty."},
    {"id": 12, "name": "Tapo Pan/Tilt Home Security Wi-Fi Camera", "category": "AI Vision & Security",
     "brand": "TP-Link", "price": 3000, "moq": "10 pcs",
     "shortDescription": "High-definition indoor security camera with 360° horizontal viewing.",
     "description": "Capture every detail with 1080p definition. The Tapo Pan/Tilt camera provides 360° horizontal and 114° vertical range.",
     "additionalInfo": {**{"Resolution": "1080p (1920 x 1080)", "Field of View": "360° Horizontal, 114° Vertical",
                           "Night Vision": "850 nm IR up to 30 ft", "Audio": "Two-Way Audio",
                           "Storage": "MicroSD (up to 128 GB)", "Wireless Rate": "150 Mbps (2.4 GHz)",
                           "Motion Detection": "Yes", "App Support": "Tapo App"}, **std_hw},
     "warranty": "2 Year TP-Link Warranty."},
    {"id": 13, "name": "Embedded & AI Dev Boards Bundle", "category": "AI Dev Boards", "brand": "Various",
     "price": 45000, "badge": "Bundle", "moq": "1 Kit",
     "shortDescription": "A comprehensive distributor listing bundle of essential boards.",
     "description": "Perfect for institutions and prototyping labs, this distributor bundle includes a curated selection of embedded systems.",
     "additionalInfo": {**{"Contents": "5x Various AI Boards", "Processors": "ARM Cortex / RISC-V",
                           "NPU Included": "Yes (Up to 2 TOPS)", "Memory Options": "1GB - 8GB LPDDR4",
                           "Connectivity": "Wi-Fi, BLE, Ethernet", "Interfaces": "MIPI-CSI, DSI, GPIO",
                           "Use Case": "Prototyping & R&D", "Support": "Yocto, Ubuntu, Android"}, **std_hw},
     "warranty": "Varies by individual board manufacturer."},
    {"id": 14, "name": "Raspberry Pi Camera V2 / Noir V2 Kit", "category": "AI Vision & Security",
     "brand": "Raspberry Pi", "price": 4500, "moq": "15 Kits",
     "shortDescription": "Combo kit featuring both standard and NoIR infrared modules.",
     "description": "This vision kit includes both the standard Pi Camera V2 and the Pi NoIR V2 module.",
     "additionalInfo": {
         **{"Sensors Included": "1x IMX219 (Standard), 1x IMX219 (NoIR)", "Resolution": "8 Megapixels each",
            "Infrared Filter": "Removed on NoIR", "Video": "1080p30 / 720p60", "Interface": "CSI port",
            "Lens Type": "Fixed focus", "Included Accessories": "Ribbon cables, Mounts",
            "Use Case": "Day/Night vision"}, **std_hw}, "warranty": "1 Year Standard Warranty."},
    {"id": 15, "name": "Raspberry Pi 4 / 3 / Zero & Accessories Kit", "category": "AI Dev Boards",
     "brand": "Raspberry Pi", "price": 15000, "badge": "Kit", "moq": "5 Kits",
     "shortDescription": "Complete ecosystem starter pack including multiple Pi boards.",
     "description": "The ultimate Raspberry Pi ecosystem kit. This comprehensive package includes multiple generations of Pi boards.",
     "additionalInfo": {
         **{"Boards Included": "Pi 4 Model B, Pi 3 Model B+, Pi Zero W", "Accessories": "Power Supplies, Heat Sinks",
            "Storage": "3x 32GB Class 10 MicroSD", "Cases": "Official Enclosures included",
            "Cables": "Micro/Mini HDMI to HDMI", "Connectivity": "Onboard Wi-Fi/Bluetooth",
            "Target Audience": "Educational Labs", "Warranty": "Official Parts Warranty"}, **std_hw},
     "warranty": "1 Year Standard Warranty."},
    {"id": 16, "name": "MSI RTX 4080 Gaming X Trio 16GB", "category": "AI Graphics Cards", "brand": "MSI",
     "price": 115000, "moq": "2 pcs", "shortDescription": "High-tier Ada Lovelace GPU with exceptional cooling.",
     "description": "Game in style with the MSI RTX 4080 Gaming X Trio. Upgraded with TRI FROZR 3, TORX FAN 5.0.",
     "additionalInfo": {
         **{"Brand": "MSI", "CUDA Cores": "9728", "Memory": "16GB GDDR6X", "Boost Clock": "2520 MHz", "TDP": "320W",
            "PSU Required": "750W", "Interface": "PCIe 4.0", "Cooling": "TRI FROZR 3"}, **std_hw},
     "warranty": "3 Year Manufacturer Warranty."},
    {"id": 17, "name": "Asus Dual RTX 4070 12GB", "category": "AI Graphics Cards", "brand": "ASUS", "price": 65000,
     "moq": "5 pcs", "shortDescription": "Compact and powerful RTX 4070 featuring two Axial-tech fans.",
     "description": "The ASUS Dual GeForce RTX™ 4070 fuses dynamic thermal performance with broad compatibility.",
     "additionalInfo": {
         **{"Brand": "ASUS", "CUDA Cores": "5888", "Memory": "12GB GDDR6X", "Boost Clock": "2475 MHz", "TDP": "200W",
            "PSU Required": "650W", "Interface": "PCIe 4.0", "Form Factor": "2.5 Slot"}, **std_hw},
     "warranty": "3 Year ASUS Warranty."},
    {"id": 18, "name": "MSI RTX 4070 Ti Gaming X Trio 12GB", "category": "AI Graphics Cards", "brand": "MSI",
     "price": 85000, "badge": "Popular", "moq": "3 pcs",
     "shortDescription": "Premium 1440p and 4K capability with whisper-quiet cooling.",
     "description": "The MSI RTX 4070 Ti Gaming X Trio strikes the perfect balance between high-end performance and acoustic stealth.",
     "additionalInfo": {
         **{"Brand": "MSI", "CUDA Cores": "7680", "Memory": "12GB GDDR6X", "Boost Clock": "2610 MHz", "TDP": "285W",
            "PSU Required": "700W", "Cooling": "TRI FROZR 3", "Dimensions": "337 x 140 x 62 mm"}, **std_hw},
     "warranty": "3 Year Manufacturer Warranty."},
    {"id": 19, "name": "LG 27GS60F UltraGear Monitor", "category": "AI Monitors", "brand": "LG", "price": 15000,
     "moq": "1 pc", "shortDescription": "Pure gaming monitor featuring 180Hz refresh rate and 1ms response time.",
     "description": "The LG 27GS60F is a performance-focused UltraGear gaming monitor featuring a stunning FHD IPS panel.",
     "additionalInfo": {**{"Panel Type": "27-inch IPS", "Resolution": "FHD (1920x1080)", "Refresh Rate": "180Hz",
                           "Response Time": "1ms (GtG)", "Color Gamut": "sRGB 99%", "HDR": "HDR10",
                           "Adaptive Sync": "G-Sync / FreeSync", "Ports": "1x DP, 2x HDMI"}, **std_hw},
     "warranty": "3 Year LG Warranty."},
    {"id": 20, "name": "LG 27GS65F UltraGear Monitor", "category": "AI Monitors", "brand": "LG", "price": 17000,
     "moq": "1 pc", "shortDescription": "Gaming-focused display with height adjustment and HDR10.",
     "description": "Elevate your gaming setup with the LG 27GS65F UltraGear monitor. Featuring an FHD IPS display running at 180Hz.",
     "additionalInfo": {**{"Panel Type": "27-inch IPS", "Resolution": "FHD (1920x1080)", "Refresh Rate": "180Hz",
                           "Response Time": "1ms (GtG)", "Ergonomics": "Tilt/Height/Pivot", "Color Gamut": "sRGB 99%",
                           "Adaptive Sync": "G-Sync Compatible", "Ports": "DP, HDMI"}, **std_hw},
     "warranty": "3 Year LG Warranty."},
    {"id": 21, "name": "LG 27GS75Q UltraGear Monitor", "category": "AI Monitors", "brand": "LG", "price": 25000,
     "moq": "1 pc", "shortDescription": "High refresh QHD gaming monitor with G-Sync compatibility.",
     "description": "Experience incredible detail with the LG 27GS75Q. This QHD IPS monitor boasts a 180Hz refresh rate.",
     "additionalInfo": {**{"Panel Type": "27-inch IPS", "Resolution": "QHD (2560x1440)", "Refresh Rate": "180Hz",
                           "Response Time": "1ms (GtG)", "Brightness": "300 nits", "HDR": "HDR10",
                           "Ergonomics": "Tilt/Height/Swivel", "Color Gamut": "sRGB 99%"}, **std_hw},
     "warranty": "3 Year LG Warranty."},
    {"id": 22, "name": "LG 27GS85Q UltraGear Monitor", "category": "AI Monitors", "brand": "LG", "price": 35000,
     "badge": "Premium", "moq": "1 pc",
     "shortDescription": "Professional gaming panel featuring Nano IPS and 98% DCI-P3 color gamut.",
     "description": "The LG 27GS85Q utilizes LG's acclaimed Nano IPS technology for breathtaking color reproduction.",
     "additionalInfo": {
         **{"Panel Type": "27-inch Nano IPS", "Resolution": "QHD (2560x1440)", "Refresh Rate": "180Hz (O/C 200Hz)",
            "Response Time": "1ms (GtG)", "Color Gamut": "DCI-P3 98%", "DisplayHDR": "HDR 400",
            "Ports": "DP 1.4, HDMI 2.1", "Ergonomics": "Height/Pivot/Tilt"}, **std_hw},
     "warranty": "3 Year LG Warranty."},
    {"id": 23, "name": "LG 27GS60QC UltraGear Curved Monitor", "category": "AI Monitors", "brand": "LG",
     "price": 22000, "moq": "1 pc", "shortDescription": "Curved QHD gaming monitor with 180Hz refresh rate.",
     "description": "Immerse yourself in your favorite titles with the LG 27GS60QC. This VA curved panel offers deep contrast.",
     "additionalInfo": {
         **{"Panel Type": "27-inch VA Curved (1000R)", "Resolution": "QHD (2560x1440)", "Refresh Rate": "180Hz",
            "Response Time": "1ms (MBR)", "Contrast Ratio": "3000:1", "HDR": "HDR10",
            "Adaptive Sync": "FreeSync Premium", "Ports": "DP 1.4, HDMI 2.0"}, **std_hw},
     "warranty": "3 Year LG Warranty."},
    {"id": 24, "name": "LG 27GR93U UltraGear 4K Monitor", "category": "AI Monitors", "brand": "LG", "price": 45000,
     "badge": "4K UHD", "moq": "1 pc", "shortDescription": "4K gaming monitor delivering 144Hz performance and HDR10.",
     "description": "Push your gaming PC to the limit with the LG 27GR93U. This 4K IPS display offers a blistering 144Hz refresh rate.",
     "additionalInfo": {**{"Panel Type": "27-inch IPS", "Resolution": "4K UHD (3840x2160)", "Refresh Rate": "144Hz",
                           "Response Time": "1ms (GtG)", "Color Gamut": "DCI-P3 95%", "DisplayHDR": "HDR 400",
                           "Connectivity": "HDMI 2.1, DP 1.4", "Adaptive Sync": "G-Sync Compatible"}, **std_hw},
     "warranty": "3 Year LG Warranty."},
    {"id": 25, "name": "LG 32GS60QC UltraGear Curved Monitor", "category": "AI Monitors", "brand": "LG", "price": 28000,
     "moq": "1 pc", "shortDescription": "Large 32-inch gaming-only curved monitor with 180Hz.",
     "description": "The 32-inch LG 32GS60QC brings massive screen real estate with an immersive curve.",
     "additionalInfo": {
         **{"Panel Type": "32-inch VA Curved (1000R)", "Resolution": "QHD (2560x1440)", "Refresh Rate": "180Hz",
            "Response Time": "1ms (MBR)", "Contrast Ratio": "3000:1", "Color Gamut": "sRGB 99%",
            "Adaptive Sync": "FreeSync", "Ports": "DP, HDMI"}, **std_hw}, "warranty": "3 Year LG Warranty."},
    {"id": 26, "name": "LG 32G600A UltraGear Monitor", "category": "AI Monitors", "brand": "LG", "price": 27000,
     "moq": "1 pc", "shortDescription": "32-inch VA Curved display with HDR and G-Sync compatibility.",
     "description": "The LG 32G600A is built for dedicated gamers. Featuring a 32-inch QHD VA curved screen.",
     "additionalInfo": {**{"Panel Type": "32-inch VA Curved", "Resolution": "QHD (2560x1440)", "Refresh Rate": "180Hz",
                           "Contrast Ratio": "2500:1", "HDR": "HDR10", "Viewing Angle": "178°/178°",
                           "Color Support": "16.7M", "Ports": "1x DP, 2x HDMI"}, **std_hw},
     "warranty": "3 Year LG Warranty."},
    {"id": 27, "name": "LG 32GS75Q UltraGear Monitor", "category": "AI Monitors", "brand": "LG", "price": 35000,
     "moq": "1 pc", "shortDescription": "Performance 32-inch gaming monitor with a versatile pivot stand.",
     "description": "Enjoy expansive QHD gameplay on the 32-inch LG 32GS75Q. This IPS monitor features a high-performance 180Hz refresh rate.",
     "additionalInfo": {**{"Panel Type": "32-inch IPS", "Resolution": "QHD (2560x1440)", "Refresh Rate": "180Hz",
                           "Response Time": "1ms (GtG)", "Color Gamut": "sRGB 99%", "HDR": "HDR10",
                           "Ergonomics": "Fully Adjustable Stand", "Ports": "DP 1.4, HDMI 2.0"}, **std_hw},
     "warranty": "3 Year LG Warranty."},
    {"id": 28, "name": "LG 32GS85Q UltraGear Monitor", "category": "AI Monitors", "brand": "LG", "price": 45000,
     "badge": "Pro", "moq": "1 pc",
     "shortDescription": "Large Nano IPS display for spectacular color accuracy and speed.",
     "description": "The LG 32GS85Q scales up Nano IPS technology to a 32-inch QHD canvas.", "additionalInfo": {
        **{"Panel Type": "32-inch Nano IPS", "Resolution": "QHD (2560x1440)", "Refresh Rate": "180Hz",
           "Response Time": "1ms (GtG)", "Color Gamut": "DCI-P3 98%", "DisplayHDR": "HDR400",
           "Connectivity": "HDMI 2.1, DP 1.4", "Audio": "Headphone Out"}, **std_hw}, "warranty": "3 Year LG Warranty."},
    {"id": 29, "name": "LG 27G850A-B UltraGear 4K Monitor", "category": "AI Monitors", "brand": "LG", "price": 70000,
     "badge": "Flagship", "moq": "1 pc", "shortDescription": "Premium 4K UHD gaming display with 240Hz dual mode.",
     "description": "The LG 27G850A-B is a premium, no-compromise gaming display. Featuring dual-mode capabilities.",
     "additionalInfo": {**{"Panel Type": "27-inch IPS (Dual Mode)", "Resolution": "4K (160Hz) / FHD (240Hz)",
                           "Response Time": "0.03ms", "Contrast Ratio": "1500000:1", "Color Gamut": "DCI-P3 98.5%",
                           "DisplayHDR": "True Black 400", "Connectivity": "HDMI 2.1, Type-C",
                           "Audio": "4-pole Headphone out"}, **std_hw}, "warranty": "3 Year LG Warranty."},
    {"id": 30, "name": "LG 34G600A UltraGear Ultrawide", "category": "AI Monitors", "brand": "LG", "price": 35000,
     "moq": "1 pc", "shortDescription": "Ultrawide UWQHD gaming monitor with an immersive 160Hz panel.",
     "description": "Expand your field of view with the LG 34G600A. This 34-inch VA curved ultrawide monitor brings UWQHD resolution to life.",
     "additionalInfo": {
         **{"Panel Type": "34-inch VA Curved Ultrawide", "Resolution": "UWQHD (3440x1440)", "Refresh Rate": "160Hz",
            "Aspect Ratio": "21:9", "Contrast Ratio": "3000:1", "HDR": "HDR10", "Response Time": "1ms (MBR)",
            "Ports": "DP 1.4, HDMI 2.0"}, **std_hw}, "warranty": "3 Year LG Warranty."},
    {"id": 31, "name": "LG 27SR50F Smart Monitor", "category": "AI Smart Monitors", "brand": "LG", "price": 20000,
     "moq": "1 pc", "shortDescription": "FHD IPS smart display powered by webOS with built-in streaming.",
     "description": "Work and play without a PC. The LG 27SR50F features built-in webOS for direct access to streaming apps.",
     "additionalInfo": {**{"Panel Type": "27-inch IPS", "Resolution": "FHD (1920x1080)", "Smart Platform": "webOS 23",
                           "Connectivity": "Wi-Fi, Bluetooth", "Screen Share": "AirPlay 2, Miracast",
                           "Audio": "Built-in 5W x 2", "Ergonomics": "Tilt Adjustable", "Ports": "2x HDMI, 2x USB"},
                        **std_hw}, "warranty": "3 Year LG Warranty."},
    {"id": 32, "name": "LG 32SR50F Smart Monitor", "category": "AI Smart Monitors", "brand": "LG", "price": 25000,
     "moq": "1 pc", "shortDescription": "32-inch Smart OS display equipped with Magic Remote.",
     "description": "The LG 32SR50F is a comprehensive smart monitor. Including the LG Magic Remote and ThinQ IoT hub compatibility.",
     "additionalInfo": {**{"Panel Type": "32-inch IPS", "Resolution": "FHD (1920x1080)", "Smart Platform": "webOS 23",
                           "Remote": "Magic Remote Included", "IoT": "ThinQ Home Hub", "Audio": "Built-in 5W x 2",
                           "Connectivity": "Wi-Fi / BT", "Ports": "2x HDMI, 2x USB"}, **std_hw},
     "warranty": "3 Year LG Warranty."},
    {"id": 33, "name": "LG 32SR75U 4K Smart Monitor", "category": "AI Smart Monitors", "brand": "LG", "price": 40000,
     "badge": "AI-Ready", "moq": "1 pc", "shortDescription": "4K UHD Smart display featuring USB-C 65W power delivery.",
     "description": "Streamline your workspace with the LG 32SR75U. This AI-Ready 4K Smart Monitor delivers stunning UHD visuals.",
     "additionalInfo": {
         **{"Panel Type": "32-inch IPS", "Resolution": "4K UHD (3840x2160)", "Smart Platform": "webOS 23",
            "Power Delivery": "USB Type-C (65W)", "Audio": "Built-in 5W x 2", "Screen Share": "AirPlay 2, Miracast",
            "Ergonomics": "Tilt / Height", "Ports": "USB-C, 2x HDMI"}, **std_hw}, "warranty": "3 Year LG Warranty."},
    {"id": 34, "name": "LG 43SQ700S 4K Smart Monitor", "category": "AI Smart Monitors", "brand": "LG", "price": 50000,
     "badge": "Massive", "moq": "1 pc", "shortDescription": "Massive 43-inch smart display ideal for AI workstations.",
     "description": "Dominate your workflow on the massive LG 43SQ700S. A 43-inch 4K UHD smart monitor complete with webOS.",
     "additionalInfo": {
         **{"Panel Type": "43-inch IPS", "Resolution": "4K UHD (3840x2160)", "Smart Platform": "webOS 22",
            "Power Delivery": "USB Type-C (65W)", "Audio": "Built-in 10W x 2", "IoT": "ThinQ", "Remote": "Magic Remote",
            "Dimensions": "967 x 647 x 274 mm"}, **std_hw}, "warranty": "3 Year LG Warranty."},
    {"id": 35, "name": "LG 34SR60QC Ultrawide Smart Monitor", "category": "AI Smart Monitors", "brand": "LG",
     "price": 45000, "moq": "1 pc", "shortDescription": "34-inch WQHD Curved smart display for ultimate productivity.",
     "description": "The LG 34SR60QC merges the benefits of an ultrawide workspace with webOS smart capabilities.",
     "additionalInfo": {
         **{"Panel Type": "34-inch VA Curved", "Resolution": "WQHD (3440x1440)", "Smart Platform": "webOS 23",
            "Aspect Ratio": "21:9", "Network": "Wi-Fi & BT", "Audio": "5W x 2 Speakers",
            "Productivity": "PiP / PbP Support", "Ports": "2x HDMI"}, **std_hw}, "warranty": "3 Year LG Warranty."},
    {"id": 36, "name": "LG 34SR65QC Ultrawide Smart Monitor", "category": "AI Smart Monitors", "brand": "LG",
     "price": 48000, "moq": "1 pc", "shortDescription": "Curved Ultrawide with built-in smart OS and screen sharing.",
     "description": "Enhance your desk with the LG 34SR65QC. This 34-inch WQHD curved smart monitor provides easy screen sharing.",
     "additionalInfo": {
         **{"Panel Type": "34-inch VA Curved", "Resolution": "WQHD (3440x1440)", "Smart Platform": "webOS 23",
            "Stand": "Height & Tilt Adjustable", "Screen Share": "AirPlay 2, Miracast", "Network": "Dual-band Wi-Fi",
            "Audio": "Built-in Speakers", "Ports": "HDMI, USB"}, **std_hw}, "warranty": "3 Year LG Warranty."},
    {"id": 37, "name": "Samsung HG43U701 Hospitality Smart TV", "category": "AI Commercial Displays",
     "brand": "Samsung", "price": 20500, "moq": "5 pcs",
     "shortDescription": "43-inch 4K UHD smart TV designed for hospitality.",
     "description": "The Samsung HG43U701 is a premium hospitality display delivering 4K UHD resolution.",
     "additionalInfo": {**{"Panel Size": "43-inch", "Resolution": "4K UHD (3840x2160)", "Brightness": "250 nits",
                           "Hospitality Platform": "LYNK Cloud / REACH 4.0", "Audio": "20W (10W + 10W)",
                           "VESA Mount": "200x200mm", "Ports": "3x HDMI, 1x USB, 1x RJ45", "Tuner": "DVB-T2/C"},
                        **std_hw}, "warranty": "3 Years Onsite Warranty."},
    {"id": 38, "name": "Samsung HG50U701 Hospitality Smart TV", "category": "AI Commercial Displays",
     "brand": "Samsung", "price": 29000, "moq": "5 pcs",
     "shortDescription": "50-inch 4K UHD hospitality smart TV for guest rooms.",
     "description": "Scale up your guest experience with the 50-inch Samsung HG50U701. Offering rich 4K UHD picture quality.",
     "additionalInfo": {**{"Panel Size": "50-inch", "Resolution": "4K UHD (3840x2160)", "HDR": "HDR10+",
                           "Hospitality Platform": "LYNK Cloud", "Pro:Idiom Support": "Yes", "VESA Mount": "200x200mm",
                           "Bezel Design": "3 Bezel-less", "Max Power": "125W"}, **std_hw},
     "warranty": "3 Years Onsite Warranty."},
    {"id": 39, "name": "Samsung HG55U701 Hospitality Smart TV", "category": "AI Commercial Displays",
     "brand": "Samsung", "price": 31000, "moq": "5 pcs",
     "shortDescription": "55-inch large-scale hospitality display with sharp 4K resolution.",
     "description": "The Samsung HG55U701 provides an impressive 55-inch 4K viewing experience.", "additionalInfo": {
        **{"Panel Size": "55-inch", "Resolution": "4K UHD (3840x2160)", "Processor": "Crystal Processor 4K",
           "Micro Dimming": "UHD Dimming", "Hospitality Platform": "LYNK REACH 4.0", "Connectivity": "Wi-Fi 5, BT 4.2",
           "Audio": "Dolby Digital Plus", "VESA": "200x200mm"}, **std_hw}, "warranty": "3 Years Onsite Warranty."},
    {"id": 40, "name": "Samsung HG65U701 Hospitality Smart TV", "category": "AI Commercial Displays",
     "brand": "Samsung", "price": 45000, "moq": "2 pcs",
     "shortDescription": "Expansive 65-inch 4K hospitality display for premium suites.",
     "description": "Deliver a flagship visual experience with the Samsung HG65U701. This massive 65-inch 4K hospitality TV is engineered for luxury hotel suites.",
     "additionalInfo": {**{"Panel Size": "65-inch", "Resolution": "4K UHD (3840x2160)", "Color": "PurColor",
                           "Hospitality Platform": "LYNK Cloud", "Sound Output": "20W", "Ports": "3x HDMI, 2x USB",
                           "VESA Mount": "400x300mm", "Remote": "Multi-code Remote"}, **std_hw},
     "warranty": "3 Years Onsite Warranty."},
    {"id": 41, "name": "Samsung BE43FH Business TV", "category": "AI Commercial Displays", "brand": "Samsung",
     "price": 21000, "moq": "2 pcs", "shortDescription": "43-inch AI-Ready commercial TV outputting 250 nits.",
     "description": "The Samsung BE43FH Business TV combines the visual quality of a Samsung TV with commercial-grade durability.",
     "additionalInfo": {**{"Panel Size": "43-inch", "Resolution": "4K UHD (3840x2160)", "Brightness": "250 nits",
                           "Operation Hours": "16/7 Rated", "App": "Samsung Business TV App",
                           "Connectivity": "Wi-Fi, RJ45", "Audio": "20W", "VESA Mount": "200x200mm"}, **std_hw},
     "warranty": "3 Years Onsite Warranty."},
    {"id": 42, "name": "Samsung BE55FH Business TV", "category": "AI Commercial Displays", "brand": "Samsung",
     "price": 34000, "moq": "2 pcs",
     "shortDescription": "55-inch commercial signage TV delivering 300 nits of brightness.",
     "description": "Ideal for impactful digital signage and corporate communications, the Samsung BE55FH is a 55-inch 4K Business TV.",
     "additionalInfo": {**{"Panel Size": "55-inch", "Resolution": "4K UHD (3840x2160)", "Brightness": "300 nits",
                           "Operation Hours": "16/7 Rated", "Management": "Samsung Business App", "OS": "Tizen",
                           "Connectivity": "Bluetooth, Wi-Fi", "VESA Mount": "200x200mm"}, **std_hw},
     "warranty": "3 Years Onsite Warranty."},
    {"id": 43, "name": "Samsung QB55CE Crystal UHD Signage", "category": "AI Commercial Displays", "brand": "Samsung",
     "price": 36000, "moq": "1 pc", "shortDescription": "55-inch digital signage display with Crystal UHD processor.",
     "description": "The Samsung QB55CE brings content to life with billions of shades of color via its Crystal UHD processor.",
     "additionalInfo": {
         **{"Panel Size": "55-inch", "Resolution": "4K UHD (3840x2160)", "Brightness": "350 nits", "Panel Tech": "VA",
            "Operation Hours": "16/7 Rated", "OS": "Tizen 7.0", "Storage": "8GB Internal",
            "Connectivity": "Wi-Fi, BT, HDMI"}, **std_hw}, "warranty": "3 Years Onsite Warranty."},
    {"id": 44, "name": "Samsung QM55C Professional Signage", "category": "AI Commercial Displays", "brand": "Samsung",
     "price": 43000, "badge": "24/7 Rating", "moq": "1 pc",
     "shortDescription": "Ultra-bright 500 nit professional signage display rated for 24/7 operation.",
     "description": "Built for non-stop performance, the Samsung QM55C Professional Signage offers 500 nits of brightness and a non-glare panel.",
     "additionalInfo": {**{"Panel Size": "55-inch", "Resolution": "4K UHD (3840x2160)", "Brightness": "500 nits",
                           "Glare Level": "Non-Glare (25% Haze)", "Operation Hours": "24/7 Rated",
                           "OS": "Tizen 7.0 (Smart Signage)", "Storage": "16GB Internal",
                           "Slim Design": "28.5mm Depth"}, **std_hw}, "warranty": "3 Years Onsite Warranty."},
    {"id": 45, "name": "Samsung QH98C UHD Signage", "category": "AI Commercial Displays", "brand": "Samsung",
     "price": 550000, "badge": "Massive 98\"", "moq": "1 pc",
     "shortDescription": "Gigantic 98-inch large format signage with an incredible 700 nits.",
     "description": "Command attention in any space with the Samsung QH98C. This colossal 98-inch UHD large format display outputs a brilliant 700 nits.",
     "additionalInfo": {**{"Panel Size": "98-inch", "Resolution": "4K UHD (3840x2160)", "Brightness": "700 nits",
                           "Panel Type": "IPS/VA High Contrast", "Operation Hours": "24/7 Rated",
                           "Glare Level": "Non-Glare", "SoC": "Quad Core (Tizen 7.0)",
                           "Interfaces": "DP 1.2, HDMI 2.0 (x3)"}, **std_hw}, "warranty": "3 Years Onsite Warranty."},
    {"id": 46, "name": "Samsung WA75C Interactive Flip Display", "category": "AI Interactive Displays",
     "brand": "Samsung", "price": 88000, "moq": "1 pc",
     "shortDescription": "75-inch 4K interactive whiteboard with advanced collaboration software.",
     "description": "Transform your boardroom with the Samsung WA75C Interactive Flip. Featuring highly responsive touch technology.",
     "additionalInfo": {**{"Panel Size": "75-inch", "Resolution": "4K UHD (3840x2160)", "Touch Tech": "IR (Infrared)",
                           "Multi-Touch": "Up to 40 Points", "OS": "Android 11", "Storage": "32GB ROM / 4GB RAM",
                           "Connectivity": "Wi-Fi, HDMI, USB-C", "Audio": "15W x 2"}, **std_hw},
     "warranty": "3 Years Onsite Warranty."},
    {"id": 47, "name": "Samsung WA65F Interactive Flip Display", "category": "AI Interactive Displays",
     "brand": "Samsung", "price": 72000, "moq": "1 pc",
     "shortDescription": "65-inch smart interactive display for education and huddle spaces.",
     "description": "The Samsung WA65F delivers intuitive touch and pen interaction on a sharp 65-inch 4K canvas.",
     "additionalInfo": {**{"Panel Size": "65-inch", "Resolution": "4K UHD (3840x2160)", "Touch Tech": "IR Touch",
                           "Multi-Touch": "40 Points", "OS": "Android-based custom UI",
                           "Screen Share": "Built-in casting", "Front Ports": "HDMI, USB-C, USB-A",
                           "Pen": "Passive Pen included"}, **std_hw}, "warranty": "3 Years Onsite Warranty."},
    {"id": 48, "name": "Samsung WA86F Interactive Flip Display", "category": "AI Interactive Displays",
     "brand": "Samsung", "price": 175000, "badge": "Enterprise", "moq": "1 pc",
     "shortDescription": "Flagship 86-inch enterprise interactive display for ultimate collaboration.",
     "description": "The massive 86-inch Samsung WA86F Interactive Flip is built for the most demanding enterprise environments.",
     "additionalInfo": {**{"Panel Size": "86-inch", "Resolution": "4K UHD (3840x2160)", "Touch Tech": "IR 40-point",
                           "Brightness": "400 nits", "OS": "Android 11 OS", "Storage": "64GB ROM / 8GB RAM",
                           "Audio": "15W x 2 Front Firing", "Glass": "Anti-glare, Tempered"}, **std_hw},
     "warranty": "3 Years Onsite Warranty."},
    {"id": 49, "name": "RealWear HMT-1 AR Smart Glasses", "category": "AI AR/VR Wearables", "brand": "RealWear",
     "price": 150000, "moq": "1 pc", "shortDescription": "Voice-controlled rugged wearable for remote assistance.",
     "description": "The RealWear HMT-1 is a true AI/AR wearable designed for the connected worker. Completely hands-free and voice-controlled.",
     "additionalInfo": {**{"Display": "20° FOV, 24-bit color LCD (WVGA)", "Processor": "2.0 GHz 8-core Snapdragon 625",
                           "Memory": "3GB RAM / 32GB Flash", "Battery": "3250 mAh Li-Ion", "OS": "Android 10",
                           "Ruggedness": "IP66, MIL-STD-810G", "Audio": "4 mics, 91dB speaker", "Weight": "380g"},
                        **std_hw}, "warranty": "1 Year Enterprise Warranty."},
    {"id": 50, "name": "RealWear HMT-1Z1 Intrinsically Safe", "category": "AI AR/VR Wearables", "brand": "RealWear",
     "price": 200000, "badge": "ATEX Zone 1", "moq": "1 pc",
     "shortDescription": "ATEX Zone 1 certified hands-free wearable for hazardous environments.",
     "description": "Designed specifically for oil, gas, and chemical industries, the RealWear HMT-1Z1 is intrinsically safe.",
     "additionalInfo": {
         **{"Certifications": "ATEX Zone 1, IECEx Zone 1", "Display": "WVGA LCD", "Processor": "Snapdragon 625",
            "Memory": "3GB RAM / 32GB Flash", "Battery": "3400 mAh (Non-removable)", "OS": "Android 10",
            "Ruggedness": "IP66, MIL-STD-810G", "Weight": "430g"}, **std_hw},
     "warranty": "1 Year Enterprise Warranty."},
    {"id": 51, "name": "RealWear Navigator 500", "category": "AI AR/VR Wearables", "brand": "RealWear", "price": 180000,
     "moq": "1 pc", "shortDescription": "High-performance smart glasses for frontline collaboration.",
     "description": "The next generation of industrial wearables. The RealWear Navigator 500 features a modular design and upgraded camera.",
     "additionalInfo": {
         **{"Display": "20° FOV WVGA", "Processor": "Snapdragon 662 (8-core)", "Memory": "4GB RAM / 64GB Storage",
            "Camera": "48 MP with OIS", "Battery": "2600 mAh (Hot-swappable)", "OS": "Android 11",
            "Ruggedness": "IP66, Drop Tested to 2m", "Weight": "272g"}, **std_hw},
     "warranty": "1 Year Enterprise Warranty."},
    {"id": 52, "name": "RealWear Navigator 520", "category": "AI AR/VR Wearables", "brand": "RealWear", "price": 220000,
     "badge": "Upgraded", "moq": "1 pc",
     "shortDescription": "Enhanced Navigator with larger display and thermal camera support.",
     "description": "The RealWear Navigator 520 improves upon the 500 with a significantly larger and sharper HyperDisplay.",
     "additionalInfo": {**{"Display": "HyperDisplay (0.35 inch HD, 24° FOV)", "Processor": "Snapdragon 662",
                           "Memory": "4GB RAM / 64GB Flash", "Camera": "48 MP with PDAF/OIS",
                           "Battery": "2600 mAh (Hot-Swappable)", "OS": "Android 11",
                           "Ruggedness": "IP66, MIL-STD-810H", "Weight": "274g"}, **std_hw},
     "warranty": "1 Year Enterprise Warranty."},
    {"id": 53, "name": "RealWear Navigator Z1", "category": "AI AR/VR Wearables", "brand": "RealWear", "price": 250000,
     "moq": "1 pc", "shortDescription": "Intelligent wearable for remote mentoring & advanced IoT workflows.",
     "description": "The RealWear Navigator Z1 pushes the boundaries of enterprise AR. Packing advanced processing power.",
     "additionalInfo": {
         **{"Display": "HyperDisplay HD (720p)", "Processor": "Snapdragon SD 6490", "Memory": "8GB RAM / 128GB Storage",
            "Camera": "48 MP / 1080p60 Video", "Certifications": "ATEX Zone 1, C1D1",
            "Battery": "Hot-swappable ATEX cert", "OS": "Android 12", "Connectivity": "Wi-Fi 6, 5G"}, **std_hw},
     "warranty": "1 Year Enterprise Warranty."},
    {"id": 54, "name": "RealWear Arc 3", "category": "AI AR/VR Wearables", "brand": "RealWear", "price": 280000,
     "badge": "Next-Gen", "moq": "1 pc",
     "shortDescription": "Next-Gen see-through display AR glasses for industrial use.",
     "description": "The RealWear Arc 3 represents the future of spatial computing. Featuring a state-of-the-art see-through optical display.",
     "additionalInfo": {**{"Display Type": "See-Through Binocular Waveguide", "Processor": "Snapdragon XR2 Gen 1",
                           "Field of View": "40° Diagonal", "Weight": "Under 250g", "Battery": "Dual hot-swappable",
                           "Camera": "Dual 1080p Tracking, 12MP RGB", "OS": "RealWear OS (Android)",
                           "Sensors": "IMU, ToF"}, **std_hw}, "warranty": "1 Year Enterprise Warranty."},
    {"id": 55, "name": "RealWear Thermal Camera Module", "category": "AI Accessories", "brand": "RealWear",
     "price": 50000, "moq": "1 pc", "shortDescription": "Thermal vision add-on module for Navigator 500 series.",
     "description": "Transform your RealWear Navigator into a powerful predictive maintenance tool.",
     "additionalInfo": {**{"Sensor": "FLIR Lepton 3.5", "Resolution": "160 x 120 Thermal", "Frame Rate": "9 Hz",
                           "Compatibility": "Navigator 500 & 520", "Scene Range": "-20°C to 400°C",
                           "Visual Overlay": "MSX Technology", "Dimensions": "42 x 35 x 20mm", "Weight": "35g"},
                        **std_hw}, "warranty": "1 Year Enterprise Warranty."},
    {"id": 56, "name": "RealWear Arc 3 Accessory Kit", "category": "AI Accessories", "brand": "RealWear",
     "price": 25000, "moq": "1 Kit", "shortDescription": "Essential battery, charger & wearable accessories for Arc 3.",
     "description": "Maximize uptime and comfort with the official Arc 3 Accessory Kit.", "additionalInfo": {
        **{"Includes": "2x 2600mAh Batteries, 1x 4-Bay Charger", "Fast Charging": "80% in 1 hour",
           "Compatibility": "Arc 3 Series", "Cable": "USB-C Heavy Duty", "Straps": "3-point adjustable",
           "Case": "Rugged EVA carrying case", "Warranty": "90 Days", "Platform": "Enterprise"}, **std_hw},
     "warranty": "90 Day Accessory Warranty."},
    {"id": 57, "name": "RealWear PPE Helmet Mount Kit", "category": "AI Accessories", "brand": "RealWear",
     "price": 5000, "moq": "5 Kits",
     "shortDescription": "Safety compliance helmet mounting hardware for RealWear devices.",
     "description": "Ensure safety compliance on the job site. This official PPE Helmet Mount Kit securely fastens your smart glasses.",
     "additionalInfo": {**{"Compatibility": "MSA, 3M, Bullard Hard Hats", "Mechanism": "Clip-on dual bracket",
                           "Material": "Industrial-grade polymer", "Adjustment": "3-Axis pivot",
                           "Safety": "Maintains ANSI Z89.1 rating", "Clips": "4x Helmet Clips included",
                           "Weight": "50g", "Warranty": "90 Days"}, **std_hw},
     "warranty": "90 Day Accessory Warranty."},
    {"id": 58, "name": "RealWear Enterprise Software Suite", "category": "Software", "brand": "RealWear",
     "price": 80000, "badge": "License", "moq": "1 License",
     "shortDescription": "Remote collaboration & workflow software including RealWear Collaborate.",
     "description": "Unlock the full potential of your fleet with the RealWear Enterprise Software Suite.",
     "additionalInfo": {**{"Features": "RealWear Collaborate, Device Management", "Deployment": "Cloud/SaaS",
                           "Support": "24/7 Priority Ticket Access", "Updates": "Over-the-air (OTA)",
                           "Security": "End-to-end encryption", "Integrations": "MS Teams, Zoom, Webex",
                           "License Term": "1 Year", "Platform": "Web/Android"}, **std_sw},
     "warranty": "Annual Subscription License."},
    {"id": 59, "name": "Hikvision DS-2CD1327G2H-LIU 2MP IP Dome", "category": "AI Vision & Security",
     "brand": "Hikvision", "price": 2700, "moq": "5 pcs",
     "shortDescription": "2MP Dome Camera with AcuSense AI Human/Vehicle Detection.",
     "description": "Enhance perimeter security with the Hikvision DS-2CD1327G2H-LIU. Featuring TRUE AI on-device classification.",
     "additionalInfo": {
         **{"Resolution": "2 MP (1920×1080)", "Lens": "2.8/4mm fixed", "IR Range": "Up to 30m", "Audio": "Built-in mic",
            "Compression": "H.265+", "Protection": "IP67", "AI Features": "Human & Vehicle Classification",
            "Frame Rate": "30fps"}, **std_hw}, "warranty": "1 Year Manufacturer Warranty."},
    {"id": 60, "name": "Hikvision DS-2CD1347G2H-LIU 4MP IP Dome", "category": "AI Vision & Security",
     "brand": "Hikvision", "price": 3950, "moq": "5 pcs",
     "shortDescription": "4MP Dome Camera featuring Smart Hybrid ColorVu.",
     "description": "Capture crisp 4MP detail day or night with the Hikvision DS-2CD1347G2H-LIU.", "additionalInfo": {
        **{"Resolution": "4 MP", "Illumination": "ColorVu (24/7 Color)", "Lens": "2.8mm",
           "Light Range": "Up to 30m White Light", "Audio": "Built-in mic", "Protection": "IP67",
           "Compression": "H.265+", "AI": "AcuSense"}, **std_hw}, "warranty": "1 Year Manufacturer Warranty."},
    {"id": 61, "name": "Hikvision DS-2CD1367G2H-LIU 6MP IP Dome", "category": "AI Vision & Security",
     "brand": "Hikvision", "price": 5150, "moq": "5 pcs",
     "shortDescription": "High-resolution 6MP AI Dome Camera for advanced analytics.",
     "description": "The Hikvision DS-2CD1367G2H-LIU is built for high-stakes environments. It combines an ultra-clear 6MP sensor with TRUE AI analytics.",
     "additionalInfo": {
         **{"Resolution": "6 MP", "Illumination": "Smart Hybrid Light", "Lens": "2.8/4mm", "IR Range": "Up to 40m",
            "WDR": "120 dB", "Protection": "IP67", "Compression": "H.265+", "AI": "Deep Learning Analytics"}, **std_hw},
     "warranty": "1 Year Manufacturer Warranty."},
    {"id": 62, "name": "Hikvision DS-2CD1027G2H-LIU 2MP IP Bullet", "category": "AI Vision & Security",
     "brand": "Hikvision", "price": 2750, "moq": "5 pcs",
     "shortDescription": "2MP AI Bullet Camera for outdoor perimeter classification.",
     "description": "Secure outdoor boundaries with the Hikvision DS-2CD1027G2H-LIU. This weather-resistant 2MP bullet camera leverages AcuSense AI.",
     "additionalInfo": {
         **{"Form Factor": "Bullet", "Resolution": "2 MP", "Lens": "2.8mm", "IR Range": "30m", "Audio": "Supported",
            "WDR": "Digital WDR", "Environment": "IP67 Weatherproof", "Power": "PoE / 12V DC"}, **std_hw},
     "warranty": "1 Year Manufacturer Warranty."},
    {"id": 63, "name": "Hikvision DS-2CD1047G2H-LIU 4MP IP Bullet", "category": "AI Vision & Security",
     "brand": "Hikvision", "price": 4000, "moq": "5 pcs", "shortDescription": "4MP Smart AI night color Bullet Camera.",
     "description": "The Hikvision DS-2CD1047G2H-LIU ensures nothing goes unseen in the dark. Utilizing Smart Hybrid ColorVu and AcuSense.",
     "additionalInfo": {**{"Form Factor": "Bullet", "Resolution": "4 MP", "Night Vision": "ColorVu", "Lens": "4mm",
                           "WDR": "120 dB True WDR", "Audio": "Built-in Mic", "Protection": "IP67",
                           "AI": "Human/Vehicle Detection"}, **std_hw}, "warranty": "1 Year Manufacturer Warranty."},
    {"id": 64, "name": "Hikvision DS-2CD1067G2H-LIU 6MP IP Bullet", "category": "AI Vision & Security",
     "brand": "Hikvision", "price": 5200, "badge": "Advanced AI", "moq": "5 pcs",
     "shortDescription": "Top-tier 6MP Bullet Camera with advanced AI analytics.",
     "description": "Deploy maximum surveillance capabilities with the 6MP Hikvision DS-2CD1067G2H-LIU.",
     "additionalInfo": {
         **{"Form Factor": "Bullet", "Resolution": "6 MP", "Lens": "2.8mm/4mm", "IR Range": "40m", "WDR": "120 dB",
            "Protection": "IP67", "Power": "802.3af PoE", "AI Analytics": "Intrusion/Line Crossing"}, **std_hw},
     "warranty": "1 Year Manufacturer Warranty."},
    {"id": 65, "name": "Hikvision DS-2DE4225IW-DE 2MP IP PTZ", "category": "AI Vision & Security", "brand": "Hikvision",
     "price": 25200, "moq": "1 pc", "shortDescription": "2MP PTZ Camera equipped with AI-based Smart Tracking.",
     "description": "Take active control of your security with the Hikvision DS-2DE4225IW-DE. This Pan-Tilt-Zoom camera uses built-in TRUE AI.",
     "additionalInfo": {
         **{"Form Factor": "PTZ", "Resolution": "2 MP", "Zoom": "25x Optical / 16x Digital", "IR Range": "Up to 100m",
            "Pan/Tilt": "360° Endless / -15° to 90°", "WDR": "120 dB", "Protection": "IP66", "AI": "Smart Tracking"},
         **std_hw}, "warranty": "1 Year Manufacturer Warranty."},
    {"id": 66, "name": "Hikvision DS-2DE4425IW-DE 4MP IP PTZ", "category": "AI Vision & Security", "brand": "Hikvision",
     "price": 31000, "badge": "Enterprise", "moq": "1 pc",
     "shortDescription": "Enterprise 4MP PTZ Camera with advanced AI tracking algorithms.",
     "description": "The Hikvision DS-2DE4425IW-DE is an enterprise-grade 4MP PTZ solution. It delivers exceptional optical zoom capabilities.",
     "additionalInfo": {**{"Form Factor": "PTZ", "Resolution": "4 MP", "Zoom": "25x Optical", "IR Range": "Up to 100m",
                           "Compression": "H.265+", "WDR": "120 dB", "Audio I/O": "1/1", "Protection": "IP66"},
                        **std_hw}, "warranty": "1 Year Manufacturer Warranty."},
    {"id": 67, "name": "Hikvision DS-7604NXI-K1 4-Channel AI NVR", "category": "AI Networking & Storage",
     "brand": "Hikvision", "price": 6350, "moq": "1 pc",
     "shortDescription": "4-Channel NVR providing edge AI analytics for standard cameras.",
     "description": "Upgrade your existing camera fleet with the Hikvision DS-7604NXI-K1. This AcuSense NVR applies powerful TRUE AI human detection.",
     "additionalInfo": {**{"Channels": "4 IP Cameras", "Decoding": "Up to 1ch @ 12MP", "Storage": "1 SATA (up to 10TB)",
                           "Bandwidth": "40 Mbps Incoming", "AI": "Motion Detection 2.0", "Compression": "H.265+",
                           "Networking": "1x RJ45 100M", "Video Output": "HDMI/VGA"}, **std_hw},
     "warranty": "1 Year Manufacturer Warranty."},
    {"id": 68, "name": "Hikvision DS-7608NXI-K1 8-Channel AI NVR", "category": "AI Networking & Storage",
     "brand": "Hikvision", "price": 6950, "moq": "1 pc", "shortDescription": "8-Channel centralized AI processing NVR.",
     "description": "The Hikvision DS-7608NXI-K1 efficiently manages up to 8 IP cameras. It dramatically reduces false alarms and enables instant Smart Search.",
     "additionalInfo": {**{"Channels": "8 IP Cameras", "Decoding": "Up to 2ch @ 12MP", "Storage": "1 SATA (up to 10TB)",
                           "Bandwidth": "80 Mbps Incoming", "AI": "Facial Recognition / Motion 2.0",
                           "Compression": "H.265+", "Audio": "1-ch Two-way", "Power": "12V DC"}, **std_hw},
     "warranty": "1 Year Manufacturer Warranty."},
    {"id": 69, "name": "Hikvision DS-7616NXI-K1 16-Channel AI NVR", "category": "AI Networking & Storage",
     "brand": "Hikvision", "price": 8350, "badge": "Pro NVR", "moq": "1 pc",
     "shortDescription": "Enterprise-grade 16-Channel AI NVR for large deployments.",
     "description": "Designed for expanding businesses, the Hikvision DS-7616NXI-K1 handles 16 channels of continuous high-definition recording.",
     "additionalInfo": {
         **{"Channels": "16 IP Cameras", "Decoding": "Up to 2ch @ 12MP", "Storage": "1 SATA (up to 10TB)",
            "Bandwidth": "160 Mbps Incoming", "AI Capabilities": "AcuSense on all channels", "Video Out": "4K HDMI",
            "Network": "Gigabit RJ45", "Power": "12V DC"}, **std_hw}, "warranty": "1 Year Manufacturer Warranty."},
    {"id": 70, "name": "EZVIZ C6N (2MP) Indoor PT 360", "category": "AI Vision & Security", "brand": "EZVIZ",
     "price": 1420, "moq": "10 pcs", "shortDescription": "Supports AI-based tracking & detection in 1080p.",
     "description": "Keep a watchful eye on your home or office with the EZVIZ C6N. This 2MP pan-tilt camera features TRUE AI human detection.",
     "additionalInfo": {
         **{"Resolution": "1080p (2 MP)", "Field of View": "360° Pan / 55° Tilt", "Night Vision": "IR up to 10m",
            "Audio": "Two-way talk", "Storage": "MicroSD (256GB max)", "Connectivity": "2.4 GHz Wi-Fi",
            "AI": "Smart Tracking", "Dimensions": "88 × 88 × 119 mm"}, **std_hw}, "warranty": "1 Year EZVIZ Warranty."},
    {"id": 71, "name": "EZVIZ C6N (4MP) Indoor PT 360", "category": "AI Vision & Security", "brand": "EZVIZ",
     "price": 2675, "moq": "10 pcs", "shortDescription": "Higher resolution 4MP AI indoor camera.",
     "description": "The EZVIZ C6N (4MP) doubles the clarity of its predecessor. Enjoy 2K+ resolution alongside smart 360-degree panning.",
     "additionalInfo": {
         **{"Resolution": "2K (4 MP)", "Field of View": "360° Pan / 55° Tilt", "Night Vision": "IR up to 10m",
            "Audio": "Two-way talk", "Storage": "MicroSD (256GB max)", "Connectivity": "2.4/5 GHz Dual Wi-Fi",
            "AI": "Human Detection", "Compression": "H.265"}, **std_hw}, "warranty": "1 Year EZVIZ Warranty."},
    {"id": 72, "name": "EZVIZ TY1 (2MP) Indoor PT 360", "category": "AI Vision & Security", "brand": "EZVIZ",
     "price": 1420, "badge": "Budget", "moq": "10 pcs",
     "shortDescription": "Popular and affordable AI-powered PT camera.",
     "description": "The EZVIZ TY1 (2MP) is an affordable, feature-packed indoor security camera. It utilizes TRUE AI to actively detect movement.",
     "additionalInfo": {**{"Resolution": "1080p", "PTZ": "360° Horizontal Coverage", "Night Vision": "IR 10m",
                           "Sleep Mode": "Privacy Shutter", "Audio": "Two-way Talk", "Storage": "MicroSD (256GB)",
                           "Wi-Fi": "2.4 GHz", "AI Features": "Motion Auto-Tracking"}, **std_hw},
     "warranty": "1 Year EZVIZ Warranty."},
    {"id": 73, "name": "EZVIZ TY1 (4MP) Indoor PT 360", "category": "AI Vision & Security", "brand": "EZVIZ",
     "price": 2675, "moq": "10 pcs", "shortDescription": "Enhanced 4MP AI detection with 360-degree coverage.",
     "description": "Upgrade your indoor coverage with the EZVIZ TY1 (4MP). Combining a razor-sharp 2K+ lens with onboard TRUE AI human detection.",
     "additionalInfo": {
         **{"Resolution": "2K+ (4 MP)", "PTZ": "360° Coverage", "Night Vision": "Smart IR 10m", "Audio": "Two-way Talk",
            "Compression": "H.265", "Storage": "MicroSD up to 256GB", "Wi-Fi": "2.4GHz",
            "AI Features": "Human Shape Detection"}, **std_hw}, "warranty": "1 Year EZVIZ Warranty."},
    {"id": 74, "name": "EZVIZ H6C Pro (2MP) Indoor PT", "category": "AI Vision & Security", "brand": "EZVIZ",
     "price": 1525, "moq": "10 pcs", "shortDescription": "2MP indoor camera with advanced AI motion filtering.",
     "description": "The EZVIZ H6C Pro intelligently filters out irrelevant movement, like pets or shadows. Focusing strictly on AI human detection.",
     "additionalInfo": {
         **{"Resolution": "1080p", "Lens": "4mm @ F2.4", "PTZ": "340° Pan / 55° Tilt", "Night Vision": "10m IR",
            "Audio": "Two-Way", "Storage": "MicroSD (512GB max)", "AI": "AI-Powered Human Shape Detection",
            "Connectivity": "2.4GHz Wi-Fi / RJ45"}, **std_hw}, "warranty": "1 Year EZVIZ Warranty."},
    {"id": 75, "name": "EZVIZ H6C Pro (4MP) Indoor PT", "category": "AI Vision & Security", "brand": "EZVIZ",
     "price": 2730, "moq": "10 pcs", "shortDescription": "Advanced AI indoor monitoring with 4MP clarity.",
     "description": "Experience premium indoor surveillance with the EZVIZ H6C Pro (4MP). Boasting superior lens quality and TRUE AI.",
     "additionalInfo": {**{"Resolution": "4 MP (2K+)", "Lens": "4mm @ F2.0", "PTZ": "340° Pan / 55° Tilt",
                           "Night Vision": "Color Night Vision", "Audio": "Two-Way Talk",
                           "Storage": "MicroSD up to 512GB", "AI Features": "Auto-Tracking & Human Detection",
                           "App Support": "EZVIZ App"}, **std_hw}, "warranty": "1 Year EZVIZ Warranty."},
    {"id": 76, "name": "EZVIZ H7C Dual Lens Indoor", "category": "AI Vision & Security", "brand": "EZVIZ",
     "price": 3150, "badge": "Dual Lens", "moq": "5 pcs",
     "shortDescription": "Innovative 4MP + 4MP dual lens AI indoor camera.",
     "description": "The EZVIZ H7C redefines indoor monitoring. Equipped with two 4MP lenses, it simultaneously captures wide-angle overviews.",
     "additionalInfo": {**{"Resolutions": "4MP + 4MP (8MP Total)", "Lenses": "Fixed + PTZ Lens",
                           "Night Vision": "Color Night Vision up to 10m",
                           "AI Features": "Co-detection & Auto-Tracking", "Audio": "High-Quality Two-Way",
                           "Storage": "MicroSD (512GB)", "Connectivity": "Wi-Fi 6", "Interface": "USB-C"}, **std_hw},
     "warranty": "1 Year EZVIZ Warranty."},
    {"id": 77, "name": "Prama PT-DRAS1A16Q-K1 16-ch AI DVR", "category": "AI Networking & Storage", "brand": "Prama",
     "price": 6350, "moq": "1 pc", "shortDescription": "1080P/4MP AI H.265Pro+ DVR with built-in analytics.",
     "description": "Breathe new life into analog coaxial systems with the Prama PT-DRAS1A16Q-K1. This AI DVR processes video feeds internally.",
     "additionalInfo": {
         **{"Channels": "16-ch Analog / Up to 24-ch IP", "Resolution": "Up to 4MP Lite", "Compression": "H.265 Pro+",
            "Storage": "1 SATA (up to 10TB)", "Audio": "1-ch RCA / 16-ch Coax", "AI": "Human/Vehicle Analysis",
            "Network": "1x 100M RJ45", "Power": "12V DC"}, **std_hw}, "warranty": "1 Year Manufacturer Warranty."},
    {"id": 78, "name": "Prama PT-DRAS2A16U-K2 16-ch AI DVR", "category": "AI Networking & Storage", "brand": "Prama",
     "price": 11616, "badge": "5MP DVR", "moq": "1 pc",
     "shortDescription": "High-channel 5MP AI DVR with advanced analytics.",
     "description": "The Prama PT-DRAS2A16U-K2 delivers high-resolution 5MP recording over coaxial lines with an advanced AI engine.",
     "additionalInfo": {
         **{"Channels": "16-ch Analog / Up to 32-ch IP", "Resolution": "Up to 8MP (4K)", "Compression": "H.265 Pro+",
            "Storage": "2 SATA (up to 10TB each)", "Audio": "4-ch RCA", "AI": "Deep learning motion detection",
            "Network": "Gigabit Ethernet", "Power": "12V DC"}, **std_hw}, "warranty": "1 Year Manufacturer Warranty."},
    {"id": 79, "name": "Prama PT-NRAS2A08-K2 8-ch AI NVR", "category": "AI Networking & Storage", "brand": "Prama",
     "price": 5900, "moq": "1 pc", "shortDescription": "8-channel 2HDD H.265+ Aisense NVR for edge AI processing.",
     "description": "Secure your network with the Prama PT-NRAS2A08-K2 Aisense NVR. Accommodating 2 HDDs for extended storage.",
     "additionalInfo": {**{"Channels": "8-ch IP", "Bandwidth": "80 Mbps In/Out", "Decoding": "8-ch @ 1080p",
                           "Storage": "2 SATA (up to 8TB each)", "Compression": "H.265+",
                           "Output": "HDMI/VGA independent", "AI": "Aisense perimeter protection",
                           "Network": "1x RJ45 Gigabit"}, **std_hw}, "warranty": "1 Year Manufacturer Warranty."},
    {"id": 80, "name": "Prama PT-NRAS2A16-K2 16-ch AI NVR", "category": "AI Networking & Storage", "brand": "Prama",
     "price": 6790, "moq": "1 pc", "shortDescription": "Enterprise 16-channel AI NVR for dedicated classification.",
     "description": "The Prama PT-NRAS2A16-K2 efficiently handles up to 16 IP cameras. Empowered by Aisense technology.",
     "additionalInfo": {
         **{"Channels": "16-ch IP", "Bandwidth": "160 Mbps Incoming", "Decoding": "2-ch @ 8MP / 16-ch @ 1080p",
            "Storage": "2 SATA (up to 8TB each)", "Video Out": "4K HDMI",
            "AI Capabilities": "Face Recognition & Perimeter", "Interface": "2x USB 2.0", "Network": "Gigabit RJ45"},
         **std_hw}, "warranty": "1 Year Manufacturer Warranty."},
    {"id": 81, "name": "Prama PT-NRAS2A32-K2 32-ch AI NVR", "category": "AI Networking & Storage", "brand": "Prama",
     "price": 9400, "moq": "1 pc", "shortDescription": "Large-scale 32-channel AI deployment NVR.",
     "description": "Scale your security operations massively with the Prama PT-NRAS2A32-K2. This 32-channel Aisense NVR processes vast video data.",
     "additionalInfo": {
         **{"Channels": "32-ch IP", "Bandwidth": "256 Mbps Incoming", "Decoding": "4-ch @ 8MP / 16-ch @ 1080p",
            "Storage": "2 SATA (up to 8TB each)", "Video Out": "4K HDMI", "AI": "Smart Search & Playback",
            "Interface": "1x USB 3.0 / 1x USB 2.0", "Form Factor": "1U Rackmount"}, **std_hw},
     "warranty": "1 Year Manufacturer Warranty."},
    {"id": 82, "name": "Prama PT-NRAS2B16-K4 16-ch AI NVR", "category": "AI Networking & Storage", "brand": "Prama",
     "price": 13700, "badge": "High Storage", "moq": "1 pc",
     "shortDescription": "16-channel NVR with 4HDD bays and advanced AI analytics.",
     "description": "Never run out of space. The Prama PT-NRAS2B16-K4 features 4 HDD bays for massive data retention.",
     "additionalInfo": {
         **{"Channels": "16-ch IP", "Bandwidth": "160 Mbps Incoming", "Storage": "4 SATA (up to 10TB each)",
            "Decoding": "Up to 4-ch @ 8MP", "Output": "2x HDMI (up to 4K)", "AI": "Aisense Deep Learning",
            "Network": "2x Gigabit RJ45", "Form Factor": "1.5U Rackmount"}, **std_hw},
     "warranty": "1 Year Manufacturer Warranty."},
    {"id": 83, "name": "Prama PT-NRAS2B32-K4 32-ch AI NVR", "category": "AI Networking & Storage", "brand": "Prama",
     "price": 16900, "badge": "Enterprise", "moq": "1 pc",
     "shortDescription": "Large enterprise 32-channel AI NVR with 4HDD capacity.",
     "description": "The ultimate Prama recording solution. The PT-NRAS2B32-K4 manages 32 concurrent IP video streams.",
     "additionalInfo": {
         **{"Channels": "32-ch IP", "Bandwidth": "256 Mbps Incoming", "Storage": "4 SATA (up to 10TB each)",
            "Decoding": "Up to 8-ch @ 8MP", "Interfaces": "1x eSATA, 1x RS-485", "AI": "Advanced perimeter protection",
            "Network": "2x Gigabit RJ45", "Power Supply": "100-240V AC"}, **std_hw},
     "warranty": "1 Year Manufacturer Warranty."},
    {"id": 84, "name": "Prama PT-NPZE4225IW-DP 2MP AI PTZ", "category": "AI Vision & Security", "brand": "Prama",
     "price": 20900, "moq": "1 pc", "shortDescription": "2MP 25X IP PTZ Camera with AI-based auto tracking.",
     "description": "Monitor vast outdoor areas easily. The Prama PT-NPZE4225IW-DP features a powerful 25X optical zoom.",
     "additionalInfo": {
         **{"Resolution": "2 MP (1920×1080)", "Zoom": "25x Optical, 16x Digital", "Night Vision": "100m IR",
            "WDR": "120 dB True WDR", "Protection": "IP66", "Surge Protection": "4000V",
            "AI": "Face Capture / Auto Tracking", "Compression": "H.265+"}, **std_hw},
     "warranty": "1 Year Manufacturer Warranty."},
    {"id": 85, "name": "Prama PT-NPZE4425IW-DP 4MP AI PTZ", "category": "AI Vision & Security", "brand": "Prama",
     "price": 25700, "moq": "1 pc", "shortDescription": "High resolution 4MP AI PTZ with 25X zoom.",
     "description": "The Prama PT-NPZE4425IW-DP captures exceptional 4MP detail at extreme distances. Engineered with robust TRUE AI smart tracking.",
     "additionalInfo": {
         **{"Resolution": "4 MP (2560×1440)", "Zoom": "25x Optical", "Night Vision": "100m IR", "WDR": "120 dB",
            "Protection": "IP66 Weatherproof", "Power": "Hi-PoE / 12V DC", "AI": "Target Classification",
            "Operating Temp": "-30°C to 65°C"}, **std_hw}, "warranty": "1 Year Manufacturer Warranty."},
    {"id": 86, "name": "Runway ML", "category": "AI Software", "brand": "Runway", "price": 2500, "badge": "Video Gen",
     "moq": "1 License", "shortDescription": "Advanced generative AI video creation platform.",
     "description": "Runway ML empowers creators with next-generation AI video tools. Generate stunning video sequences from text prompts.",
     "additionalInfo": {
         **{"Architecture": "Gen-2 Model", "Formats": "MP4, MOV, ProRes", "Resolution Support": "Up to 4K",
            "Cloud Storage": "500GB included", "API Access": "REST API available",
            "Max Video Length": "Up to 16s per generation", "Collaboration": "Team Workspace",
            "Integrations": "Premiere Pro"}, **std_sw}, "warranty": "Monthly/Annual Subscription."},
    {"id": 87, "name": "Pictory", "category": "AI Software", "brand": "Pictory", "price": 1500, "moq": "1 License",
     "shortDescription": "AI video generation from long-form text and scripts.",
     "description": "Pictory automatically creates high-conversion video sales letters and social media snippets from your long-form text.",
     "additionalInfo": {**{"Core AI": "OpenAI GPT-4 / ElevenLabs", "Supported Inputs": "Text, URL, Audio, Video",
                           "Max Video Length": "60 minutes", "Export Resolution": "1080p / 4K",
                           "Stock Library": "3M+ Getty Images", "Voiceovers": "50+ AI Voices",
                           "Branding": "Custom Intros/Outros", "Subtitles": "Auto-sync 50+ languages"}, **std_sw},
     "warranty": "Monthly/Annual Subscription."},
    {"id": 88, "name": "Fliki", "category": "AI Software", "brand": "Fliki", "price": 1200, "moq": "1 License",
     "shortDescription": "Create videos from text with incredibly realistic AI voices.",
     "description": "Fliki transforms your blog posts or scripts into engaging videos with hyper-realistic text-to-speech voices.",
     "additionalInfo": {**{"Voices": "2000+ AI Voices in 75+ languages", "Video Engine": "DALL-E 3 & Stable Diffusion",
                           "Export": "MP4 (1080p)", "Audio Export": "MP3, WAV",
                           "Max Script Length": "30,000 characters", "API Access": "Yes",
                           "Integrations": "WordPress, Twitter", "Clone Voice": "Premium Tier only"}, **std_sw},
     "warranty": "Monthly/Annual Subscription."},
    {"id": 89, "name": "Adobe Firefly", "category": "AI Software", "brand": "Adobe", "price": 2500,
     "badge": "Image Gen", "moq": "1 License",
     "shortDescription": "Generative AI for creative professionals integrated with Adobe.",
     "description": "Adobe Firefly is a powerful generative AI engine built into the Adobe ecosystem. Safely generate high-quality images.",
     "additionalInfo": {**{"Model": "Firefly Image 3 Model", "Integration": "Photoshop, Illustrator",
                           "Output Resolution": "Up to 2000x2000px", "Copyright": "Commercially Safe",
                           "Languages": "100+ prompt languages", "Features": "Text to Image, Generative Fill",
                           "Format": "JPEG, PNG, SVG", "Cloud": "Adobe CC Sync"}, **std_sw},
     "warranty": "Monthly/Annual Subscription."},
    {"id": 90, "name": "MidJourney", "category": "AI Software", "brand": "MidJourney", "price": 2500,
     "moq": "1 License", "shortDescription": "Industry-leading AI image generation through Discord.",
     "description": "MidJourney creates breathtaking, award-winning images from natural language descriptions.",
     "additionalInfo": {
         **{"Model Version": "V6 Alpha", "Interface": "Discord / Web Alpha", "Max Resolution": "2048x2048px (upscaled)",
            "Aspect Ratios": "Custom (--ar parameter)", "Speed": "Fast GPU hours included", "Output": "PNG",
            "Job Modes": "Relax, Fast, Turbo", "Licensing": "Full commercial terms"}, **std_sw},
     "warranty": "Monthly/Annual Subscription."},
    {"id": 91, "name": "Canva AI", "category": "AI Software", "brand": "Canva", "price": 1500, "moq": "1 License",
     "shortDescription": "Accessible AI design and image generation suite.",
     "description": "Canva's Magic Studio integrates AI directly into your design process. Generate custom images effortlessly.",
     "additionalInfo": {
         **{"AI Suite": "Magic Studio", "Max Canvas Size": "8000x3125px", "Exports": "PNG, JPG, PDF, MP4, SVG",
            "Features": "Magic Switch, Magic Write", "Languages": "100+ Supported", "Cloud Storage": "1TB included",
            "Team Collaboration": "Real-time editing", "Mobile App": "iOS / Android"}, **std_sw},
     "warranty": "Monthly/Annual Subscription."},
    {"id": 92, "name": "Suno", "category": "AI Software", "brand": "Suno", "price": 1000, "badge": "Music Gen",
     "moq": "1 License", "shortDescription": "Generate full-length songs with vocals from text prompts.",
     "description": "Suno is a revolutionary AI music generator that can compose complete songs, including realistic vocals.",
     "additionalInfo": {**{"Core Model": "Bark / Chirp V3", "Output Length": "Up to 2 mins per generation",
                           "Extensions": "Extend up to 10 mins", "Audio Format": "MP3, WAV",
                           "Vocals": "Multi-lingual auto-vocals", "Genres": "Any text-described genre",
                           "Commercial Rights": "Yes (Pro)", "API": "Community APIs"}, **std_sw},
     "warranty": "Monthly/Annual Subscription."},
    {"id": 93, "name": "AIVA", "category": "AI Software", "brand": "AIVA", "price": 1500, "moq": "1 License",
     "shortDescription": "AI music composer designed for creative professionals.",
     "description": "AIVA acts as your virtual music composing assistant. Create custom background music quickly.",
     "additionalInfo": {**{"AI Engine": "Deep Learning LSTM", "Genres": "Cinematic, Jazz, Pop, Ambient",
                           "Output Formats": "MP3, WAV, MIDI, STEMS", "Maximum Tracks": "300 downloads/month",
                           "Licensing": "Full Copyright Ownership", "UI": "Web & Desktop App",
                           "Editing": "Built-in piano roll", "Use Case": "Video Games, Film"}, **std_sw},
     "warranty": "Monthly/Annual Subscription."},
    {"id": 94, "name": "Udio", "category": "AI Software", "brand": "Udio", "price": 1000, "moq": "1 License",
     "shortDescription": "High-fidelity AI music generation platform.",
     "description": "Udio generates pristine, studio-quality music tracks from text. Offering intricate control over genres.",
     "additionalInfo": {
         **{"Model": "Udio V1 High-Fidelity", "Audio Quality": "320kbps / 48kHz", "Track Length": "Up to 3 minutes",
            "Features": "Custom Lyrics, Instrumental", "Formats": "MP3, WAV", "Commercial Rights": "Standard License",
            "Generation Speed": "~30 seconds", "Language": "Global Music Support"}, **std_sw},
     "warranty": "Monthly/Annual Subscription."},
    {"id": 95, "name": "Semrush", "category": "AI Software", "brand": "Semrush", "price": 8500, "badge": "SEO Tools",
     "moq": "1 License", "shortDescription": "Comprehensive AI-driven SEO and marketing toolkit.",
     "description": "Semrush utilizes AI to analyze market trends, track keyword performance, and audit websites.",
     "additionalInfo": {**{"Databases": "25B Keywords, 808M Domains", "AI Features": "SEO Writing Assistant",
                           "Tracking": "Daily rank tracking", "API Access": "Yes (Business Tier)",
                           "Integration": "GSC, Adobe, Trello", "Export": "PDF, CSV, Excel",
                           "Users": "Multi-user management", "Cloud": "SaaS Platform"}, **std_sw},
     "warranty": "Monthly/Annual Subscription."},
    {"id": 96, "name": "Surfer SEO", "category": "AI Software", "brand": "Surfer", "price": 5500, "moq": "1 License",
     "shortDescription": "AI content optimization platform for top search rankings.",
     "description": "Surfer SEO analyzes top-performing web pages and provides data-driven, AI-generated guidelines.",
     "additionalInfo": {**{"AI Model": "NLP & GPT-4 Integration", "Analysis": "500+ on-page factors",
                           "Keyword Database": "Multi-lingual NLP", "SERP Analyzer": "Real-time top 50",
                           "AI Writer": "Auto-generate articles", "Integrations": "WP, Google Docs",
                           "Extension": "Chrome extension", "Export": "HTML, Text"}, **std_sw},
     "warranty": "Monthly/Annual Subscription."},
    {"id": 97, "name": "Jasper", "category": "AI Software", "brand": "Jasper", "price": 4500, "moq": "1 License",
     "shortDescription": "Enterprise-grade AI copywriting and marketing assistant.",
     "description": "Jasper helps your team create high-quality, SEO-optimized content 10X faster.", "additionalInfo": {
        **{"Core Models": "GPT-4, Claude, Gemini", "Tone of Voice": "Custom brand voice URL",
           "Workflows": "50+ Marketing Templates", "Output": "Web, PDF, DOCX", "Team Features": "Campaign Management",
           "Security": "SOC2 Certified", "Integrations": "Surfer SEO, Chrome", "Support": "Priority Routing"},
        **std_sw}, "warranty": "Monthly/Annual Subscription."},
    {"id": 98, "name": "GitHub Copilot", "category": "AI Software", "brand": "GitHub", "price": 1500,
     "badge": "Code Gen", "moq": "1 License", "shortDescription": "AI pair programmer integrated into your IDE.",
     "description": "GitHub Copilot utilizes OpenAI models to suggest code snippets and entire functions in real-time.",
     "additionalInfo": {**{"Base Model": "OpenAI Codex", "Supported IDEs": "VS Code, JetBrains",
                           "Languages": "Python, JS, TS, Go, C++", "Latency": "~100ms",
                           "Context Window": "8,000+ tokens", "Security": "No telemetry retention",
                           "Vulnerability Filter": "Built-in scanner", "License": "Business Seat"}, **std_sw},
     "warranty": "Monthly/Annual Subscription."},
    {"id": 99, "name": "Replit AI", "category": "AI Software", "brand": "Replit", "price": 1500, "moq": "1 License",
     "shortDescription": "Cloud-based IDE with integrated AI coding assistance.",
     "description": "Replit AI allows developers to write, debug, and deploy code entirely in the cloud.",
     "additionalInfo": {
         **{"Environment": "Cloud IDE", "AI Model": "Replit LM (CodeLlama)", "Context Window": "32k tokens",
            "Features": "Explain Code, Generate", "Deployment": "1-click cloud hosting",
            "Databases": "Built-in PostgreSQL", "Collaboration": "Multiplayer real-time",
            "Runtime": "Containerized VMs"}, **std_sw}, "warranty": "Monthly/Annual Subscription."},
    {"id": 100, "name": "Cursor AI", "category": "AI Software", "brand": "Cursor", "price": 2000, "moq": "1 License",
     "shortDescription": "The AI-first code editor designed to build software faster.",
     "description": "Cursor is an advanced IDE built around AI. It understands your entire codebase.",
     "additionalInfo": {**{"Base Models": "GPT-4, Claude 3 Opus", "Context Window": "Up to 128k tokens",
                           "Feature": "Codebase-wide Q&A", "Refactoring": "Inline editing diffs",
                           "IDE Base": "VSCodium (VS Code compat)", "Privacy": "Local mode available",
                           "Platforms": "Windows, macOS, Linux", "Terminal": "Integrated AI Bash"}, **std_sw},
     "warranty": "Monthly/Annual Subscription."},
    {"id": 101, "name": "ElevenLabs", "category": "AI Software", "brand": "ElevenLabs", "price": 2000,
     "badge": "Voice Bot", "moq": "1 License",
     "shortDescription": "The most realistic AI text-to-speech and voice cloning software.",
     "description": "ElevenLabs generates incredibly emotive and lifelike audio from text. It supports over 20 languages.",
     "additionalInfo": {
         **{"Voice Model": "Eleven Multilingual v2", "Languages": "29 Languages", "Voices": "1000+ Pre-made",
            "Voice Cloning": "Instant & Professional", "Audio Output": "192kbps MP3 / 44.1kHz",
            "Latency": "~400ms (Turbo)", "API Access": "REST and WebSockets", "Use Case": "Audiobooks, Gaming"},
         **std_sw}, "warranty": "Monthly/Annual Subscription."},
    {"id": 102, "name": "Play.ht", "category": "AI Software", "brand": "Play.ht", "price": 1500, "moq": "1 License",
     "shortDescription": "AI voice generator for ultra-realistic text-to-speech.",
     "description": "Play.ht allows you to instantly generate high-quality audio files using an extensive library of AI voices.",
     "additionalInfo": {
         **{"Voice Model": "PlayHT 2.0 Turbo", "Languages": "130+ Languages", "Voices": "800+ Premium AI Voices",
            "Voice Cloning": "Cross-lingual support", "Output Formats": "MP3, WAV, OGG",
            "Features": "Multi-voice conversations", "API Rate Limit": "Up to 50 concurrent requests",
            "Pronunciation": "Custom phonetic library"}, **std_sw}, "warranty": "Monthly/Annual Subscription."},
    {"id": 103, "name": "Resemble AI", "category": "AI Software", "brand": "Resemble", "price": 2500,
     "moq": "1 License", "shortDescription": "Generative AI voice cloning for enterprise applications.",
     "description": "Resemble AI builds custom, high-fidelity AI voices. It specializes in secure voice cloning for call centers.",
     "additionalInfo": {**{"Voice Model": "Resemble V3 Generative", "Voice Cloning": "Deep learning models",
                           "Speech-to-Speech": "Real-time conversion", "Audio Output": "44.1kHz / 48kHz WAV",
                           "API": "Enterprise GraphQL/REST", "Security": "Resemble Detect (Watermark)",
                           "Latency": "<300ms", "Deployment": "Cloud/On-Premise"}, **std_sw},
     "warranty": "Monthly/Annual Subscription."},
]


# ══════════════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/auth/send-otp', methods=['POST'])
def send_otp():
    data  = request.get_json()
    email = data.get('email', '').strip().lower()
    name  = data.get('name', 'User').strip()

    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required.'}), 400

    conn     = get_db_connection()
    existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if existing:
        return jsonify({'status': 'error', 'message': 'Email is already registered.'}), 409

    otp_code   = ''.join(random.choices(string.digits, k=6))
    expires_at = (datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    conn.execute(
        'INSERT OR REPLACE INTO otp_verifications (email, name, otp, expires_at, attempts) VALUES (?, ?, ?, ?, 0)',
        (email, name, otp_code, expires_at)
    )
    conn.commit()
    conn.close()

    if not send_otp_email(email, name, otp_code):
        return jsonify({'status': 'error', 'message': 'Failed to send OTP email. Check Gmail config in .env'}), 500

    return jsonify({'status': 'success', 'message': 'OTP sent successfully.'})


@app.route('/api/auth/verify-otp-register', methods=['POST'])
def verify_otp_register():
    data     = request.get_json()
    email    = data.get('email',    '').strip().lower()
    name     = data.get('name',     '').strip()
    phone    = data.get('phone',    '').strip()
    password = data.get('password', '').strip()
    otp_code = data.get('otp',      '').strip()

    if not all([email, name, password, otp_code]):
        return jsonify({'status': 'error', 'message': 'All fields are required.'}), 400

    conn   = get_db_connection()
    record = conn.execute('SELECT * FROM otp_verifications WHERE email = ?', (email,)).fetchone()

    if not record:
        conn.close()
        return jsonify({'status': 'error', 'message': 'No OTP found. Please request a new one.'}), 404

    attempts   = record['attempts']
    stored_otp = record['otp']
    expires_at = datetime.strptime(record['expires_at'], '%Y-%m-%d %H:%M:%S')

    if attempts >= 5:
        conn.execute('DELETE FROM otp_verifications WHERE email = ?', (email,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'error', 'message': 'Too many attempts. Please request a new OTP.'}), 429

    conn.execute('UPDATE otp_verifications SET attempts = ? WHERE email = ?', (attempts + 1, email))
    conn.commit()

    if datetime.utcnow() > expires_at:
        conn.execute('DELETE FROM otp_verifications WHERE email = ?', (email,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'error', 'message': 'OTP has expired. Please request a new one.'}), 410

    if otp_code != stored_otp:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Invalid OTP. Please try again.'}), 401

    # Hash password before storing
    hashed_pw = generate_password_hash(password)

    try:
        conn.execute('INSERT INTO users (email, name, password, phone) VALUES (?, ?, ?, ?)', (email, name, hashed_pw, phone or None))
        conn.commit()
    except Exception:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Email already registered.'}), 409

    conn.execute('DELETE FROM otp_verifications WHERE email = ?', (email,))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'user': {'name': name, 'email': email, 'phone': phone or ''}})


@app.route('/api/auth/login', methods=['POST'])
def login_customer():
    data     = request.json
    email    = data.get('email', '').strip().lower()
    phone    = data.get('phone', '').strip()
    password = data.get('password', '').strip()

    conn = get_db_connection()

    if email:
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    elif phone:
        user = conn.execute('SELECT * FROM users WHERE phone = ?', (phone,)).fetchone()
    else:
        conn.close()
        return jsonify({"status": "error", "message": "Email or phone is required."}), 400

    conn.close()

    if user and check_password_hash(user['password'], password):
        return jsonify({"status": "success", "user": {"name": user['name'], "email": user['email'], "phone": user['phone'] or ''}})

    return jsonify({"status": "error", "message": "Invalid credentials."}), 401


@app.route('/api/auth/social', methods=['POST'])
def social_login():
    data       = request.json
    provider   = data.get('provider', 'Social')
    real_email = data.get('email')
    real_name  = data.get('name')
    uid        = data.get('uid')

    if not real_email:
        real_email = f"{uid}@{provider.lower()}.com"

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (real_email,)).fetchone()

    if not user:
        conn.execute(
            'INSERT INTO users (email, name, password) VALUES (?, ?, ?)',
            (real_email, real_name, generate_password_hash("oauth_no_password"))
        )
        conn.commit()

    conn.close()
    return jsonify({"status": "success", "user": {"name": real_name, "email": real_email, "phone": ""}})


@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    data  = request.get_json()
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required.'}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT id, name FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if not user:
        return jsonify({'status': 'error', 'message': 'No account found with this email.'}), 404

    otp_code   = ''.join(random.choices(string.digits, k=6))
    expires_at = (datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    conn.execute(
        'INSERT OR REPLACE INTO otp_verifications (email, name, otp, expires_at, attempts) VALUES (?, ?, ?, ?, 0)',
        (email, user['name'], otp_code, expires_at)
    )
    conn.commit()
    conn.close()

    if not send_otp_email(email, user['name'], otp_code):
        return jsonify({'status': 'error', 'message': 'Failed to send OTP email.'}), 500

    return jsonify({'status': 'success', 'message': 'OTP sent to your email.'})


@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    data         = request.get_json()
    email        = data.get('email',        '').strip().lower()
    otp_code     = data.get('otp',          '').strip()
    new_password = data.get('new_password', '').strip()

    if not all([email, otp_code, new_password]):
        return jsonify({'status': 'error', 'message': 'All fields are required.'}), 400

    conn   = get_db_connection()
    record = conn.execute('SELECT * FROM otp_verifications WHERE email = ?', (email,)).fetchone()

    if not record:
        conn.close()
        return jsonify({'status': 'error', 'message': 'No OTP found. Please request a new one.'}), 404

    attempts   = record['attempts']
    stored_otp = record['otp']
    expires_at = datetime.strptime(record['expires_at'], '%Y-%m-%d %H:%M:%S')

    if attempts >= 5:
        conn.execute('DELETE FROM otp_verifications WHERE email = ?', (email,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'error', 'message': 'Too many attempts. Please request a new OTP.'}), 429

    conn.execute('UPDATE otp_verifications SET attempts = ? WHERE email = ?', (attempts + 1, email))
    conn.commit()

    if datetime.utcnow() > expires_at:
        conn.execute('DELETE FROM otp_verifications WHERE email = ?', (email,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'error', 'message': 'OTP has expired. Please request a new one.'}), 410

    if otp_code != stored_otp:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Invalid OTP. Please try again.'}), 401

    hashed_pw = generate_password_hash(new_password)
    conn.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_pw, email))
    conn.execute('DELETE FROM otp_verifications WHERE email = ?', (email,))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'message': 'Password reset successfully.'})


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(products)


# ══════════════════════════════════════════════════════════════════════════════
# CART & WISHLIST  (per-user, persisted in DB)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/cart', methods=['GET', 'POST'])
def handle_cart():
    user_email = request.headers.get('User-Email', 'guest')

    if request.method == 'POST':
        data = request.json
        if data and 'cart' in data:
            conn = get_db_connection()
            conn.execute(
                'INSERT OR REPLACE INTO carts (user_email, cart_data) VALUES (?, ?)',
                (user_email, json.dumps(data['cart']))
            )
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "cart": data['cart']})
        return jsonify({"status": "error", "message": "No cart data provided."}), 400

    conn  = get_db_connection()
    row   = conn.execute('SELECT cart_data FROM carts WHERE user_email = ?', (user_email,)).fetchone()
    conn.close()
    return jsonify(json.loads(row['cart_data']) if row else {})


@app.route('/api/wishlist', methods=['GET', 'POST'])
def handle_wishlist():
    user_email = request.headers.get('User-Email', 'guest')

    if request.method == 'POST':
        data = request.json
        if data and 'wishlist' in data:
            conn = get_db_connection()
            conn.execute(
                'INSERT OR REPLACE INTO wishlists (user_email, wishlist_data) VALUES (?, ?)',
                (user_email, json.dumps(data['wishlist']))
            )
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "wishlist": data['wishlist']})
        return jsonify({"status": "error", "message": "No wishlist data provided."}), 400

    conn = get_db_connection()
    row  = conn.execute('SELECT wishlist_data FROM wishlists WHERE user_email = ?', (user_email,)).fetchone()
    conn.close()
    return jsonify(json.loads(row['wishlist_data']) if row else [])


# ══════════════════════════════════════════════════════════════════════════════
# INQUIRY & BOOKING
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/inquiry', methods=['POST'])
def handle_inquiry():
    data    = request.json
    name    = data.get('name', 'N/A')
    email   = data.get('email', 'N/A')
    phone   = data.get('phone', 'Not Provided')
    product = data.get('product', 'Not Selected')
    message = data.get('message', '')

    html_content = f"""
    <div style="margin:0;padding:40px 0;background:#eef2f7;font-family:Segoe UI,Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr><td align="center">
              <table width="640" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 10px 35px rgba(0,0,0,0.08);">
                <tr><td style="padding:30px 30px 20px 30px;background:#111827;color:#ffffff;">
                    <h2 style="margin:0;font-size:20px;font-weight:600;">New Inquiry Received</h2>
                    <p style="margin:6px 0 0 0;font-size:13px;color:#9ca3af;">Website Lead Notification</p>
                </td></tr>
                <tr><td style="padding:30px;">
                    <table width="100%" cellpadding="10" cellspacing="0" style="font-size:14px;color:#374151;">
                      <tr><td style="color:#6b7280;width:140px;">Full Name</td><td style="font-weight:600;color:#111827;">{name}</td></tr>
                      <tr><td style="color:#6b7280;">Email</td><td><a href="mailto:{email}" style="color:#2563eb;text-decoration:none;font-weight:500;">{email}</a></td></tr>
                      <tr><td style="color:#6b7280;">Phone</td><td>{phone}</td></tr>
                      <tr><td style="color:#6b7280;">Product Interest</td><td style="font-weight:600;color:#111827;">{product}</td></tr>
                    </table>
                    <div style="height:1px;background:#e5e7eb;margin:25px 0;"></div>
                    <div style="background:#f9fafb;padding:20px;border-radius:10px;border:1px solid #e5e7eb;">
                      <p style="margin:0;font-size:13px;color:#6b7280;">Message</p>
                      <p style="margin:8px 0 0 0;font-size:14px;color:#111827;line-height:1.6;">{message}</p>
                    </div>
                </td></tr>
                <tr><td style="background:#f3f4f6;padding:18px;text-align:center;font-size:12px;color:#6b7280;">
                    Submitted via <strong>NeuroStore Website</strong><br/>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                </td></tr>
              </table>
          </td></tr>
        </table>
    </div>"""

    success = send_email_helper("New Inquiry from Website", html_content, email)
    if success:
        return jsonify({"status": "success", "message": "Inquiry sent successfully!"})
    return jsonify({"status": "error", "message": "Failed to send email."}), 500


@app.route('/api/book-service', methods=['POST'])
def handle_booking():
    data    = request.json
    name    = data.get('name', 'N/A')
    email   = data.get('email', 'N/A')
    phone   = data.get('phone', 'Not Provided')
    company = data.get('company', 'Not Provided')
    message = data.get('message', 'No message provided.')
    service = data.get('service', 'Service')

    html_content = f"""
    <div style="background:#f1f5f9;padding:50px 0;font-family:Segoe UI,Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td align="center">
            <table width="720" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:18px;overflow:hidden;box-shadow:0 25px 60px rgba(0,0,0,0.08);">
              <tr><td style="background:linear-gradient(90deg,#4f46e5,#7c3aed);padding:28px 40px;color:#ffffff;">
                  <h2 style="margin:0;font-size:22px;font-weight:600;">New Service Booking</h2>
              </td></tr>
              <tr><td style="padding:40px;">
                  <div style="text-align:center;margin-bottom:30px;">
                    <span style="background:#eef2ff;color:#4338ca;padding:10px 22px;border-radius:30px;font-size:14px;font-weight:600;">{service}</span>
                  </div>
                  <div style="background:#f8fafc;padding:25px;border-radius:14px;border:1px solid #e2e8f0;">
                    <table width="100%" cellpadding="8" cellspacing="0" style="font-size:14px;color:#334155;">
                      <tr><td style="width:160px;color:#64748b;">Full Name</td><td style="font-weight:600;color:#0f172a;">{name}</td></tr>
                      <tr><td style="color:#64748b;">Email</td><td><a href="mailto:{email}" style="color:#2563eb;text-decoration:none;">{email}</a></td></tr>
                      <tr><td style="color:#64748b;">Phone</td><td>{phone}</td></tr>
                      <tr><td style="color:#64748b;">Company</td><td>{company}</td></tr>
                    </table>
                  </div>
                  <div style="margin-top:30px;padding:24px;background:#ffffff;border-radius:14px;border:1px solid #e2e8f0;">
                    <p style="margin:0 0 10px 0;font-size:13px;color:#64748b;font-weight:500;">Client Message</p>
                    <p style="margin:0;font-size:15px;color:#0f172a;line-height:1.7;">{message}</p>
                  </div>
              </td></tr>
              <tr><td style="background:#f8fafc;padding:18px;text-align:center;font-size:12px;color:#64748b;">
                  Generated automatically by NeuroStore Booking System<br/>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
              </td></tr>
            </table>
        </td></tr>
      </table>
    </div>"""

    success = send_email_helper(f"New Service Booking - {service}", html_content, email)
    if success:
        return jsonify({"status": "success", "message": "Booking sent successfully!"})
    return jsonify({"status": "error", "message": "Failed to send booking email."}), 500


# ══════════════════════════════════════════════════════════════════════════════
# ORDERS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/orders/user', methods=['GET'])
def get_user_orders():
    user_email = request.headers.get('User-Email')
    if not user_email:
        return jsonify({"orders": []}), 400
    conn   = get_db_connection()
    orders = conn.execute(
        'SELECT * FROM orders WHERE user_email = ? ORDER BY id DESC', (user_email,)
    ).fetchall()
    conn.close()
    return jsonify({"orders": [dict(o) for o in orders]})


@app.route('/api/orders', methods=['POST'])
def place_order():
    data       = request.json
    user_email = request.headers.get('User-Email')
    items      = data.get('items', {})
    total      = data.get('total', 0)
    address    = data.get('address', '')
    payment    = data.get('payment', 'COD')

    if not items or total <= 0:
        return jsonify({"status": "error", "message": "Invalid order data"}), 400

    try:
        conn    = get_db_connection()
        cursor  = conn.execute(
            '''INSERT INTO orders (user_email, items, total, address, payment, payment_id, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_email, json.dumps(items), total, address, payment,
             None, 'Confirmed', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Order placed!", "order_id": order_id})
    except Exception as e:
        print(f"Order Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# RAZORPAY
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/razorpay/create-order', methods=['POST'])
def create_razorpay_order():
    key_id     = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        return jsonify({"error": "Payment gateway not configured"}), 500

    client = razorpay.Client(auth=(key_id, key_secret))
    data   = request.json
    amount = data.get('amount', 0)

    if not amount or amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    try:
        order = client.order.create({
            "amount":          int(amount * 100),
            "currency":        "INR",
            "receipt":         f"receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "payment_capture": 1
        })
        return jsonify({"id": order['id'], "amount": order['amount'], "currency": order['currency']})
    except Exception as e:
        print(f"Razorpay Order Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/razorpay/verify', methods=['POST'])
def verify_razorpay_payment():
    data                = request.json
    user_email          = request.headers.get('User-Email')
    razorpay_order_id   = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature  = data.get('razorpay_signature')
    items               = data.get('items', {})
    total               = data.get('total', 0)
    address             = data.get('address', '')
    payment_method      = data.get('method', 'Online')

    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    if not key_secret:
        return jsonify({"success": False, "error": "Payment gateway not configured"}), 500

    try:
        message             = f"{razorpay_order_id}|{razorpay_payment_id}".encode()
        generated_signature = hmac.new(key_secret.encode(), message, hashlib.sha256).hexdigest()

        if generated_signature != razorpay_signature:
            return jsonify({"success": False, "error": "Signature mismatch"}), 400

        conn     = get_db_connection()
        existing = conn.execute('SELECT id FROM orders WHERE payment_id = ?', (razorpay_payment_id,)).fetchone()
        if existing:
            conn.close()
            return jsonify({"success": True})

        cursor = conn.execute(
            '''INSERT INTO orders (user_email, items, total, address, payment, payment_id, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_email, json.dumps(items), total, address, payment_method,
             razorpay_payment_id, 'Confirmed', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"success": True, "order_id": order_id})

    except Exception as e:
        print(f"Verification Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES  (protected by HTTP Basic Auth)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    import base64
    data     = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    if username == ADMIN_USER and password == ADMIN_PASS:
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        return jsonify({'status': 'success', 'token': token})
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401


@app.route('/api/admin/product', methods=['POST'])
@require_admin
def add_product():
    global products
    data        = request.json
    new_id      = max(p['id'] for p in products) + 1 if products else 1
    new_product = {
        "id":               new_id,
        "name":             data.get('name'),
        "category":         data.get('category'),
        "brand":            data.get('brand', 'NeuroStore'),
        "price":            int(data.get('price', 0)),
        "shortDescription": data.get('shortDescription', ''),
        "badge":            "New",
        "image":            "https://images.unsplash.com/photo-1611162617474-5b21e879e113?q=80&w=800&auto=format&fit=crop"
    }
    products.insert(0, new_product)
    return jsonify({"status": "success", "message": "Product added successfully!"})


@app.route('/api/admin/product/<int:product_id>', methods=['DELETE'])
@require_admin
def delete_product(product_id):
    global products
    products = [p for p in products if p['id'] != product_id]
    return jsonify({"status": "success", "message": "Product deleted successfully!"})


@app.route('/api/admin/orders', methods=['GET'])
@require_admin
def get_all_orders():
    conn   = get_db_connection()
    orders = conn.execute('SELECT * FROM orders ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify({"orders": [dict(o) for o in orders]})


@app.route('/api/admin/users', methods=['GET'])
@require_admin
def get_all_users():
    conn  = get_db_connection()
    users = conn.execute('SELECT id, name, email, phone FROM users').fetchall()
    conn.close()
    return jsonify({"users": [dict(u) for u in users]})


# ══════════════════════════════════════════════════════════════════════════════
# ADDRESSES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/addresses', methods=['GET'])
def get_addresses():
    email = request.headers.get('User-Email')
    if not email:
        return jsonify([])
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT * FROM addresses WHERE user_email = ? ORDER BY is_default DESC, id ASC',
        (email,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/addresses', methods=['POST'])
def add_address():
    email = request.headers.get('User-Email')
    if not email:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if data.get('is_default'):
        conn.execute('UPDATE addresses SET is_default = 0 WHERE user_email = ?', (email,))
    conn.execute(
        '''INSERT INTO addresses (user_email, label, name, street, city, state, zip, country, is_default)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (email, data.get('label', ''), data.get('name', ''), data.get('street', ''),
         data.get('city', ''), data.get('state', ''), data.get('zip', ''),
         data.get('country', 'India'), 1 if data.get('is_default') else 0)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/addresses/<int:addr_id>', methods=['PUT'])
def update_address(addr_id):
    email = request.headers.get('User-Email')
    if not email:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if data.get('is_default'):
        conn.execute('UPDATE addresses SET is_default = 0 WHERE user_email = ?', (email,))
    conn.execute(
        '''UPDATE addresses SET label=?, name=?, street=?, city=?, state=?, zip=?, country=?, is_default=?
           WHERE id=? AND user_email=?''',
        (data.get('label', ''), data.get('name', ''), data.get('street', ''),
         data.get('city', ''), data.get('state', ''), data.get('zip', ''),
         data.get('country', 'India'), 1 if data.get('is_default') else 0,
         addr_id, email)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/addresses/<int:addr_id>', methods=['DELETE'])
def delete_address(addr_id):
    email = request.headers.get('User-Email')
    if not email:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    conn.execute('DELETE FROM addresses WHERE id = ? AND user_email = ?', (addr_id, email))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/addresses/<int:addr_id>/default', methods=['PATCH'])
def set_default_address(addr_id):
    email = request.headers.get('User-Email')
    if not email:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    conn.execute('UPDATE addresses SET is_default = 0 WHERE user_email = ?', (email,))
    conn.execute('UPDATE addresses SET is_default = 1 WHERE id = ? AND user_email = ?', (addr_id, email))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ══════════════════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app.run(debug=True, port=5000)