import os
import json
import hmac
import random
import string
import hashlib
import smtplib
import sqlite3
import base64
import razorpay
import threading
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask import send_from_directory
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            label TEXT DEFAULT 'Home',
            name TEXT,
            street TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            country TEXT DEFAULT 'India',
            is_default INTEGER DEFAULT 0
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS product_views (
            product_id INTEGER NOT NULL,
            user_email TEXT NOT NULL DEFAULT 'guest',
            viewed_at  TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS search_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_email TEXT NOT NULL DEFAULT 'guest',
            query      TEXT,
            searched_at TEXT NOT NULL
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
STORE_EMAIL        = os.getenv("STORE_EMAIL", EMAIL_USER)  # admin/store notification address


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


def _build_item_rows(items_dict):
    """Return an HTML table body string + plain-text lines for the order items."""
    rows_html  = ''
    rows_plain = ''
    if isinstance(items_dict, str):
        try:
            items_dict = json.loads(items_dict.replace("'", '"'))
        except Exception:
            items_dict = {}
    if not isinstance(items_dict, dict):
        return '', ''
    for pid, qty in items_dict.items():
        product_name = next((p['name'] for p in products if str(p['id']) == str(pid)), f'Product #{pid}')
        price        = next((p['price'] for p in products if str(p['id']) == str(pid)), 0)
        try:
            qty_num = int(qty)
            price_num = float(price)
            total_item_price = int(price_num * qty_num)
        except (ValueError, TypeError):
            qty_num = 1
            total_item_price = 0

        rows_html  += (
            f'<tr>'
            f'<td style="padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:13px;color:#334155;">{product_name}</td>'
            f'<td style="padding:10px 12px;text-align:center;border-bottom:1px solid #f1f5f9;">×{qty_num}</td>'
            f'<td style="padding:10px 12px;text-align:right;font-weight:600;border-bottom:1px solid #f1f5f9;">₹{total_item_price:,}</td>'
            f'</tr>'
        )
        rows_plain += f'  • {product_name}  ×{qty_num}  —  ₹{total_item_price:,}\n'
    return rows_html, rows_plain


def send_order_confirmation_email(
        to_email, customer_name, order_id,
        items_dict, total, address, payment_method,
        payment_id=None
):
    """
    Send two emails in a single SMTP session:
      1. Customer confirmation  → to_email   (if provided)
      2. Store/admin alert      → STORE_EMAIL (always)
    """
    try:
        item_rows_html, item_rows_plain = _build_item_rows(items_dict)
        payment_label = 'Cash on Delivery' if payment_method == 'COD' else 'Online Payment'
        year          = datetime.now().year
        order_date    = datetime.now().strftime('%d %b %Y, %I:%M %p')

        # ── 1. Customer confirmation HTML ──────────────────────────────────────
        customer_html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f8fafc;padding:40px 20px;">
          <div style="background:#fff;border-radius:16px;overflow:hidden;border:1px solid #e2e8f0;">

            <!-- Header -->
            <div style="background:#0f172a;padding:28px 36px;">
              <h2 style="margin:0;color:#fff;font-size:22px;">NeuroStore</h2>
              <p style="margin:4px 0 0;color:#94a3b8;font-size:13px;">Order Confirmation</p>
            </div>

            <!-- Body -->
            <div style="padding:36px;">
              <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:16px 20px;margin-bottom:24px;">
                <p style="margin:0;font-size:15px;font-weight:700;color:#15803d;">✅ Order Confirmed &mdash; #{order_id}</p>
              </div>
              <p style="font-size:15px;color:#334155;margin-bottom:20px;">
                Hi <strong>{customer_name}</strong>, thank you for shopping with NeuroStore!
                Your order has been received and is being processed.
              </p>

              <!-- Items table -->
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;margin-bottom:20px;">
                <thead>
                  <tr style="background:#f8fafc;">
                    <th style="padding:10px 12px;text-align:left;font-size:12px;color:#64748b;text-transform:uppercase;">Product</th>
                    <th style="padding:10px 12px;text-align:center;font-size:12px;color:#64748b;text-transform:uppercase;">Qty</th>
                    <th style="padding:10px 12px;text-align:right;font-size:12px;color:#64748b;text-transform:uppercase;">Amount</th>
                  </tr>
                </thead>
                <tbody>{item_rows_html}</tbody>
              </table>

              <!-- Total -->
              <div style="text-align:right;margin-bottom:20px;">
                <span style="font-size:16px;font-weight:800;color:#6366f1;">Total: ₹{int(total):,}</span>
                <span style="display:block;font-size:12px;color:#94a3b8;margin-top:4px;">Incl. 18% GST &nbsp;·&nbsp; {payment_label}</span>
              </div>

              <!-- Shipping -->
              <div style="background:#f8fafc;border-radius:10px;padding:14px 18px;margin-bottom:20px;border:1px solid #e2e8f0;">
                <p style="margin:0;font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;">Shipping To</p>
                <p style="margin:6px 0 0;font-size:13px;color:#334155;line-height:1.5;">{address}</p>
              </div>

              <p style="font-size:13px;color:#64748b;line-height:1.6;">
                📦 Estimated delivery: <strong>3–7 business days</strong><br/>
                Questions? Email us at <a href="mailto:info@staunchtec.com" style="color:#6366f1;font-weight:700;text-decoration:none;">info@staunchtec.com</a>
              </p>
            </div>

            <!-- Footer -->
            <div style="background:#f1f5f9;padding:16px 36px;text-align:center;">
              <p style="margin:0;font-size:12px;color:#94a3b8;">© {year} NeuroStore &nbsp;|&nbsp; All rights reserved</p>
            </div>
          </div>
        </div>"""

        # ── 2. Store/admin notification HTML ───────────────────────────────────
        customer_display = to_email if to_email else 'Guest (no email)'
        payment_id_line  = f'<p style="margin:0;font-size:13px;color:#334155;"><strong>Payment ID:</strong> {payment_id}</p>' if payment_id else ''

        admin_html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f8fafc;padding:40px 20px;">
          <div style="background:#fff;border-radius:16px;overflow:hidden;border:1px solid #e2e8f0;">

            <!-- Header -->
            <div style="background:#1e1b4b;padding:28px 36px;">
              <h2 style="margin:0;color:#fff;font-size:22px;">NeuroStore &mdash; New Order Alert</h2>
              <p style="margin:4px 0 0;color:#a5b4fc;font-size:13px;">Admin Notification</p>
            </div>

            <!-- Body -->
            <div style="padding:36px;">
              <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:16px 20px;margin-bottom:24px;">
                <p style="margin:0;font-size:15px;font-weight:700;color:#1d4ed8;">🛒 New Order Placed &mdash; #{order_id}</p>
                <p style="margin:4px 0 0;font-size:12px;color:#3b82f6;">{order_date}</p>
              </div>

              <!-- Customer info -->
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;margin-bottom:20px;">
                <tr style="background:#f8fafc;">
                  <th colspan="2" style="padding:10px 12px;text-align:left;font-size:11px;color:#64748b;text-transform:uppercase;">Customer Details</th>
                </tr>
                <tr>
                  <td style="padding:10px 12px;font-size:13px;color:#64748b;border-bottom:1px solid #f1f5f9;">Name</td>
                  <td style="padding:10px 12px;font-size:13px;font-weight:600;color:#0f172a;border-bottom:1px solid #f1f5f9;">{customer_name}</td>
                </tr>
                <tr>
                  <td style="padding:10px 12px;font-size:13px;color:#64748b;border-bottom:1px solid #f1f5f9;">Email</td>
                  <td style="padding:10px 12px;font-size:13px;font-weight:600;color:#0f172a;border-bottom:1px solid #f1f5f9;">{customer_display}</td>
                </tr>
                <tr>
                  <td style="padding:10px 12px;font-size:13px;color:#64748b;border-bottom:1px solid #f1f5f9;">Payment</td>
                  <td style="padding:10px 12px;font-size:13px;font-weight:600;color:#0f172a;border-bottom:1px solid #f1f5f9;">{payment_label}</td>
                </tr>
                <tr>
                  <td style="padding:10px 12px;font-size:13px;color:#64748b;">Address</td>
                  <td style="padding:10px 12px;font-size:13px;color:#334155;line-height:1.5;">{address}</td>
                </tr>
              </table>

              {payment_id_line}

              <!-- Items ordered -->
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;margin-top:16px;margin-bottom:20px;">
                <thead>
                  <tr style="background:#f8fafc;">
                    <th style="padding:10px 12px;text-align:left;font-size:12px;color:#64748b;text-transform:uppercase;">Product</th>
                    <th style="padding:10px 12px;text-align:center;font-size:12px;color:#64748b;text-transform:uppercase;">Qty</th>
                    <th style="padding:10px 12px;text-align:right;font-size:12px;color:#64748b;text-transform:uppercase;">Amount</th>
                  </tr>
                </thead>
                <tbody>{item_rows_html}</tbody>
              </table>

              <div style="text-align:right;margin-bottom:16px;">
                <span style="font-size:17px;font-weight:800;color:#6366f1;">Order Total: ₹{int(total):,}</span>
                <span style="display:block;font-size:12px;color:#94a3b8;margin-top:4px;">Incl. 18% GST</span>
              </div>

              <p style="font-size:12px;color:#94a3b8;margin-top:24px;">
                This is an automated admin notification from NeuroStore.
                Do not reply to this email.
              </p>
            </div>

            <!-- Footer -->
            <div style="background:#f1f5f9;padding:16px 36px;text-align:center;">
              <p style="margin:0;font-size:12px;color:#94a3b8;">© {year} NeuroStore Admin Panel</p>
            </div>
          </div>
        </div>"""

        # ── Send emails in one SMTP session ───────────────────────────────
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)

        # — Customer email (only if valid recipient address provided) —
        if to_email and isinstance(to_email, str) and '@' in to_email:
            try:
                msg_customer = MIMEMultipart('alternative')
                msg_customer['Subject'] = f'Order Confirmed \u2705 \u2014 NeuroStore #{order_id}'
                msg_customer['From']    = f'NeuroStore <{EMAIL_USER}>'
                msg_customer['To']      = to_email
                msg_customer.attach(MIMEText(customer_html, 'html'))
                server.sendmail(EMAIL_USER, to_email, msg_customer.as_string())
                print(f"[EMAIL] Customer confirmation sent to {to_email}")
            except Exception as customer_err:
                print(f"[EMAIL ERROR] Failed sending to customer {to_email}: {customer_err}")

        # — Store/admin notification (always sent) —
        if STORE_EMAIL and isinstance(STORE_EMAIL, str) and '@' in STORE_EMAIL:
            try:
                msg_admin = MIMEMultipart('alternative')
                msg_admin['Subject'] = f'\U0001f6d2 New Order #{order_id} \u2014 \u20b9{int(total):,} ({payment_label})'
                msg_admin['From']    = f'NeuroStore Orders <{EMAIL_USER}>'
                msg_admin['To']      = STORE_EMAIL
                msg_admin.attach(MIMEText(admin_html, 'html'))
                server.sendmail(EMAIL_USER, STORE_EMAIL, msg_admin.as_string())
                print(f"[EMAIL] Admin notification sent to {STORE_EMAIL}")
            except Exception as admin_err:
                print(f"[EMAIL ERROR] Failed sending to admin {STORE_EMAIL}: {admin_err}")

        server.quit()
        return True

    except Exception as e:
        print(f"ORDER EMAIL ERROR: {e}")
        return False


def send_order_confirmation_email_async(to_email, customer_name, order_id, items_dict, total, address, payment_method, payment_id=None):
    """
    Dispatch send_order_confirmation_email in a background thread to prevent blocking HTTP response.
    Sends 2 emails: 1 to user (if email provided) and 1 to store/admin (STORE_EMAIL).
    """
    threading.Thread(
        target=send_order_confirmation_email,
        kwargs={
            'to_email': to_email,
            'customer_name': customer_name,
            'order_id': order_id,
            'items_dict': items_dict,
            'total': total,
            'address': address,
            'payment_method': payment_method,
            'payment_id': payment_id,
        },
        daemon=True
    ).start()


def send_order_status_update_email(to_email, customer_name, order_id, new_status, items_dict, total, address):
    """
    Send an order tracking status update email to the customer.
    Called whenever admin changes the order status or a customer cancels.
    """
    if not to_email or not isinstance(to_email, str) or '@' not in to_email:
        return False  # Guest order with no email — skip silently

    try:
        item_rows_html, _ = _build_item_rows(items_dict)
        year = datetime.now().year
        updated_at = datetime.now().strftime('%d %b %Y, %I:%M %p')

        # ── Extract product names from items_dict ───────────────────────────────
        parsed_items = items_dict
        if isinstance(parsed_items, str):
            try:
                parsed_items = json.loads(parsed_items.replace("'", '"'))
            except Exception:
                parsed_items = {}
        if not isinstance(parsed_items, dict):
            parsed_items = {}

        product_names = []
        for pid in parsed_items.keys():
            name = next((p['name'] for p in products if str(p['id']) == str(pid)), None)
            if name:
                product_names.append(name)

        if product_names:
            # Show first product name; if multiple items add "+N more"
            banner_title = product_names[0]
            if len(product_names) > 1:
                banner_title += f' +{len(product_names) - 1} more'
            subject_title = product_names[0] if len(product_names) == 1 else f'{product_names[0]} & {len(product_names)-1} more'
        else:
            banner_title  = f'Order #{order_id}'
            subject_title = f'Order #{order_id}'

        # ── Visual Tracking Progress Bar Builder ─────────────────────────────
        step_order = {'Confirmed': 1, 'Processing': 2, 'Shipped': 3, 'Delivered': 4}
        curr_step = step_order.get(new_status, 0)
        
        timeline_html = ""
        if new_status != 'Cancelled':
            steps = [
                ('Confirmed', '1', '\u2705'),
                ('Processing', '2', '\u2699\ufe0f'),
                ('Shipped', '3', '\U0001f69a'),
                ('Delivered', '4', '\U0001f4e6')
            ]
            cols = ""
            for name, num, icon in steps:
                s_idx = step_order[name]
                if s_idx < curr_step:
                    circle_bg = '#10b981'
                    circle_txt = '#ffffff'
                    label_color = '#059669'
                    badge_icon = '\u2713'
                elif s_idx == curr_step:
                    circle_bg = '#4f46e5'
                    circle_txt = '#ffffff'
                    label_color = '#4f46e5'
                    badge_icon = icon
                else:
                    circle_bg = '#e2e8f0'
                    circle_txt = '#64748b'
                    label_color = '#94a3b8'
                    badge_icon = num

                cols += f"""
                <td style="text-align:center;width:25%;padding:4px;">
                    <div style="display:inline-block;width:32px;height:32px;line-height:32px;border-radius:50%;background:{circle_bg};color:{circle_txt};font-size:13px;font-weight:700;margin:0 auto 6px;">
                        {badge_icon}
                    </div>
                    <div style="font-size:11px;font-weight:700;color:{label_color};text-transform:uppercase;letter-spacing:0.5px;">
                        {name}
                    </div>
                </td>
                """
            timeline_html = f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px 8px;margin-bottom:24px;">
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>{cols}</tr>
                </table>
            </div>
            """

        # ── Status-specific styling ──────────────────────────────────────────
        status_config = {
            'Confirmed':  {'icon': '\u2705', 'color': '#15803d', 'bg': '#f0fdf4', 'border': '#bbf7d0',
                           'message': 'Your order has been confirmed and is being prepared.'},
            'Processing': {'icon': '\u2699\ufe0f', 'color': '#b45309', 'bg': '#fffbeb', 'border': '#fde68a',
                           'message': 'Great news! Your order is currently being processed and packed.'},
            'Shipped':    {'icon': '\U0001f69a', 'color': '#1d4ed8', 'bg': '#eff6ff', 'border': '#bfdbfe',
                           'message': 'Your order is on its way! Estimated delivery: 2\u20135 business days.'},
            'Delivered':  {'icon': '\U0001f4e6', 'color': '#0f172a', 'bg': '#f8fafc', 'border': '#e2e8f0',
                           'message': 'Your order has been delivered. We hope you love your purchase!'},
            'Cancelled':  {'icon': '\u274c', 'color': '#b91c1c', 'bg': '#fef2f2', 'border': '#fecaca',
                           'message': 'Your order has been cancelled. If this was a mistake, please contact us.'},
        }
        cfg = status_config.get(new_status, {
            'icon': '\u2139\ufe0f', 'color': '#334155', 'bg': '#f8fafc', 'border': '#e2e8f0',
            'message': f'Your order status has been updated to {new_status}.'
        })

        html_body = f"""
        <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;background:#f1f5f9;padding:32px 16px;">
          <div style="background:#ffffff;border-radius:20px;overflow:hidden;border:1px solid #e2e8f0;box-shadow:0 10px 25px rgba(15,23,42,0.08);">

            <!-- Modern Gradient Header -->
            <div style="background:linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);padding:32px 36px;text-align:left;">
              <div style="display:inline-block;background:rgba(99,102,241,0.25);border:1px solid rgba(165,180,252,0.3);color:#c7d2fe;padding:4px 12px;border-radius:9999px;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:12px;">
                Order Tracking Update
              </div>
              <h1 style="margin:0;color:#ffffff;font-size:24px;font-weight:800;letter-spacing:-0.5px;">NeuroStore</h1>
              <p style="margin:6px 0 0;color:#94a3b8;font-size:13px;">Live status notification for your purchase</p>
            </div>

            <!-- Main Content Area -->
            <div style="padding:32px 36px;">

              <!-- Status Banner -->
              <div style="background:{cfg['bg']};border:1px solid {cfg['border']};border-left:6px solid {cfg['color']};border-radius:12px;padding:20px 24px;margin-bottom:24px;">
                <div style="font-size:19px;font-weight:800;color:{cfg['color']};margin-bottom:4px;">
                  {cfg['icon']}&nbsp; {banner_title}
                </div>
                <div style="font-size:12px;color:#64748b;font-weight:600;">
                  Status: <span style="color:{cfg['color']};font-weight:700;">{new_status}</span> &nbsp;&middot;&nbsp; Order #{order_id} &nbsp;&middot;&nbsp; {updated_at}
                </div>
              </div>

              {timeline_html}

              <p style="font-size:15px;color:#334155;line-height:1.6;margin:0 0 24px;">
                Hi <strong>{customer_name}</strong>,<br/>
                {cfg['message']}
              </p>

              <!-- Items Table -->
              <div style="margin-bottom:24px;">
                <div style="font-size:12px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">
                  Order Summary
                </div>
                <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;border-collapse:separate;border-spacing:0;">
                  <thead>
                    <tr style="background:#f8fafc;">
                      <th style="padding:12px 16px;text-align:left;font-size:12px;color:#475569;text-transform:uppercase;font-weight:700;">Product</th>
                      <th style="padding:12px 16px;text-align:center;font-size:12px;color:#475569;text-transform:uppercase;font-weight:700;">Qty</th>
                      <th style="padding:12px 16px;text-align:right;font-size:12px;color:#475569;text-transform:uppercase;font-weight:700;">Amount</th>
                    </tr>
                  </thead>
                  <tbody>{item_rows_html}</tbody>
                </table>
              </div>

              <!-- Total Card -->
              <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;text-align:right;margin-bottom:24px;">
                <span style="font-size:13px;color:#64748b;font-weight:600;margin-right:12px;">Total Paid / Payable:</span>
                <span style="font-size:20px;font-weight:800;color:#4f46e5;">\u20b9{int(total):,}</span>
              </div>

              <!-- Delivery Destination -->
              <div style="background:#f8fafc;border-radius:12px;padding:18px 20px;margin-bottom:28px;border:1px solid #e2e8f0;">
                <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">
                  📍 Shipping Destination
                </div>
                <div style="font-size:14px;color:#1e293b;line-height:1.5;font-weight:500;">
                  {address}
                </div>
              </div>

              <!-- Support Info Block -->
              <div style="border-top:1px solid #e2e8f0;padding-top:20px;">
                <p style="font-size:13px;color:#64748b;line-height:1.6;margin:0;">
                  Need assistance with your delivery? Contact our support team at
                  <a href="mailto:info@staunchtec.com" style="color:#4f46e5;font-weight:700;text-decoration:none;">info@staunchtec.com</a>
                </p>
              </div>

            </div>

            <!-- Premium Footer -->
            <div style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:20px 36px;text-align:center;">
              <p style="margin:0;font-size:12px;color:#94a3b8;">
                \u00a9 {year} <strong>NeuroStore</strong> &nbsp;|&nbsp; StaunchTech Ecosystem
              </p>
            </div>
          </div>
        </div>"""

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'{subject_title} \u2014 {new_status} | NeuroStore'
        msg['From']    = f'NeuroStore <{EMAIL_USER}>'
        msg['To']      = to_email
        msg.attach(MIMEText(html_body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to_email, msg.as_string())
        server.quit()
        print(f"[EMAIL] Order status update ({new_status}) sent to {to_email}")
        return True

    except Exception as e:
        print(f"[ORDER STATUS EMAIL ERROR] {e}")
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
    {
        "id": 1,
        "name": "Foxit PDF Editor Pro",
        "category": "AI Software",
        "brand": "Foxit",
        "price": 1000,
        "badge": "AI Powered",
        "moq": "1 License",
        "features": [
            "AI Document Summarizer & Smart Q&A",
            "Full Text, Image & Layout Editing",
            "High-Accuracy Multilingual OCR",
            "256-bit AES Encryption & E-Sign",
            "Instant Digital License Delivery"
        ],
        "shortDescription": "Professional PDF editor with integrated AI document intelligence, OCR conversion, legal e-signatures, and enterprise-grade security.",
        "description": "Foxit PDF Editor Pro is a full-featured, professional PDF editing and document management suite equipped with cutting-edge AI features. Create, convert, edit, organize, redact, and e-sign PDF documents with enterprise-grade security across all devices.",
        "additionalInfo": {
            "Product Edition": "Foxit PDF Editor Pro (2026 AI Suite)",
            "Brand": "Foxit Software Inc.",
            "License Type": "Digital License (Instant Activation)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows 11 / 10, macOS 12+, Web, iOS & Android",
            "AI Capabilities": "AI Document Summarizer, Smart Chat, Rewrite & Translate",
            "Editing Tools": "Full Text & Object Editing, Headers, Footers, Watermarks",
            "OCR Engine": "Multilingual Optical Character Recognition (Editable/Searchable)",
            "File Formats": "PDF, PDF/A, Word (.docx), Excel (.xlsx), PPTX, HTML, RTF, Images",
            "Security & Compliance": "256-bit AES Encryption, Permanent Redaction, RMS & HIPAA Compliant",
            "E-Signature": "Built-in Foxit eSign & Certified Digital Signatures",
            "Support & Updates": "24/7 Priority Support, Documentation & Free Version Updates",
            **std_sw
        },
        "warranty": "1 Year Official Foxit Software Assurance & Enterprise Technical Support."
    }
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
        conn.execute('INSERT INTO users (email, name, password) VALUES (?, ?, ?)', (email, name, hashed_pw))
        conn.commit()
    except Exception:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Email already registered.'}), 409

    conn.execute('DELETE FROM otp_verifications WHERE email = ?', (email,))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'user': {'name': name, 'email': email}})


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
        return jsonify({"status": "success", "user": {"name": user['name'], "email": user['email']}})

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
    return jsonify({"status": "success", "user": {"name": real_name, "email": real_email}})


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


@app.route('/api/track/view', methods=['POST'])
def track_product_view():
    """Record a product page view. Called by the frontend on product detail page load."""
    data       = request.json or {}
    product_id = data.get('product_id')
    user_email = request.headers.get('User-Email', 'guest')
    if not product_id:
        return jsonify({'status': 'error', 'message': 'product_id required'}), 400
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO product_views (product_id, user_email, viewed_at) VALUES (?, ?, ?)',
        (int(product_id), user_email, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/track/search', methods=['POST'])
def track_product_search():
    """Record a product search click. Called when user clicks a search result in the nav."""
    data       = request.json or {}
    product_id = data.get('product_id')
    query      = data.get('query', '')
    user_email = request.headers.get('User-Email', 'guest')
    if not product_id:
        return jsonify({'status': 'error', 'message': 'product_id required'}), 400
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO search_logs (product_id, user_email, query, searched_at) VALUES (?, ?, ?, ?)',
        (int(product_id), user_email, query, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/admin/user-profile/<path:email>', methods=['GET'])
@require_admin
def admin_user_profile(email):
    """Return full profile for one user: account info, orders, wishlist, top searched products."""
    conn = get_db_connection()

    # 1. Account info
    user_row = conn.execute(
        'SELECT id, name, email, phone FROM users WHERE email = ?', (email,)
    ).fetchone()
    user_info = dict(user_row) if user_row else {'email': email, 'name': email.split('@')[0].capitalize(), 'phone': '—'}

    # 2. Orders for this user
    order_rows = conn.execute(
        'SELECT id, items, total, address, payment, payment_id, status, created_at FROM orders WHERE user_email = ? ORDER BY id DESC',
        (email,)
    ).fetchall()
    orders = [dict(r) for r in order_rows]

    # 3. Wishlist
    wish_row = conn.execute(
        'SELECT wishlist_data FROM wishlists WHERE user_email = ?', (email,)
    ).fetchone()
    wishlist_raw = {}
    if wish_row:
        try:
            wishlist_raw = json.loads(wish_row['wishlist_data'])
            if not isinstance(wishlist_raw, dict):
                wishlist_raw = {}
        except Exception:
            wishlist_raw = {}
    wishlist = [
        {'product_id': int(pid), 'qty': int(qty)}
        for pid, qty in wishlist_raw.items()
        if int(qty) > 0
    ]

    # 4. Most searched products (by search_logs)
    search_rows = conn.execute('''
        SELECT product_id, COUNT(*) as count
        FROM search_logs
        WHERE user_email = ?
        GROUP BY product_id
        ORDER BY count DESC
        LIMIT 10
    ''', (email,)).fetchall()
    top_searched = [{'product_id': r['product_id'], 'count': r['count']} for r in search_rows]

    # 5. Most viewed product pages
    view_rows = conn.execute('''
        SELECT product_id, COUNT(*) as count
        FROM product_views
        WHERE user_email = ?
        GROUP BY product_id
        ORDER BY count DESC
        LIMIT 10
    ''', (email,)).fetchall()
    top_viewed = [{'product_id': r['product_id'], 'count': r['count']} for r in view_rows]

    conn.close()
    return jsonify({
        'user': user_info,
        'orders': orders,
        'wishlist': wishlist,
        'top_searched': top_searched,
        'top_viewed': top_viewed,
    })


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
    data        = request.json
    user_email  = request.headers.get('User-Email')
    guest_email = data.get('guest_email')
    guest_name  = data.get('guest_name')
    items       = data.get('items', {})
    total       = data.get('total', 0)
    address     = data.get('address', '')
    payment     = data.get('payment', 'COD')

    # Use user_email if logged in, else fall back to guest_email
    stored_email = user_email or guest_email or 'guest'

    try:
        conn = get_db_connection()

        customer_name = guest_name or 'Customer'
        if user_email:
            row = conn.execute('SELECT name FROM users WHERE email = ?', (user_email,)).fetchone()
            if row:
                customer_name = row['name']

        cursor = conn.execute(
            'INSERT INTO orders (user_email, items, total, address, payment, payment_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (stored_email, json.dumps(items), total, address, payment, 'COD', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()

        confirm_email = user_email or data.get('confirm_email') or guest_email

        # Always notify the store; send customer email only if we have their address
        send_order_confirmation_email_async(
            to_email       = confirm_email,   # None for anonymous guests → only store notified
            customer_name  = customer_name,
            order_id       = order_id,
            items_dict     = items,
            total          = total,
            address        = address,
            payment_method = payment,
            payment_id     = None,            # COD — no Razorpay payment ID
        )

        return jsonify({"status": "success", "message": "Order placed!", "order_id": order_id})

    except Exception as e:
        print(f"Order Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_single_order(order_id):
    user_email = request.headers.get('User-Email')
    conn       = get_db_connection()
    order      = conn.execute(
        'SELECT * FROM orders WHERE id = ?', (order_id,)
    ).fetchone()
    conn.close()

    if not order:
        return jsonify({"error": "Order not found"}), 404

    order_dict = dict(order)
    # Allow access if user owns it OR if guest (no email header) and order belongs to 'guest'
    if user_email and order_dict.get('user_email') not in (user_email, 'guest'):
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify(order_dict)


@app.route('/api/orders/<int:order_id>/cancel', methods=['PATCH'])
def cancel_order(order_id):
    user_email = request.headers.get('User-Email')
    conn       = get_db_connection()
    order      = conn.execute(
        'SELECT * FROM orders WHERE id = ?', (order_id,)
    ).fetchone()

    if not order:
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    order_dict = dict(order)

    # Ownership check
    if user_email and order_dict.get('user_email') not in (user_email, 'guest'):
        conn.close()
        return jsonify({"error": "Unauthorized"}), 403

    # Business rule: can only cancel Confirmed or Processing orders
    if order_dict['status'] in ('Shipped', 'Delivered', 'Cancelled'):
        conn.close()
        return jsonify({
            "error": f"Cannot cancel an order that is already '{order_dict['status']}'"
        }), 400

    conn.execute(
        "UPDATE orders SET status = 'Cancelled' WHERE id = ?",
        (order_id,)
    )
    conn.commit()

    # ── Fetch customer name for the cancellation email ─────────────────────
    cancel_email = order_dict.get('user_email')
    customer_name = 'Customer'
    if cancel_email and cancel_email != 'guest':
        row = conn.execute('SELECT name FROM users WHERE email = ?', (cancel_email,)).fetchone()
        if row:
            customer_name = row['name']
    conn.close()

    # ── Send cancellation email in a background thread ─────────────────────
    import threading
    threading.Thread(
        target=send_order_status_update_email,
        args=(
            cancel_email if cancel_email != 'guest' else None,
            customer_name,
            order_id,
            'Cancelled',
            order_dict.get('items', '{}'),
            order_dict.get('total', 0),
            order_dict.get('address', ''),
        ),
        daemon=True
    ).start()

    return jsonify({"status": "success", "message": "Order cancelled successfully."})

# ══════════════════════════════════════════════════════════════════════════════
# ADDRESSES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/addresses', methods=['GET'])
def get_addresses():
    user_email = request.headers.get('User-Email')
    if not user_email:
        return jsonify([]), 400
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT * FROM addresses WHERE user_email = ? ORDER BY is_default DESC, id ASC',
        (user_email,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/addresses', methods=['POST'])
def add_address():
    user_email = request.headers.get('User-Email')
    if not user_email:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    conn = get_db_connection()

    # If new address is default, clear existing default first
    if data.get('is_default'):
        conn.execute(
            'UPDATE addresses SET is_default = 0 WHERE user_email = ?',
            (user_email,)
        )

    cursor = conn.execute(
        '''INSERT INTO addresses (user_email, label, name, street, city, state, zip, country, is_default)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            user_email,
            data.get('label', ''),
            data.get('name', ''),
            data.get('street', ''),
            data.get('city', ''),
            data.get('state', ''),
            data.get('zip', ''),
            data.get('country', 'India'),
            1 if data.get('is_default') else 0,
        )
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({'status': 'success', 'id': new_id})


@app.route('/api/addresses/<int:addr_id>', methods=['PUT'])
def update_address(addr_id):
    user_email = request.headers.get('User-Email')
    if not user_email:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    conn = get_db_connection()

    if data.get('is_default'):
        conn.execute(
            'UPDATE addresses SET is_default = 0 WHERE user_email = ?',
            (user_email,)
        )

    conn.execute(
        '''UPDATE addresses SET label=?, name=?, street=?, city=?, state=?, zip=?, country=?, is_default=?
           WHERE id=? AND user_email=?''',
        (
            data.get('label', ''),
            data.get('name', ''),
            data.get('street', ''),
            data.get('city', ''),
            data.get('state', ''),
            data.get('zip', ''),
            data.get('country', 'India'),
            1 if data.get('is_default') else 0,
            addr_id,
            user_email,
        )
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


@app.route('/api/addresses/<int:addr_id>', methods=['DELETE'])
def delete_address(addr_id):
    user_email = request.headers.get('User-Email')
    if not user_email:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    conn.execute(
        'DELETE FROM addresses WHERE id = ? AND user_email = ?',
        (addr_id, user_email)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


@app.route('/api/addresses/<int:addr_id>/default', methods=['PATCH'])
def set_default_address(addr_id):
    user_email = request.headers.get('User-Email')
    if not user_email:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    conn.execute(
        'UPDATE addresses SET is_default = 0 WHERE user_email = ?',
        (user_email,)
    )
    conn.execute(
        'UPDATE addresses SET is_default = 1 WHERE id = ? AND user_email = ?',
        (addr_id, user_email)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})
# ══════════════════════════════════════════════════════════════════════════════
# RAZORPAY
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/razorpay/create-order', methods=['POST'])
def create_razorpay_order():
    key_id     = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    print(f"DEBUG: create_razorpay_order called. Key ID: {key_id}")

    if not key_id or not key_secret:
        return jsonify({"error": "Payment gateway not configured"}), 500

    client = razorpay.Client(auth=(key_id, key_secret))
    data   = request.json
    amount = data.get('amount', 0)

    if not amount or amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    try:
        order = client.order.create({
            "amount":          int(round(amount * 100)),
            "currency":        "INR",
            "receipt":         f"receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "payment_capture": 1
        })
        print(f"DEBUG: Razorpay Order created successfully: {order['id']}")
        return jsonify({"id": order['id'], "amount": order['amount'], "currency": order['currency'], "key": key_id})
    except Exception as e:
        print(f"Razorpay Order Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/razorpay/verify', methods=['POST'])
def verify_razorpay_payment():
    data                = request.json
    user_email          = request.headers.get('User-Email')  # None for guests — that's fine
    razorpay_order_id   = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature  = data.get('razorpay_signature')
    items               = data.get('items', {})
    total               = data.get('total', 0)
    address             = data.get('address', '')
    payment_method      = data.get('method', 'Online')

    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    if not key_secret:
        return jsonify({"success": False, "error": "Payment gateway not configured. Set RAZORPAY_KEY_SECRET in .env"}), 500

    # ── Validate required fields ──
    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        return jsonify({"success": False, "error": "Missing payment verification fields"}), 400

    try:
        # ── FIXED: use hmac.new correctly ──
        message             = f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8')
        generated_signature = hmac.new(
            key_secret.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()

        if generated_signature != razorpay_signature:
            print(f"Signature mismatch.\nExpected: {generated_signature}\nGot: {razorpay_signature}")
            return jsonify({"success": False, "error": "Signature mismatch — payment not verified"}), 400

        conn     = get_db_connection()
        existing = conn.execute('SELECT id FROM orders WHERE payment_id = ?', (razorpay_payment_id,)).fetchone()
        if existing:
            conn.close()
            return jsonify({"success": True, "order_id": existing['id']})

        confirm_email = user_email or data.get('confirm_email') or data.get('email') or data.get('userEmail') or data.get('guest_email')
        stored_email  = confirm_email or user_email or 'guest'

        cursor = conn.execute(
            'INSERT INTO orders (user_email, items, total, address, payment, payment_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (
                stored_email,
                json.dumps(items),
                total,
                address,
                payment_method,
                razorpay_payment_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()

        customer_name = data.get('customer_name') or data.get('guest_name') or 'Customer'
        if confirm_email:
            conn2 = get_db_connection()
            row = conn2.execute('SELECT name FROM users WHERE email = ?', (confirm_email,)).fetchone()
            conn2.close()
            if row and row['name']:
                customer_name = row['name']

        # Always send — customer email only if available, store always notified
        send_order_confirmation_email_async(
            to_email       = confirm_email,
            customer_name  = customer_name,
            order_id       = order_id,
            items_dict     = items,
            total          = total,
            address        = address,
            payment_method = payment_method,
            payment_id     = razorpay_payment_id,
        )

        return jsonify({"success": True, "order_id": order_id})

    except Exception as e:
        print(f"Verification Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES  (protected by HTTP Basic Auth)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data     = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if username == ADMIN_USER and password == ADMIN_PASS:
        token = base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('utf-8')
        return jsonify({"status": "success", "token": token})

    return jsonify({"status": "error", "message": "Invalid admin credentials"}), 401

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


@app.route('/api/admin/orders/<int:order_id>/status', methods=['PUT', 'PATCH'])
@require_admin
def update_order_status(order_id):
    data           = request.json or {}
    new_status     = data.get('status')
    valid_statuses = ['Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled']

    if not new_status or new_status not in valid_statuses:
        return jsonify({"status": "error", "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    conn  = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        conn.close()
        return jsonify({"status": "error", "message": "Order not found"}), 404

    order_dict = dict(order)
    conn.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
    conn.commit()

    # ── Fetch customer name for the email ──────────────────────────────────
    customer_email = order_dict.get('user_email')
    customer_name  = 'Customer'
    if customer_email and customer_email != 'guest':
        row = conn.execute('SELECT name FROM users WHERE email = ?', (customer_email,)).fetchone()
        if row:
            customer_name = row['name']
    conn.close()

    # ── Send status-update email to customer ───────────────────────────────
    import threading
    threading.Thread(
        target=send_order_status_update_email,
        args=(
            customer_email if customer_email != 'guest' else None,
            customer_name,
            order_id,
            new_status,
            order_dict.get('items', '{}'),
            order_dict.get('total', 0),
            order_dict.get('address', ''),
        ),
        daemon=True
    ).start()

    return jsonify({"status": "success", "message": f"Order #{order_id} status updated to {new_status}"})



@app.route('/api/admin/users', methods=['GET'])
@require_admin
def get_all_users():
    conn = get_db_connection()
    # 1. Registered users from database
    db_users = conn.execute('SELECT id, name, email, phone FROM users').fetchall()
    users_list = []
    seen_emails = set()

    for u in db_users:
        u_dict = dict(u)
        u_dict['type'] = 'Registered User'
        users_list.append(u_dict)
        if u_dict.get('email'):
            seen_emails.add(u_dict['email'].lower())

    # 2. Customers who placed orders (direct checkout or guest)
    order_users = conn.execute(
        'SELECT DISTINCT user_email FROM orders WHERE user_email IS NOT NULL AND user_email != "guest"'
    ).fetchall()

    for ou in order_users:
        email = (ou['user_email'] or '').strip().lower()
        if email and email not in seen_emails:
            seen_emails.add(email)
            users_list.append({
                'id': len(users_list) + 1,
                'name': email.split('@')[0].capitalize(),
                'email': ou['user_email'],
                'phone': '—',
                'type': 'Order Customer'
            })

    conn.close()
    return jsonify({"users": users_list})


@app.route('/api/admin/analytics/wishlists', methods=['GET'])
@require_admin
def admin_analytics_wishlists():
    """Return per-user wishlist breakdown and aggregate wishlist count per product."""
    conn = get_db_connection()
    rows = conn.execute('SELECT user_email, wishlist_data FROM wishlists').fetchall()
    conn.close()

    product_counts = {}   # product_id -> count (users who wishlisted it)
    user_wishlists = []   # [{email, items: [{id, qty}]}]

    for row in rows:
        email = row['user_email']
        try:
            data = json.loads(row['wishlist_data'])
        except Exception:
            data = {}

        # wishlist_data is stored as {product_id: qty} dict or [] empty list
        if not isinstance(data, dict):
            data = {}

        wishlisted_products = []
        for pid, qty in data.items():
            try:
                qty_int = int(qty)
                if qty_int > 0:
                    pid_int = int(pid)
                    wishlisted_products.append({'product_id': pid_int, 'qty': qty_int})
                    product_counts[pid_int] = product_counts.get(pid_int, 0) + 1
            except Exception:
                continue

        if wishlisted_products:
            user_wishlists.append({'email': email, 'items': wishlisted_products})

    # Sort aggregate by count descending
    top_products = sorted(
        [{'product_id': pid, 'wishlist_count': cnt} for pid, cnt in product_counts.items()],
        key=lambda x: x['wishlist_count'],
        reverse=True
    )

    return jsonify({
        'user_wishlists': user_wishlists,
        'top_wishlisted': top_products
    })


@app.route('/api/admin/analytics/views', methods=['GET'])
@require_admin
def admin_analytics_views():
    """Return top viewed products and per-user view counts."""
    conn = get_db_connection()

    # Top 20 most viewed products
    top_rows = conn.execute('''
        SELECT product_id, COUNT(*) as view_count
        FROM product_views
        GROUP BY product_id
        ORDER BY view_count DESC
        LIMIT 20
    ''').fetchall()

    # Unique visitor count per product (distinct emails)
    unique_rows = conn.execute('''
        SELECT product_id, COUNT(DISTINCT user_email) as unique_users
        FROM product_views
        GROUP BY product_id
        ORDER BY unique_users DESC
        LIMIT 20
    ''').fetchall()

    unique_map = {r['product_id']: r['unique_users'] for r in unique_rows}

    top_products = [
        {
            'product_id': r['product_id'],
            'view_count': r['view_count'],
            'unique_users': unique_map.get(r['product_id'], 0)
        }
        for r in top_rows
    ]

    conn.close()
    return jsonify({'top_viewed': top_products})


# ══════════════════════════════════════════════════════════════════════════════
# SERVE REACT APP
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def serve():
    try:
        return send_from_directory('static', 'index.html')
    except Exception as e:
        print(f"Error serving index.html: {e}")
        return {"error": str(e)}, 500

@app.route('/<path:path>')
def static_files(path):
    try:
        return send_from_directory('static', path)
    except Exception as e:
        print(f"Error serving {path}: {e}")
        return {"error": str(e)}, 500


if __name__ == '__main__':
    app.run(debug=True, port=8000)