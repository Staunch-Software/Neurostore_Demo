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
        "softwareType": "AI Software",
        "family": "PDF Editor",
        "term": "1 Year",
        "brand": "Foxit",
        "image": "/Foxit PDF Editor.png",
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
            "Software Type": "AI Software",
            "License Type": "Digital License (Instant Activation)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows 11 / 10, macOS 12+, Web, iOS & Android",
            "AI Capabilities": "AI Document Summarizer, Smart Chat, Rewrite & Translate",
            "Editing Tools": "Full Text & Object Editing, Headers, Footers, Watermarks",
            "OCR Engine": "Multilingual Optical Character Recognition (Editable/Searchable)",
            "File Formats": "PDF, PDF/A, Word (.docx), Excel (.xlsx), PPTX, HTML, RTF, Images",
            "Security & Compliance": "256-bit AES Encryption, Permanent Redaction, RMS & HIPAA Compliant",
            "E-Signature": "Built-in Foxit eSign & Certified Digital Signatures",
            "Support & Updates": "24/7 Priority Support, Documentation & Free Version Updates"
        },
        "warranty": "1 Year Official Foxit Software Assurance & Enterprise Technical Support."
    },
    {
        "id": 2,
        "name": "Access LTSC 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Access LTSC 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/access.svg",
        "price": 14145,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Rapid relational database creation with rich templates",
            "Visual query builder and automated SQL formulation",
            "Customizable reports with dynamic data aggregation",
            "Integration with SQL Server and external ODBC data sources"
        ],
        "shortDescription": "Access LTSC 2024 lets you build and share a database in seconds.",
        "description": "Access LTSC 2024 lets you build and share a database in seconds. You supply the information and Access does the rest, making it easy to create and structure your data. Reports and queries put your data into the format you want, so your applications consistently look great.",
        "additionalInfo": {
            "Product Edition": "Access LTSC 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN5J:0002",
            "Product ID": "1741774",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Access LTSC 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b914,145.21",
            "List Price": "\u20b914,443.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 3,
        "name": "BizTalk Server 2020 Branch",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "BizTalk Server 2020 Branch",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/biztalk.svg",
        "price": 94106,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise Application Integration (EAI) and B2B communication hub",
            "Seamlessly connect disparate legacy on-prem systems with cloud APIs",
            "High-throughput message routing, transformation and durable transactions",
            "Over 25+ enterprise adapters including SAP, Oracle, SQL, IBM MQ and AS2"
        ],
        "shortDescription": "This specialty version of BizTalk Server is designed for hub and spoke deployment scenarios.",
        "description": "This specialty version of BizTalk Server is designed for hub and spoke deployment scenarios.",
        "additionalInfo": {
            "Product Edition": "BizTalk Server 2020 Branch",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0G49Z:0002",
            "Product ID": "1213143",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "BizTalk Server 2020 Branch",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2020",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b994,105.52",
            "List Price": "\u20b9107,391.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 4,
        "name": "BizTalk Server 2020 Enterprise",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "BizTalk Server 2020 Enterprise",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/biztalk.svg",
        "price": 1646410,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise Application Integration (EAI) and B2B communication hub",
            "Seamlessly connect disparate legacy on-prem systems with cloud APIs",
            "High-throughput message routing, transformation and durable transactions",
            "Over 25+ enterprise adapters including SAP, Oracle, SQL, IBM MQ and AS2"
        ],
        "shortDescription": "For those with enterprise-level requirements for high volume, reliability, and availability.",
        "description": "For those with enterprise-level requirements for high volume, reliability, and availability.",
        "additionalInfo": {
            "Product Edition": "BizTalk Server 2020 Enterprise",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0G49X:0001",
            "Product ID": "1213147",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "BizTalk Server 2020 Enterprise",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2020",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b91,646,409.69",
            "List Price": "\u20b91,878,844.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 5,
        "name": "BizTalk Server 2020 Standard",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "BizTalk Server 2020 Standard",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/biztalk.svg",
        "price": 377467,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise Application Integration (EAI) and B2B communication hub",
            "Seamlessly connect disparate legacy on-prem systems with cloud APIs",
            "High-throughput message routing, transformation and durable transactions",
            "Over 25+ enterprise adapters including SAP, Oracle, SQL, IBM MQ and AS2"
        ],
        "shortDescription": "For organizations with moderate volume and deployment scale requirements.",
        "description": "For organizations with moderate volume and deployment scale requirements.",
        "additionalInfo": {
            "Product Edition": "BizTalk Server 2020 Standard",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0G49W:0002",
            "Product ID": "1213151",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "BizTalk Server 2020 Standard",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2020",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9377,466.60",
            "List Price": "\u20b9430,756.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 6,
        "name": "ESU for SQL 2014 EE 2 Core pack for 1st year EOS (Coverage July 9 2025 - July 14 2026)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for SQL Server",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 1125858,
        "badge": "Security Updates (ESU)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 EE 2 Core pack for 1st year EOS (Coverage July 9 2025 - July 14 2026)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000J",
            "Product ID": "1613059",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b91,125,858.30",
            "List Price": "\u20b91,284,803.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 7,
        "name": "ESU for SQL 2014 EE 2 Core pack for 2nd year EOS (Coverage July 9 2025 - July 14 2026)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for SQL Server",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 1125858,
        "badge": "Security Updates (ESU)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 EE 2 Core pack for 2nd year EOS (Coverage July 9 2025 - July 14 2026)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000W",
            "Product ID": "1613059",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b91,125,858.30",
            "List Price": "\u20b91,284,803.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 8,
        "name": "ESU for SQL 2014 EE 2 Core pack for 3rd year EOS (Coverage July 15 2026 - July 14 2027)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for SQL Server",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 1125858,
        "badge": "Security Updates (ESU)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 EE 2 Core pack for 3rd year EOS (Coverage July 15 2026 - July 14 2027)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000Q",
            "Product ID": "1613059",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b91,125,858.30",
            "List Price": "\u20b91,284,803.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 9,
        "name": "ESU for SQL 2014 EE Per Server for 1st year EOS(Coverage July 9 2025 - July 14 2026)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for SQL Server",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 703553,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 EE Per Server for 1st year EOS(Coverage July 9 2025 - July 14 2026)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000L",
            "Product ID": "1613059",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9703,552.89",
            "List Price": "\u20b9802,878.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 10,
        "name": "ESU for SQL 2014 EE Per Server for 2nd year EOS (Coverage July 9 2025 - July 14 2026)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for SQL Server",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 703553,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 EE Per Server for 2nd year EOS (Coverage July 9 2025 - July 14 2026)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000Z",
            "Product ID": "1613059",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9703,552.89",
            "List Price": "\u20b9802,878.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 11,
        "name": "ESU for SQL 2014 EE Per Server for 3rd year EOS (Coverage July 15 2026 - July 14 2027)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for SQL Server",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 703553,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 EE Per Server for 3rd year EOS (Coverage July 15 2026 - July 14 2027)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000X",
            "Product ID": "1613059",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9703,552.89",
            "List Price": "\u20b9802,878.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 12,
        "name": "ESU for SQL 2014 Std 2 Core pack for 1st year EOS (Coverage July 9 2025 - July 14 2026)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for SQL Server",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 293676,
        "badge": "Security Updates (ESU)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 Std 2 Core pack for 1st year EOS (Coverage July 9 2025 - July 14 2026)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000K",
            "Product ID": "1613059",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9293,675.88",
            "List Price": "\u20b9335,136.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 13,
        "name": "ESU for SQL 2014 Std 2 Core pack for 2nd year EOS (Coverage July 9 2025 - July 14 2026)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for SQL Server",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 293676,
        "badge": "Security Updates (ESU)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 Std 2 Core pack for 2nd year EOS (Coverage July 9 2025 - July 14 2026)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000S",
            "Product ID": "1613059",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9293,675.88",
            "List Price": "\u20b9335,136.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 14,
        "name": "ESU for SQL 2014 Std 2 Core pack for 3rd year EOS (Coverage July 15 2026 - July 14 2027)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for SQL Server",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 293676,
        "badge": "Security Updates (ESU)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 Std 2 Core pack for 3rd year EOS (Coverage July 15 2026 - July 14 2027)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000R",
            "Product ID": "1613059",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9293,675.88",
            "List Price": "\u20b9335,136.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 15,
        "name": "ESU for SQL 2014 Std Per Server for 1st year EOS (Coverage July 9 2025 - July 14 2026)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for SQL Server",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 73419,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 Std Per Server for 1st year EOS (Coverage July 9 2025 - July 14 2026)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000H",
            "Product ID": "1613059",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b973,418.97",
            "List Price": "\u20b983,784.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 16,
        "name": "ESU for SQL 2014 Std Per Server for 2nd year EOS (Coverage July 9 2025 - July 14 2026)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for SQL Server",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 73419,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 Std Per Server for 2nd year EOS (Coverage July 9 2025 - July 14 2026)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000T",
            "Product ID": "1613059",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b973,418.97",
            "List Price": "\u20b983,784.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 17,
        "name": "ESU for SQL 2014 Std Per Server for 3rd year EOS (Coverage July 15 2026 - July 14 2027)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for SQL Server",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 73419,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 Std Per Server for 3rd year EOS (Coverage July 15 2026 - July 14 2027)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000V",
            "Product ID": "1613059",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b973,418.97",
            "List Price": "\u20b983,784.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 18,
        "name": "ESU for SQL 2016 EE 2 Core pack Year 1 (July 15 2026 - July 14 2027)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 1125858,
        "badge": "Security Updates (ESU)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2016 EE 2 Core pack Year 1 (July 15 2026 - July 14 2027)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZTC0F:000C",
            "Product ID": "1894302",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b91,125,858.30",
            "List Price": "\u20b91,284,803.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 19,
        "name": "ESU for SQL 2016 EE 2 Core pack Year 2 (July 15 2027 - July 14 2028)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 1125858,
        "badge": "Security Updates (ESU)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2016 EE 2 Core pack Year 2 (July 15 2027 - July 14 2028)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZTC0F:0007",
            "Product ID": "1894302",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b91,125,858.30",
            "List Price": "\u20b91,284,803.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 20,
        "name": "ESU for SQL 2016 EE 2 Core pack Year 3 (July 15 2028 - July 14 2029)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 1125858,
        "badge": "Security Updates (ESU)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2016 EE 2 Core pack Year 3 (July 15 2028 - July 14 2029)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZTC0F:0004",
            "Product ID": "1894302",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b91,125,858.30",
            "List Price": "\u20b91,284,803.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 21,
        "name": "ESU for SQL 2016 EE Per Server Year 1 (July 15 2026 - July 14 2027)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 703553,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2016 EE Per Server Year 1 (July 15 2026 - July 14 2027)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZTC0F:0002",
            "Product ID": "1894302",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9703,552.89",
            "List Price": "\u20b9802,878.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 22,
        "name": "ESU for SQL 2016 EE Per Server Year 2 (July 15 2027 - July 14 2028)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 703553,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2016 EE Per Server Year 2 (July 15 2027 - July 14 2028)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZTC0F:0001",
            "Product ID": "1894302",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9703,552.89",
            "List Price": "\u20b9802,878.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 23,
        "name": "ESU for SQL 2016 EE Per Server Year 3 (July 15 2028 - July 14 2029)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 703553,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2016 EE Per Server Year 3 (July 15 2028 - July 14 2029)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZTC0F:0008",
            "Product ID": "1894302",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9703,552.89",
            "List Price": "\u20b9802,878.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 24,
        "name": "ESU for SQL 2016 Std 2 Core pack Year 1 (July 15 2026 - July 14 2027)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 293676,
        "badge": "Security Updates (ESU)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2016 Std 2 Core pack Year 1 (July 15 2026 - July 14 2027)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZTC0F:000D",
            "Product ID": "1894302",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9293,675.88",
            "List Price": "\u20b9335,136.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 25,
        "name": "ESU for SQL 2016 Std 2 Core pack Year 2 (July 15 2027 - July 14 2028)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 293676,
        "badge": "Security Updates (ESU)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2016 Std 2 Core pack Year 2 (July 15 2027 - July 14 2028)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZTC0F:0003",
            "Product ID": "1894302",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9293,675.88",
            "List Price": "\u20b9335,136.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 26,
        "name": "ESU for SQL 2016 Std 2 Core pack Year 3 (July 15 2028 - July 14 2029)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 293676,
        "badge": "Security Updates (ESU)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2016 Std 2 Core pack Year 3 (July 15 2028 - July 14 2029)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZTC0F:0005",
            "Product ID": "1894302",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9293,675.88",
            "List Price": "\u20b9335,136.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 27,
        "name": "ESU for SQL 2016 Std Per Server Year 1 (July 15 2026 - July 14 2027)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 73419,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2016 Std Per Server Year 1 (July 15 2026 - July 14 2027)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZTC0F:0006",
            "Product ID": "1894302",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b973,418.97",
            "List Price": "\u20b983,784.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 28,
        "name": "ESU for SQL 2016 Std Per Server Year 2 (July 15 2027 - July 14 2028)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 73419,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2016 Std Per Server Year 2 (July 15 2027 - July 14 2028)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZTC0F:000B",
            "Product ID": "1894302",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b973,418.97",
            "List Price": "\u20b983,784.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 29,
        "name": "ESU for SQL 2016 Std Per Server Year 3 (July 15 2028 - July 14 2029)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 73419,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2016 Std Per Server Year 3 (July 15 2028 - July 14 2029)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZTC0F:0009",
            "Product ID": "1894302",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b973,418.97",
            "List Price": "\u20b983,784.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 30,
        "name": "Excel LTSC 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Excel LTSC 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/excel.svg",
        "price": 14145,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "High-performance calculation engine with dynamic array formulas",
            "Advanced data visualization, PivotTables and Power Query tools",
            "Standardized enterprise format with cross-platform compatibility",
            "Perpetual one-time purchase with complete offline capability"
        ],
        "shortDescription": "Excel LTSC 2024 helps you to analyze and visualize data more powerfully with new capabilities including Dynamic Charts with Dynamic Arrays, 14 new Text and Array functions, and a new Accessibility Rib...",
        "description": "Excel LTSC 2024 helps you to analyze and visualize data more powerfully with new capabilities including Dynamic Charts with Dynamic Arrays, 14 new Text and Array functions, and a new Accessibility Ribbon to make it easier to create spreadsheets that more people can use. Excel LTSC 2024 also includes improved speed and performance when multiple workbooks are open.",
        "additionalInfo": {
            "Product Edition": "Excel LTSC 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN5H:0002",
            "Product ID": "1741773",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Excel LTSC 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b914,145.21",
            "List Price": "\u20b914,443.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 31,
        "name": "Excel LTSC for Mac 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Excel LTSC for Mac 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/excel.svg",
        "price": 14145,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "High-performance calculation engine with dynamic array formulas",
            "Advanced data visualization, PivotTables and Power Query tools",
            "Standardized enterprise format with cross-platform compatibility",
            "Perpetual one-time purchase with complete offline capability"
        ],
        "shortDescription": "Excel LTSC for Mac 2024 helps you to analyze and visualize data more powerfully with new capabilities including Dynamic Charts with Dynamic Arrays, 14 new Text and Array functions, and a new Accessibi...",
        "description": "Excel LTSC for Mac 2024 helps you to analyze and visualize data more powerfully with new capabilities including Dynamic Charts with Dynamic Arrays, 14 new Text and Array functions, and a new Accessibility Ribbon to make it easier to create spreadsheets that more people can use. Excel LTSC for Mac 2024 also includes improved speed and performance when multiple workbooks are open.",
        "additionalInfo": {
            "Product Edition": "Excel LTSC for Mac 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN5G:0001",
            "Product ID": "1741772",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Excel LTSC for Mac 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b914,145.21",
            "List Price": "\u20b914,443.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 32,
        "name": "Exchange Server Enterprise 2019 Device CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Exchange Server Enterprise CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/exchange.svg",
        "price": 3499,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "Exchange Server Enterprise 2019 Device CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4MD:0005",
            "Product ID": "1271444",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Exchange Server Enterprise CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b93,499.02",
            "List Price": "\u20b93,993.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 33,
        "name": "Exchange Server Enterprise 2019 User CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Exchange Server Enterprise CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/exchange.svg",
        "price": 4466,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "Exchange Server Enterprise 2019 User CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4MD:0004",
            "Product ID": "1271444",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Exchange Server Enterprise CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b94,466.44",
            "List Price": "\u20b95,097.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 34,
        "name": "Exchange Server Standard 2019 Device CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Exchange Server Standard CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/exchange.svg",
        "price": 5584,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "Exchange Server Standard 2019 Device CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4MB:0005",
            "Product ID": "1271442",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Exchange Server Standard CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b95,583.71",
            "List Price": "\u20b96,372.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 35,
        "name": "Exchange Server Standard 2019 User CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Exchange Server Standard CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/exchange.svg",
        "price": 7221,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "Exchange Server Standard 2019 User CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4MB:0004",
            "Product ID": "1271442",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Exchange Server Standard CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b97,221.49",
            "List Price": "\u20b98,241.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 36,
        "name": "Office LTSC Professional Plus 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Office LTSC Professional Plus 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/office.svg",
        "price": 50254,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Complete productivity suite: Word, Excel, PowerPoint, Outlook, OneNote",
            "LTSC edition for mission-critical offline and regulated workstations",
            "One-time perpetual purchase with volume license deployment tools",
            "Enterprise security, telemetry controls and group policy support"
        ],
        "shortDescription": "Office LTSC Professional Plus 2024 gives you the tools to get work done with updated versions of Word, Excel, PowerPoint, Outlook, and Access (PC only); plus a OneNote desktop app that runs on all sup...",
        "description": "Office LTSC Professional Plus 2024 gives you the tools to get work done with updated versions of Word, Excel, PowerPoint, Outlook, and Access (PC only); plus a OneNote desktop app that runs on all supported versions of Windows and which is part of Office LTSC and Microsoft 365. (features vary: https://support.microsoft.com/en-us/office/what-s-the-difference-between-the-onenote-versions-a624e692-b78b-4c09-b07f-46181958118f?ui=en-US&rs=en-US&ad=US)",
        "additionalInfo": {
            "Product Edition": "Office LTSC Professional Plus 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN5F:0002",
            "Product ID": "1741771",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Office LTSC Professional Plus 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b950,254.28",
            "List Price": "\u20b957,349.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 37,
        "name": "Office LTSC Standard 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Office LTSC Standard 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/office.svg",
        "price": 36820,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Complete productivity suite: Word, Excel, PowerPoint, Outlook, OneNote",
            "LTSC edition for mission-critical offline and regulated workstations",
            "One-time perpetual purchase with volume license deployment tools",
            "Enterprise security, telemetry controls and group policy support"
        ],
        "shortDescription": "Office LTSC Standard 2024 gives you the essential tools to get work done with updated versions of Word, Excel, PowerPoint, and Outlook; plus a OneNote desktop app that runs on all supported versions o...",
        "description": "Office LTSC Standard 2024 gives you the essential tools to get work done with updated versions of Word, Excel, PowerPoint, and Outlook; plus a OneNote desktop app that runs on all supported versions of Windows and which is part of Office LTSC and Microsoft 365. (features vary: https://support.microsoft.com/en-us/office/what-s-the-difference-between-the-onenote-versions-a624e692-b78b-4c09-b07f-46181958118f?ui=en-US&rs=en-US&ad=US)",
        "additionalInfo": {
            "Product Edition": "Office LTSC Standard 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN5D:0002",
            "Product ID": "1741770",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Office LTSC Standard 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b936,820.03",
            "List Price": "\u20b942,056.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 38,
        "name": "Office LTSC Standard for Mac 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Office LTSC Standard for Mac 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/office.svg",
        "price": 36853,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Complete productivity suite: Word, Excel, PowerPoint, Outlook, OneNote",
            "LTSC edition for mission-critical offline and regulated workstations",
            "One-time perpetual purchase with volume license deployment tools",
            "Enterprise security, telemetry controls and group policy support"
        ],
        "shortDescription": "Office LTSC Standard for Mac 2024 gives you the essential tools to get work done with updated versions of Word, Excel, PowerPoint, OneNote and Outlook.",
        "description": "Office LTSC Standard for Mac 2024 gives you the essential tools to get work done with updated versions of Word, Excel, PowerPoint, OneNote and Outlook.",
        "additionalInfo": {
            "Product Edition": "Office LTSC Standard for Mac 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN5C:0001",
            "Product ID": "1741769",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Office LTSC Standard for Mac 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b936,853.20",
            "List Price": "\u20b942,056.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 39,
        "name": "Outlook LTSC 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Outlook LTSC 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/outlook.svg",
        "price": 14145,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Unified enterprise email, calendar, contact and task management",
            "Advanced spam filtering, phishing protection and encryption",
            "Delegated calendar access and scheduling assistant",
            "Commercial LTSC perpetual license with offline cache"
        ],
        "shortDescription": "Outlook LTSC 2024 helps you communicate and collaborate more easily with new capabilities like Reactions, Suggested replies, the ability to set working hours and location, and improvements to search f...",
        "description": "Outlook LTSC 2024 helps you communicate and collaborate more easily with new capabilities like Reactions, Suggested replies, the ability to set working hours and location, and improvements to search functionality and accessibility.",
        "additionalInfo": {
            "Product Edition": "Outlook LTSC 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN5V:0001",
            "Product ID": "1741775",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Outlook LTSC 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b914,145.21",
            "List Price": "\u20b914,443.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 40,
        "name": "Outlook LTSC for Mac 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Outlook LTSC for Mac 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/outlook.svg",
        "price": 14145,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Unified enterprise email, calendar, contact and task management",
            "Advanced spam filtering, phishing protection and encryption",
            "Delegated calendar access and scheduling assistant",
            "Commercial LTSC perpetual license with offline cache"
        ],
        "shortDescription": "Outlook LTSC for Mac 2024 helps you communicate and collaborate more easily with new capabilities like Reactions, Suggested replies, the ability to set working hours and location, and improvements to ...",
        "description": "Outlook LTSC for Mac 2024 helps you communicate and collaborate more easily with new capabilities like Reactions, Suggested replies, the ability to set working hours and location, and improvements to search functionality and accessibility.",
        "additionalInfo": {
            "Product Edition": "Outlook LTSC for Mac 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN5W:0001",
            "Product ID": "1741776",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Outlook LTSC for Mac 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b914,145.21",
            "List Price": "\u20b914,443.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 41,
        "name": "PowerPoint LTSC 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "PowerPoint LTSC 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/powerpoint.svg",
        "price": 14145,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Professional slide design with cinematic transitions and animations",
            "Presenter View, teleprompter notes and interactive laser pointer",
            "Export to ultra-high-definition 4K video and vector formats",
            "Perpetual commercial license for enterprise presentations"
        ],
        "shortDescription": "PowerPoint LTSC 2024 helps you create compelling content with the addition of capabilities like PowerPoint Cameo, Recording Studio, closed captions for video and audio, and integration of Stream 2.",
        "description": "PowerPoint LTSC 2024 helps you create compelling content with the addition of capabilities like PowerPoint Cameo, Recording Studio, closed captions for video and audio, and integration of Stream 2.0 and FlipGrid content.",
        "additionalInfo": {
            "Product Edition": "PowerPoint LTSC 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN47:0001",
            "Product ID": "1741768",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "PowerPoint LTSC 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b914,145.21",
            "List Price": "\u20b914,443.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 42,
        "name": "PowerPoint LTSC for Mac 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "PowerPoint LTSC for Mac 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/powerpoint.svg",
        "price": 14145,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Professional slide design with cinematic transitions and animations",
            "Presenter View, teleprompter notes and interactive laser pointer",
            "Export to ultra-high-definition 4K video and vector formats",
            "Perpetual commercial license for enterprise presentations"
        ],
        "shortDescription": "PowerPoint LTSC for Mac 2024 helps you create compelling content with the addition of capabilities like PowerPoint Cameo, Recording Studio, closed captions for video and audio, and integration of Stream 2.",
        "description": "PowerPoint LTSC for Mac 2024 helps you create compelling content with the addition of capabilities like PowerPoint Cameo, Recording Studio, closed captions for video and audio, and integration of Stream 2.0 and FlipGrid content.",
        "additionalInfo": {
            "Product Edition": "PowerPoint LTSC for Mac 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN46:0002",
            "Product ID": "1741767",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "PowerPoint LTSC for Mac 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b914,145.21",
            "List Price": "\u20b914,443.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 43,
        "name": "Project Professional 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Project Professional 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/project.svg",
        "price": 84129,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Comprehensive Gantt charts, scheduling and resource allocation",
            "Critical path calculation, baseline tracking and earned value analysis",
            "Built-in customizable reporting dashboards and status summaries",
            "Commercial perpetual license for project and portfolio managers"
        ],
        "shortDescription": "Project Professional 2024 enables you to deliver projects successfully by keeping your projects, resources, and teams organized and focused.",
        "description": "Project Professional 2024 enables you to deliver projects successfully by keeping your projects, resources, and teams organized and focused. Plan projects, track status efficiently, and communicate in the moment by hovering over other team members' names in a project plan to see online presence and start chats or calls through Microsoft Teams. Sync Project schedules and plans easily with Project Online and Project Server 2024. Project Professional 2024 is compatible with all versions of Office LTSC 2024. Microsoft Teams, Microsoft Office, Project Online, and Project Server 2024 are sold separately.",
        "additionalInfo": {
            "Product Edition": "Project Professional 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN45:0001",
            "Product ID": "1741766",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Project Professional 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b984,128.97",
            "List Price": "\u20b996,006.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 44,
        "name": "Project Server 2019",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Project Server 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/project.svg",
        "price": 463978,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Comprehensive Gantt charts, scheduling and resource allocation",
            "Critical path calculation, baseline tracking and earned value analysis",
            "Built-in customizable reporting dashboards and status summaries",
            "Commercial perpetual license for project and portfolio managers"
        ],
        "shortDescription": "Project Server 2019 offers a robust end-to-end project and portfolio management solution, with strong collaboration capabilities powered by SharePoint Server 2019.",
        "description": "Project Server 2019 offers a robust end-to-end project and portfolio management solution, with strong collaboration capabilities powered by SharePoint Server 2019. Updates include enhancements to performance and scalability, improved reporting, and an expanded set of APIs.",
        "additionalInfo": {
            "Product Edition": "Project Server 2019",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4MH:0003",
            "Product ID": "1213156",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Project Server 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9463,978.20",
            "List Price": "\u20b9529,481.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 45,
        "name": "Project Server 2019 Device CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Project Server CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/project.svg",
        "price": 13847,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Comprehensive Gantt charts, scheduling and resource allocation",
            "Critical path calculation, baseline tracking and earned value analysis",
            "Built-in customizable reporting dashboards and status summaries",
            "Commercial perpetual license for project and portfolio managers"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "Project Server 2019 Device CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4LF:0003",
            "Product ID": "1213159",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Project Server CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b913,847.11",
            "List Price": "\u20b915,802.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 46,
        "name": "Project Server 2019 User CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Project Server CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/project.svg",
        "price": 18016,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Comprehensive Gantt charts, scheduling and resource allocation",
            "Critical path calculation, baseline tracking and earned value analysis",
            "Built-in customizable reporting dashboards and status summaries",
            "Commercial perpetual license for project and portfolio managers"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "Project Server 2019 User CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4LF:0001",
            "Product ID": "1213159",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Project Server CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b918,016.49",
            "List Price": "\u20b920,560.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 47,
        "name": "Project Standard 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Project Standard 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/project.svg",
        "price": 50627,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Comprehensive Gantt charts, scheduling and resource allocation",
            "Critical path calculation, baseline tracking and earned value analysis",
            "Built-in customizable reporting dashboards and status summaries",
            "Commercial perpetual license for project and portfolio managers"
        ],
        "shortDescription": "Project Standard 2024 helps you stay organized in visually engaging ways to get started quickly, track project tasks more efficiently, and deliver your projects on time.",
        "description": "Project Standard 2024 helps you stay organized in visually engaging ways to get started quickly, track project tasks more efficiently, and deliver your projects on time. Use powerful, out-of-the-box reporting tools to quickly measure progress and communicate project details. Project Standard 2024 is compatible with Office LTSC Standard 2024.",
        "additionalInfo": {
            "Product Edition": "Project Standard 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN44:0001",
            "Product ID": "1741765",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Project Standard 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b950,626.70",
            "List Price": "\u20b957,774.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 48,
        "name": "Rights Management Services (RMS) 2025 CAL- 1 User",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows Rights Management Services CAL 2025",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 4749,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "additionalInfo": {
            "Product Edition": "Rights Management Services (RMS) 2025 CAL- 1 User",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHF:0006",
            "Product ID": "1752048",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows Rights Management Services CAL 2025",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b94,749.48",
            "List Price": "\u20b95,420.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 49,
        "name": "Rights Management Services (RMS) 2025 CAL-1 Device",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows Rights Management Services CAL 2025",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 3685,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "additionalInfo": {
            "Product Edition": "Rights Management Services (RMS) 2025 CAL-1 Device",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHF:0005",
            "Product ID": "1752048",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows Rights Management Services CAL 2025",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b93,684.79",
            "List Price": "\u20b94,205.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 50,
        "name": "SQL Server 2025 - 1 Device CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2025 CAL",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/sqlserver.svg",
        "price": 17116,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Industry-leading relational database performance and In-Memory OLTP",
            "Always On Availability Groups for high availability and disaster recovery",
            "Transparent Data Encryption (TDE) and Always Encrypted data protection",
            "Built-in machine learning, Big Data cluster and analytics connectivity"
        ],
        "shortDescription": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have.",
        "description": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have. Standard edition offers a full-featured database with extensive scale for mid-tier applications.",
        "additionalInfo": {
            "Product Edition": "SQL Server 2025 - 1 Device CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0VNHV:0001",
            "Product ID": "1880687",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2025 CAL",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b917,115.67",
            "List Price": "\u20b919,532.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 51,
        "name": "SQL Server 2025 - 1 User CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2025 CAL",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/sqlserver.svg",
        "price": 17116,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Industry-leading relational database performance and In-Memory OLTP",
            "Always On Availability Groups for high availability and disaster recovery",
            "Transparent Data Encryption (TDE) and Always Encrypted data protection",
            "Built-in machine learning, Big Data cluster and analytics connectivity"
        ],
        "shortDescription": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have.",
        "description": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have. Standard edition offers a full-featured database with extensive scale for mid-tier applications.",
        "additionalInfo": {
            "Product Edition": "SQL Server 2025 - 1 User CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0VNHV:0002",
            "Product ID": "1880687",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2025 CAL",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b917,115.67",
            "List Price": "\u20b919,532.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 52,
        "name": "SQL Server 2025 Enterprise core - 2 core License Pack",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2025 Enterprise - 2 core License Pack",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/sqlserver.svg",
        "price": 1125907,
        "badge": "Perpetual (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Industry-leading relational database performance and In-Memory OLTP",
            "Always On Availability Groups for high availability and disaster recovery",
            "Transparent Data Encryption (TDE) and Always Encrypted data protection",
            "Built-in machine learning, Big Data cluster and analytics connectivity"
        ],
        "shortDescription": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have.",
        "description": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have. Enterprise edition offers the highest performance and scalability for mission-critical workloads.",
        "additionalInfo": {
            "Product Edition": "SQL Server 2025 Enterprise core - 2 core License Pack",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0VNGX:0006",
            "Product ID": "1880691",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2025 Enterprise - 2 core License Pack",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b91,125,907.37",
            "List Price": "\u20b91,284,859.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 53,
        "name": "SQL Server 2025 Standard core - 2 core License Pack",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2025 Standard - 2 core License Pack",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/sqlserver.svg",
        "price": 293679,
        "badge": "Perpetual (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Industry-leading relational database performance and In-Memory OLTP",
            "Always On Availability Groups for high availability and disaster recovery",
            "Transparent Data Encryption (TDE) and Always Encrypted data protection",
            "Built-in machine learning, Big Data cluster and analytics connectivity"
        ],
        "shortDescription": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have.",
        "description": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have. Standard edition offers a full-featured database with extensive scale for mid-tier applications.",
        "additionalInfo": {
            "Product Edition": "SQL Server 2025 Standard core - 2 core License Pack",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0VNH2:0002",
            "Product ID": "1880693",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2025 Standard - 2 core License Pack",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9293,679.38",
            "List Price": "\u20b9335,140.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 54,
        "name": "SQL Server 2025 Standard edition Perpetual 1 Server License",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SQL Server 2025 Standard Edition",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/sqlserver.svg",
        "price": 73543,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Industry-leading relational database performance and In-Memory OLTP",
            "Always On Availability Groups for high availability and disaster recovery",
            "Transparent Data Encryption (TDE) and Always Encrypted data protection",
            "Built-in machine learning, Big Data cluster and analytics connectivity"
        ],
        "shortDescription": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have.",
        "description": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have. Standard edition offers a full-featured database with extensive scale for mid-tier applications.",
        "additionalInfo": {
            "Product Edition": "SQL Server 2025 Standard edition Perpetual 1 Server License",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0VNJS:0002",
            "Product ID": "1880692",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SQL Server 2025 Standard Edition",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b973,542.53",
            "List Price": "\u20b983,925.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 55,
        "name": "SharePoint Enterprise 2019 Device CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SharePoint Enterprise CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/sharepoint.svg",
        "price": 6849,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "SharePoint Enterprise 2019 Device CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4LV:0003",
            "Product ID": "1213169",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SharePoint Enterprise CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b96,849.07",
            "List Price": "\u20b97,816.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 56,
        "name": "SharePoint Enterprise 2019 User CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SharePoint Enterprise CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/sharepoint.svg",
        "price": 8934,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "SharePoint Enterprise 2019 User CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4LV:0002",
            "Product ID": "1213169",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SharePoint Enterprise CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b98,933.76",
            "List Price": "\u20b910,195.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 57,
        "name": "SharePoint Standard 2019 Device CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SharePoint Standard CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/sharepoint.svg",
        "price": 7891,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "SharePoint Standard 2019 Device CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4LS:0003",
            "Product ID": "1213174",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SharePoint Standard CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b97,890.98",
            "List Price": "\u20b99,005.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 58,
        "name": "SharePoint Standard 2019 User CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "SharePoint Standard CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/sharepoint.svg",
        "price": 10050,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "SharePoint Standard 2019 User CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4LS:0002",
            "Product ID": "1213174",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "SharePoint Standard CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b910,050.15",
            "List Price": "\u20b911,469.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 59,
        "name": "Skype for Business Server Enterprise 2019 Device CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Skype for Business Server Enterprise CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/skype.svg",
        "price": 8934,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "Skype for Business Server Enterprise 2019 Device CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4LP:0003",
            "Product ID": "1213146",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Skype for Business Server Enterprise CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b98,933.76",
            "List Price": "\u20b910,195.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 60,
        "name": "Skype for Business Server Enterprise 2019 User CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Skype for Business Server Enterprise CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/skype.svg",
        "price": 11540,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "Skype for Business Server Enterprise 2019 User CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4LP:0002",
            "Product ID": "1213146",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Skype for Business Server Enterprise CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b911,539.85",
            "List Price": "\u20b913,169.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 61,
        "name": "Skype for Business Server Plus 2019 Device CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Skype for Business Server Plus CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/skype.svg",
        "price": 8934,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "Skype for Business Server Plus 2019 Device CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4LN:0003",
            "Product ID": "1213150",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Skype for Business Server Plus CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b98,933.76",
            "List Price": "\u20b910,195.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 62,
        "name": "Skype for Business Server Plus 2019 User CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Skype for Business Server Plus CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/skype.svg",
        "price": 11540,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "Skype for Business Server Plus 2019 User CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4LN:0002",
            "Product ID": "1213150",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Skype for Business Server Plus CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b911,539.85",
            "List Price": "\u20b913,169.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 63,
        "name": "Skype for Business Server Standard 2019 Device CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Skype for Business Server Standard CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/skype.svg",
        "price": 2680,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "Skype for Business Server Standard 2019 Device CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4K1:0003",
            "Product ID": "1213155",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Skype for Business Server Standard CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b92,679.69",
            "List Price": "\u20b93,058.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 64,
        "name": "Skype for Business Server Standard 2019 User CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Skype for Business Server Standard CAL 2019",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/skype.svg",
        "price": 3425,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Authorized Client Access License (CAL) for Microsoft server products",
            "Available in Per-User or Per-Device licensing models for flexibility",
            "Enables legitimate, compliant connectivity to centralized server assets",
            "Perpetual commercial compliance for enterprise network infrastructure"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software. Please purchase the appropriate number of user and device CALs for each user or device that accesses the server.",
        "additionalInfo": {
            "Product Edition": "Skype for Business Server Standard 2019 User CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0F4K1:0002",
            "Product ID": "1213155",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Skype for Business Server Standard CAL 2019",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2019",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b93,424.54",
            "List Price": "\u20b93,908.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 65,
        "name": "Visio LTSC Professional 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Visio LTSC Professional 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/visio.svg",
        "price": 43181,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Extensive library of thousands of IT, flowchart, and engineering shapes",
            "Live data linking with Excel, Active Directory and SQL Server",
            "BPMN 2.0, UML 2.5 and IEEE compliance out-of-the-box",
            "Perpetual licensing for professional diagramming and architecture design"
        ],
        "shortDescription": "Visio Professional LTSC 2024 makes it easier than ever for individuals and teams to create and share professional, versatile diagrams that simplify complex information.",
        "description": "Visio Professional LTSC 2024 makes it easier than ever for individuals and teams to create and share professional, versatile diagrams that simplify complex information. It includes all of the functionality of Visio Standard LTSC 2024 as well as updated shapes, templates, and styles; enhanced support for team collaboration, including the ability for several people to work on a single diagram at the same time; and the ability to link diagrams to data instantly. Visio Professional LTSC 2024 also helps prevent information leakage by enabling Information Rights Management.",
        "additionalInfo": {
            "Product Edition": "Visio LTSC Professional 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN43:0002",
            "Product ID": "1741764",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Visio LTSC Professional 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b943,180.88",
            "List Price": "\u20b949,277.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 66,
        "name": "Visio LTSC Standard 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Visio LTSC Standard 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/visio.svg",
        "price": 23080,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Extensive library of thousands of IT, flowchart, and engineering shapes",
            "Live data linking with Excel, Active Directory and SQL Server",
            "BPMN 2.0, UML 2.5 and IEEE compliance out-of-the-box",
            "Perpetual licensing for professional diagramming and architecture design"
        ],
        "shortDescription": "Visio Standard LTSC 2024 designed for individuals who are looking for a powerful diagramming platform with a rich set of built-in stencils.",
        "description": "Visio Standard LTSC 2024 designed for individuals who are looking for a powerful diagramming platform with a rich set of built-in stencils. It helps users to simplify complex information through simple, easy-to-understand diagrams. Visio Standard includes stencils for business, basic network diagrams, organization charts, basic flowcharts, and general multi-purpose diagrams.",
        "additionalInfo": {
            "Product Edition": "Visio LTSC Standard 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN42:0002",
            "Product ID": "1741763",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Visio LTSC Standard 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b923,079.69",
            "List Price": "\u20b926,338.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 67,
        "name": "Visual Studio Professional 2026",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Visual Studio Professional 2026",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/visualstudio.svg",
        "price": 37150,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "State-of-the-art IDE for .NET, C++, Python, JavaScript and cloud apps",
            "IntelliCode AI-assisted code completions and refactoring",
            "Advanced cross-platform debugging, profiling and unit test runners",
            "Commercial software license with Azure integration and Git tooling"
        ],
        "shortDescription": "Visual Studio Professional 2026 is a stand-alone integrated development environment software.",
        "description": "Visual Studio Professional 2026 is a stand-alone integrated development environment software. It delivers a powerful suite of innovations to enhance the development experience for professional teams. Leading the way is the AI Profiler Agent, which brings expert-level performance diagnostics directly into the developer\u2019s workflow. The new Copilot Agent Mode enables a deeply contextual AI experience across chat, debugging, reviews, and documentation. Developers also benefit from blazing-fast performance, a refreshed Fluent UI for streamlined navigation, and enterprise-grade policy controls that give organizations precise management over extension usage. These enhancements make Visual Studio Professional a smart, responsive, and secure environment for building complex applications.",
        "additionalInfo": {
            "Product Edition": "Visual Studio Professional 2026",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0VJ96:0002",
            "Product ID": "1876739",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Visual Studio Professional 2026",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b937,150.26",
            "List Price": "\u20b942,395.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 68,
        "name": "Win Server DC Core Ext Security 2012 2 Core Y1 (October 2023-2024)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for Windows Server DC Core",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 57252,
        "badge": "Perpetual (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. This ESU can be applied to either WS 2012 or WS 2012 R2. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "Win Server DC Core Ext Security 2012 2 Core Y1 (October 2023-2024)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HPVW:0009",
            "Product ID": "1613062",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for Windows Server DC Core",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b957,252.32",
            "List Price": "\u20b965,335.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 69,
        "name": "Win Server DC Core Ext Security 2012 2 Core Y2 (October 2024-2025)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for Windows Server DC Core",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 57252,
        "badge": "Perpetual (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. This ESU can be applied to either WS 2012 or WS 2012 R2. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "Win Server DC Core Ext Security 2012 2 Core Y2 (October 2024-2025)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HPVW:0008",
            "Product ID": "1613062",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for Windows Server DC Core",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b957,252.32",
            "List Price": "\u20b965,335.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 70,
        "name": "Win Server DC Core Ext Security 2012 8 Core Y1 (October 2023-2024)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for Windows Server DC Core",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 229160,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. This ESU can be applied to either WS 2012 or WS 2012 R2. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "Win Server DC Core Ext Security 2012 8 Core Y1 (October 2023-2024)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HPVW:0006",
            "Product ID": "1613062",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for Windows Server DC Core",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9229,160.00",
            "List Price": "\u20b9261,512.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 71,
        "name": "Win Server DC Core Ext Security 2012 8 Core Y2 (October 2024-2025)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for Windows Server DC Core",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 229160,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. This ESU can be applied to either WS 2012 or WS 2012 R2. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "Win Server DC Core Ext Security 2012 8 Core Y2 (October 2024-2025)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HPVW:0007",
            "Product ID": "1613062",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for Windows Server DC Core",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9229,160.00",
            "List Price": "\u20b9261,512.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 72,
        "name": "Win Server Std Core Ext Security 2012 2 Core Y1 (October 2023-2024)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for Windows Server Standard Core",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 9976,
        "badge": "Perpetual (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. This ESU can be applied to either WS 2012 or WS 2012 R2. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "Win Server Std Core Ext Security 2012 2 Core Y1 (October 2023-2024)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HPVV:0007",
            "Product ID": "1613060",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for Windows Server Standard Core",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b99,975.67",
            "List Price": "\u20b911,384.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 73,
        "name": "Win Server Std Core Ext Security 2012 2 Core Y2 (October 2024-2025)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for Windows Server Standard Core",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 9976,
        "badge": "Perpetual (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. This ESU can be applied to either WS 2012 or WS 2012 R2. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "Win Server Std Core Ext Security 2012 2 Core Y2 (October 2024-2025)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HPVV:0006",
            "Product ID": "1613060",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for Windows Server Standard Core",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b99,975.67",
            "List Price": "\u20b911,384.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 74,
        "name": "Win Server Std Core Ext Security 2012 8 Core Y1 (October 2023-2024)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for Windows Server Standard Core",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 39756,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. This ESU can be applied to either WS 2012 or WS 2012 R2. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "Win Server Std Core Ext Security 2012 8 Core Y1 (October 2023-2024)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HPVV:0001",
            "Product ID": "1613060",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for Windows Server Standard Core",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b939,756.34",
            "List Price": "\u20b945,369.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 75,
        "name": "Win Server Std Core Ext Security 2012 8 Core Y2 (October 2024-2025)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Extended Security Updates for Windows Server Standard Core",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 39756,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. This ESU can be applied to either WS 2012 or WS 2012 R2. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "Win Server Std Core Ext Security 2012 8 Core Y2 (October 2024-2025)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HPVV:0008",
            "Product ID": "1613060",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Extended Security Updates for Windows Server Standard Core",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b939,756.34",
            "List Price": "\u20b945,369.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 76,
        "name": "Windows 10 ESU Year 1 (2025 - 2026)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 10 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 4541,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "Windows 10 Extended Security Updates (ESU) include security updates for critical and important issues as defined by Microsoft Security Response Center (MSRC).",
        "description": "Windows 10 Extended Security Updates (ESU) include security updates for critical and important issues as defined by Microsoft Security Response Center (MSRC). After October 2025, PCs running Windows 10 will require ESU in order to receive security updates. Windows 10 Cloud Managed ESU are on a per-device basis.",
        "additionalInfo": {
            "Product Edition": "Windows 10 ESU Year 1 (2025 - 2026)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0SSGZ:0004",
            "Product ID": "1837466",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 10 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b94,540.93",
            "List Price": "\u20b95,182.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 77,
        "name": "Windows 10 ESU Year 2 (2026 - 2027)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 10 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 9083,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "Windows 10 Extended Security Updates (ESU) include security updates for critical and important issues as defined by Microsoft Security Response Center (MSRC).",
        "description": "Windows 10 Extended Security Updates (ESU) include security updates for critical and important issues as defined by Microsoft Security Response Center (MSRC). After October 2025, PCs running Windows 10 will require ESU in order to receive security updates. Windows 10 Cloud Managed ESU are on a per-device basis.",
        "additionalInfo": {
            "Product Edition": "Windows 10 ESU Year 2 (2026 - 2027)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0SSGZ:0001",
            "Product ID": "1837466",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 10 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b99,082.73",
            "List Price": "\u20b910,365.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 78,
        "name": "Windows 10 ESU Year 3 (2027 - 2028)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 10 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 18165,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "Windows 10 Extended Security Updates (ESU) include security updates for critical and important issues as defined by Microsoft Security Response Center (MSRC).",
        "description": "Windows 10 Extended Security Updates (ESU) include security updates for critical and important issues as defined by Microsoft Security Response Center (MSRC). After October 2025, PCs running Windows 10 will require ESU in order to receive security updates. Windows 10 Cloud Managed ESU are on a per-device basis.",
        "additionalInfo": {
            "Product Edition": "Windows 10 ESU Year 3 (2027 - 2028)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0SSGZ:0002",
            "Product ID": "1837466",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 10 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b918,165.46",
            "List Price": "\u20b920,730.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 79,
        "name": "Windows 10 Enterprise LTSB 2016 ESU Year 1 (2026 - 2027)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 10 Enterprise LTSB 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 4541,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "Windows 10 Enterprise LTSB 2016 Extended Security Updates (ESU) include security updates for critical and important issues as defined by Microsoft Security Response Center (MSRC).",
        "description": "Windows 10 Enterprise LTSB 2016 Extended Security Updates (ESU) include security updates for critical and important issues as defined by Microsoft Security Response Center (MSRC). After October 2026, this product will no longer receive security updates, non-security updates, bug fixes, technical support, or online technical content updates unless enrolled in an ESU. These ESU programs are on a per-device basis.",
        "additionalInfo": {
            "Product Edition": "Windows 10 Enterprise LTSB 2016 ESU Year 1 (2026 - 2027)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZT98X:0003",
            "Product ID": "1894303",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 10 Enterprise LTSB 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b94,540.93",
            "List Price": "\u20b95,182.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 80,
        "name": "Windows 10 Enterprise LTSB 2016 ESU Year 2 (2027 - 2028)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 10 Enterprise LTSB 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 9083,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "Windows 10 Enterprise LTSB 2016 Extended Security Updates (ESU) include security updates for critical and important issues as defined by Microsoft Security Response Center (MSRC).",
        "description": "Windows 10 Enterprise LTSB 2016 Extended Security Updates (ESU) include security updates for critical and important issues as defined by Microsoft Security Response Center (MSRC). After October 2026, this product will no longer receive security updates, non-security updates, bug fixes, technical support, or online technical content updates unless enrolled in an ESU. These ESU programs are on a per-device basis.",
        "additionalInfo": {
            "Product Edition": "Windows 10 Enterprise LTSB 2016 ESU Year 2 (2027 - 2028)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZT98X:0002",
            "Product ID": "1894303",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 10 Enterprise LTSB 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b99,082.73",
            "List Price": "\u20b910,365.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 81,
        "name": "Windows 10 Enterprise LTSB 2016 ESU Year 3 (2028 - 2029)",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 10 Enterprise LTSB 2016 ESU",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 18165,
        "badge": "Security Updates (ESU)",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "Windows 10 Enterprise LTSB 2016 Extended Security Updates (ESU) include security updates for critical and important issues as defined by Microsoft Security Response Center (MSRC).",
        "description": "Windows 10 Enterprise LTSB 2016 Extended Security Updates (ESU) include security updates for critical and important issues as defined by Microsoft Security Response Center (MSRC). After October 2026, this product will no longer receive security updates, non-security updates, bug fixes, technical support, or online technical content updates unless enrolled in an ESU. These ESU programs are on a per-device basis.",
        "additionalInfo": {
            "Product Edition": "Windows 10 Enterprise LTSB 2016 ESU Year 3 (2028 - 2029)",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGDZT98X:0001",
            "Product ID": "1894303",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 10 Enterprise LTSB 2016 ESU",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2016",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b918,165.46",
            "List Price": "\u20b920,730.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 82,
        "name": "Windows 10 Enterprise LTSC 2021 Upgrade",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 10 Enterprise LTSC 2021 Upgrade",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windows10.svg",
        "price": 21962,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "Windows 10 Enterprise LTSC 2021 builds on Windows 10 Pro, version 21H2 adding premium features designed to address the needs of large and mid-size organizations (including large academic institutions)...",
        "description": "Windows 10 Enterprise LTSC 2021 builds on Windows 10 Pro, version 21H2 adding premium features designed to address the needs of large and mid-size organizations (including large academic institutions), such as advanced protection against modern security threats, full flexibility of OS deployment, updating and support options; as well as comprehensive device and app management and control capabilities. The LTSC edition provides customers with access to the Long-Term Servicing Channel as a deployment option for their special-purpose devices and environments. The LTSC edition will not be updated with any new features; features from Windows 10 that could be updated with new functionality (including Cortana and all in-box Universal Windows apps) are not included.",
        "additionalInfo": {
            "Product Edition": "Windows 10 Enterprise LTSC 2021 Upgrade",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0D19L:0001",
            "Product ID": "1386576",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 10 Enterprise LTSC 2021 Upgrade",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2021",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b921,962.42",
            "List Price": "\u20b925,063.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 83,
        "name": "Windows 10 Enterprise N LTSC 2021 Upgrade",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 10 Enterprise N LTSC 2021 Upgrade",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windows10.svg",
        "price": 21962,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "Windows 10 Enterprise N LTSC 2021 builds on Windows 10 Pro N, version 21H2 adding premium features designed to address the needs of large and mid-size organizations (including large academic instituti...",
        "description": "Windows 10 Enterprise N LTSC 2021 builds on Windows 10 Pro N, version 21H2 adding premium features designed to address the needs of large and mid-size organizations (including large academic institutions), such as advanced protection against modern security threats, full flexibility of OS deployment, updating and support options; as well as comprehensive device and app management and control capabilities. The LTSC edition provides customers with access to the Long-Term Servicing Channel as a deployment option for their special-purpose devices and environments. The LTSC edition will not be updated with any new features; features from Windows 10 that could be updated with new functionality (including Cortana and all in-box Universal Windows apps) are not included. Windows 10 Enterprise N LTSC 2021 includes the same functionality as Windows 10 Enterprise LTSC 2021, except that it does not include certain media related technologies (e.g., Windows Media Player, Camera, Music, Movies & TV) or the Skype app.",
        "additionalInfo": {
            "Product Edition": "Windows 10 Enterprise N LTSC 2021 Upgrade",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0D19M:0001",
            "Product ID": "1386577",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 10 Enterprise N LTSC 2021 Upgrade",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2021",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b921,962.42",
            "List Price": "\u20b925,063.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 84,
        "name": "Windows 10 IoT Enterprise LTSC 2021",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 10 IoT Enterprise LTSC 2021",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windows10.svg",
        "price": 21962,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "Windows IoT Enterprise LTSC is designed for use on fixed-function specialized devices and provides a 10-year support lifecycle.",
        "description": "Windows IoT Enterprise LTSC is designed for use on fixed-function specialized devices and provides a 10-year support lifecycle. Windows IoT Enterprise LTSC is a full version of Windows that delivers the same enterprise manageability and security capabilities that are found in Windows Enterprise. It shares all the benefits of the worldwide Windows ecosystem including the ability to use the same familiar development and management tools used for your enterprise PCs and laptops. The LTSC edition provides customers with access to the Long-Term Servicing channel as a deployment option for fixed-function specialized devices, which for Windows IoT Enterprise LTSC provides security updates for a full 10 years, however, does not include feature updates. Consumer features such as the Windows Store, and in-box consumer applications are not included in this edition. For more information about deploying Windows IoT Enterprise LTSC in your environment, see https://aka.ms/WinIoTinVL. System Requirements Processor: 1 Ghz or faster (for more information, see https://aka.ms/winiothw) Memory: 2 GB Drive Space: 20 GB available hard disk space Operating System: Windows 10 IoT Enterprise LTSC 2021, 64-bit",
        "additionalInfo": {
            "Product Edition": "Windows 10 IoT Enterprise LTSC 2021",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0H3RD:0002",
            "Product ID": "1597839",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 10 IoT Enterprise LTSC 2021",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "2021",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b921,962.42",
            "List Price": "\u20b925,063.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 85,
        "name": "Windows 11 Enterprise LTSC 2024 Upgrade",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 11 Enterprise LTSC 2024 Upgrade",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windows11.svg",
        "price": 21962,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "Windows 11 Enterprise LTSC 2024 builds on Windows 11 Enterprise, version 24H2 adding premium features designed to address the needs of large and mid-size organizations (including large academic instit...",
        "description": "Windows 11 Enterprise LTSC 2024 builds on Windows 11 Enterprise, version 24H2 adding premium features designed to address the needs of large and mid-size organizations (including large academic institutions), such as advanced protection against modern security threats, full flexibility of OS deployment, updating and support options; as well as comprehensive device and app management and control capabilities. The LTSC edition provides customers with access to the Long-Term Servicing Channel as a deployment option for their special-purpose devices and environments, with quality updates provided for a full 5 years.",
        "additionalInfo": {
            "Product Edition": "Windows 11 Enterprise LTSC 2024 Upgrade",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PP46:0002",
            "Product ID": "1757128",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 11 Enterprise LTSC 2024 Upgrade",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b921,962.42",
            "List Price": "\u20b925,063.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 86,
        "name": "Windows 11 Enterprise N LTSC 2024 Upgrade",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 11 Enterprise N LTSC 2024 Upgrade",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windows11.svg",
        "price": 21962,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "Windows 11 Enterprise N LTSC 2024 builds on Windows 11 Enterprise N, version 24H2 adding premium features designed to address the needs of large and mid-size organizations (including large academic in...",
        "description": "Windows 11 Enterprise N LTSC 2024 builds on Windows 11 Enterprise N, version 24H2 adding premium features designed to address the needs of large and mid-size organizations (including large academic institutions), such as advanced protection against modern security threats, full flexibility of OS deployment, updating and support options; as well as comprehensive device and app management and control capabilities. The LTSC edition provides customers with access to the Long-Term Servicing Channel as a deployment option for their special-purpose devices and environments, with quality updates provided for a full 5 years. Windows 11 Enterprise N LTSC 2024 includes the same functionality as Windows 11 Enterprise LTSC 2024, except that it does not include certain media related technologies (e.g., Windows Media Player, Camera, Music, Movies & TV) or the Skype app.",
        "additionalInfo": {
            "Product Edition": "Windows 11 Enterprise N LTSC 2024 Upgrade",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PP45:0002",
            "Product ID": "1757127",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 11 Enterprise N LTSC 2024 Upgrade",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b921,962.42",
            "List Price": "\u20b925,063.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 87,
        "name": "Windows 11 Home N to Pro N Upgrade for Microsoft 365 Business",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 11 Pro N",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windows11.svg",
        "price": 3648,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "All the features of Windows 11 Home plus enterprise-grade security, powerful management tools like BitLocker device encryption, and enhanced productivity with remote desktop.",
        "description": "All the features of Windows 11 Home plus enterprise-grade security, powerful management tools like BitLocker device encryption, and enhanced productivity with remote desktop. Licensed for 1 PC or Mac. Windows 11 Pro N includes the same functionality as Windows 11 Pro, except that it does not include certain media related technologies (e.g., Windows Media Player, Camera, Music, Movies & TV) or the Skype app. NOTE: Not all devices running Windows 10 are eligible to receive a Windows 11 upgrade. See the Windows 11 device specifications for upgrade requirements and supported features. Certain features require additional hardware. Installing Windows 11 media on a PC that does not meet the Windows 11 minimum system requirements is not recommended and may result in compatibility issues. If you proceed with installing Windows 11 on a PC that does not meet the requirements, that PC will no longer be supported and won't be entitled to receive updates. Damages to the PC due to lack of compatibility aren't covered under the manufacturer warranty.",
        "additionalInfo": {
            "Product Edition": "Windows 11 Home N to Pro N Upgrade for Microsoft 365 Business",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0D8H3:0002",
            "Product ID": "1371339",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 11 Pro N",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b93,647.99",
            "List Price": "\u20b94,163.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 88,
        "name": "Windows 11 Home to Pro Upgrade for Microsoft 365 Business",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 11 Pro",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windows11.svg",
        "price": 3648,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "All the features of Windows 11 Home plus enterprise-grade security, powerful management tools like BitLocker device encryption, and enhanced productivity with remote desktop.",
        "description": "All the features of Windows 11 Home plus enterprise-grade security, powerful management tools like BitLocker device encryption, and enhanced productivity with remote desktop. Licensed for 1 PC or Mac. NOTE: Not all devices running Windows 10 are eligible to receive a Windows 11 upgrade. See the Windows 11 device specifications for upgrade requirements and supported features. Certain features require additional hardware. Installing Windows 11 media on a PC that does not meet the Windows 11 minimum system requirements is not recommended and may result in compatibility issues. If you proceed with installing Windows 11 on a PC that does not meet the requirements, that PC will no longer be supported and won't be entitled to receive updates. Damages to the PC due to lack of compatibility aren't covered under the manufacturer warranty.",
        "additionalInfo": {
            "Product Edition": "Windows 11 Home to Pro Upgrade for Microsoft 365 Business",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0D8H4:0002",
            "Product ID": "1371342",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 11 Pro",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b93,647.99",
            "List Price": "\u20b94,163.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 89,
        "name": "Windows 11 IoT Enterprise LTSC 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 11 IoT Enterprise LTSC 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windows11.svg",
        "price": 21962,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "Windows 11 IoT Enterprise LTSC is designed for use on fixed-function specialized devices and provides a 10-year support lifecycle, which includes quality updates for a full 10 years.",
        "description": "Windows 11 IoT Enterprise LTSC is designed for use on fixed-function specialized devices and provides a 10-year support lifecycle, which includes quality updates for a full 10 years. It is a full version of Windows that delivers the same enterprise manageability and security capabilities that are found in Windows 11 Enterprise. It shares all the benefits of the worldwide Windows ecosystem including the ability to use the same familiar development and management tools used for your enterprise PCs and laptops. Consumer features such as the Windows Store, and in-box consumer applications are not included in this edition. For more information about deploying Windows 11 IoT Enterprise LTSC in your environment, see https://aka.ms/WinIoTinVL. System Requirements Processor: 1 Ghz or faster Memory: 4 GB Drive Space: 64 GB available hard disk space Operating System: Windows 11 IoT Enterprise LTSC 2024, 64-bit For more information about system requirements, see https://aka.ms/winiothw.",
        "additionalInfo": {
            "Product Edition": "Windows 11 IoT Enterprise LTSC 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PP49:0001",
            "Product ID": "1757129",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 11 IoT Enterprise LTSC 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b921,962.42",
            "List Price": "\u20b925,063.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 90,
        "name": "Windows 11 Pro N Upgrade",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 11 Pro N",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windows11.svg",
        "price": 13922,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "All the features of Windows 11 Home plus enterprise-grade security, powerful management tools like BitLocker device encryption, and enhanced productivity with remote desktop.",
        "description": "All the features of Windows 11 Home plus enterprise-grade security, powerful management tools like BitLocker device encryption, and enhanced productivity with remote desktop. Licensed for 1 PC or Mac. Windows 11 Pro N includes the same functionality as Windows 11 Pro, except that it does not include certain media related technologies (e.g., Windows Media Player, Camera, Music, Movies & TV) or the Skype app. NOTE: Not all devices running Windows 10 are eligible to receive a Windows 11 upgrade. See the Windows 11 device specifications for upgrade requirements and supported features. Certain features require additional hardware. Installing Windows 11 media on a PC that does not meet the Windows 11 minimum system requirements is not recommended and may result in compatibility issues. If you proceed with installing Windows 11 on a PC that does not meet the requirements, that PC will no longer be supported and won't be entitled to receive updates. Damages to the PC due to lack of compatibility aren't covered under the manufacturer warranty.",
        "additionalInfo": {
            "Product Edition": "Windows 11 Pro N Upgrade",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0D8H3:0004",
            "Product ID": "1371339",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 11 Pro N",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b913,921.60",
            "List Price": "\u20b915,887.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 91,
        "name": "Windows 11 Pro Upgrade",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 11 Pro",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windows11.svg",
        "price": 13922,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "All the features of Windows 11 Home plus enterprise-grade security, powerful management tools like BitLocker device encryption, and enhanced productivity with remote desktop.",
        "description": "All the features of Windows 11 Home plus enterprise-grade security, powerful management tools like BitLocker device encryption, and enhanced productivity with remote desktop. Licensed for 1 PC or Mac. NOTE: Not all devices running Windows 10 are eligible to receive a Windows 11 upgrade. See the Windows 11 device specifications for upgrade requirements and supported features. Certain features require additional hardware. Installing Windows 11 media on a PC that does not meet the Windows 11 minimum system requirements is not recommended and may result in compatibility issues. If you proceed with installing Windows 11 on a PC that does not meet the requirements, that PC will no longer be supported and won't be entitled to receive updates. Damages to the PC due to lack of compatibility aren't covered under the manufacturer warranty.",
        "additionalInfo": {
            "Product Edition": "Windows 11 Pro Upgrade",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0D8H4:0004",
            "Product ID": "1371342",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 11 Pro",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b913,921.60",
            "List Price": "\u20b915,887.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 92,
        "name": "Windows GGWA - Windows 11 Pro - Legalization Get Genuine",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 11 GGWA",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windows11.svg",
        "price": 13996,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "Get Genuine Windows (also known as \u201cGGWA\u201d) legalization solutions assist customers to convert non-genuine Windows operating systems to genuine, to remain compliant and encourage the purchase of genuin...",
        "description": "Get Genuine Windows (also known as \u201cGGWA\u201d) legalization solutions assist customers to convert non-genuine Windows operating systems to genuine, to remain compliant and encourage the purchase of genuine Windows pre-installed PCs in the future. GGWA is strictly to help a customer rectify a mis-licensing situation. Customers may acquire Get Genuine Windows licenses for the full version of the Windows desktop operating system for devices that require valid Windows licenses. Because Get Genuine Windows licenses are full licenses for Windows, they do not have a Qualifying OS requirement. Get Genuine Windows licenses are available only as a one-time purchase, where all units must be placed under a single order. Get Genuine Windows licenses may not be assigned to devices without a Qualifying OS if such devices are obtained after the customer\u2019s order.",
        "additionalInfo": {
            "Product Edition": "Windows GGWA - Windows 11 Pro - Legalization Get Genuine",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0L4TL:0003",
            "Product ID": "1425889",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 11 GGWA",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b913,996.08",
            "List Price": "\u20b915,972.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 93,
        "name": "Windows GGWA - Windows 11 Pro N - Legalization Get Genuine",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows 11 GGWA",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windows11.svg",
        "price": 13996,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise operating system with BitLocker, Windows Hello and SmartScreen",
            "LTSC edition offering long-term stability with 5-10 year support",
            "Zero unnecessary bloatware for mission-critical workstations and kiosks",
            "Full group policy management and Microsoft Intune readiness"
        ],
        "shortDescription": "Get Genuine Windows (also known as \u201cGGWA\u201d) legalization solutions assist customers to convert non-genuine Windows operating systems to genuine, to remain compliant and encourage the purchase of genuin...",
        "description": "Get Genuine Windows (also known as \u201cGGWA\u201d) legalization solutions assist customers to convert non-genuine Windows operating systems to genuine, to remain compliant and encourage the purchase of genuine Windows pre-installed PCs in the future. GGWA is strictly to help a customer rectify a mis-licensing situation. Customers may acquire Get Genuine Windows licenses for the full version of the Windows desktop operating system for devices that require valid Windows licenses. Because Get Genuine Windows licenses are full licenses for Windows, they do not have a Qualifying OS requirement. Get Genuine Windows licenses are available only as a one-time purchase, where all units must be placed under a single order. Get Genuine Windows licenses may not be assigned to devices without a Qualifying OS if such devices are obtained after the customer\u2019s order.",
        "additionalInfo": {
            "Product Edition": "Windows GGWA - Windows 11 Pro N - Legalization Get Genuine",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0L4TL:0001",
            "Product ID": "1425889",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows 11 GGWA",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b913,996.08",
            "List Price": "\u20b915,972.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 94,
        "name": "Windows Rights Management External Connector 2025",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows Server Rights Management External Connector",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 1492668,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Designed for computers to help protect access to and usage of information flowing through applications that use AD RMS on-premise and with Azure Information Protection.",
        "description": "Designed for computers to help protect access to and usage of information flowing through applications that use AD RMS on-premise and with Azure Information Protection.",
        "additionalInfo": {
            "Product Edition": "Windows Rights Management External Connector 2025",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0XCZ2:0001",
            "Product ID": "1809687",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows Server Rights Management External Connector",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b91,492,668.35",
            "List Price": "\u20b91,703,398.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 95,
        "name": "Windows Server 2025 - 1 Device CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows Server CAL 2025",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 2948,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses Windows Server.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses Windows Server.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 - 1 Device CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHT:0005",
            "Product ID": "1752047",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows Server CAL 2025",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b92,947.84",
            "List Price": "\u20b93,364.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 96,
        "name": "Windows Server 2025 - 1 User CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows Server CAL 2025",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 3767,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses Windows Server.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses Windows Server.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 - 1 User CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHT:0002",
            "Product ID": "1752047",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows Server CAL 2025",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b93,767.16",
            "List Price": "\u20b94,299.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 97,
        "name": "Windows Server 2025 Datacenter - 16 Core",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows Server Data Center Core 2025",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 504033,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2025 Datacenter is for highly virtualized datacenter and cloud environments, including shielded virtual machines, software-defined networking, storage spaces direct, and storage replication.",
        "description": "Windows Server 2025 Datacenter is for highly virtualized datacenter and cloud environments, including shielded virtual machines, software-defined networking, storage spaces direct, and storage replication.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Datacenter - 16 Core",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHD:0001",
            "Product ID": "1752049",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows Server Data Center Core 2025",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9504,033.35",
            "List Price": "\u20b9575,191.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 98,
        "name": "Windows Server 2025 Datacenter - 2 Core",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows Server Data Center Core 2025",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 63003,
        "badge": "Perpetual (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2025 Datacenter is for highly virtualized datacenter and cloud environments, including shielded virtual machines, software-defined networking, storage spaces direct, and storage replication.",
        "description": "Windows Server 2025 Datacenter is for highly virtualized datacenter and cloud environments, including shielded virtual machines, software-defined networking, storage spaces direct, and storage replication.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Datacenter - 2 Core",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHD:0004",
            "Product ID": "1752049",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows Server Data Center Core 2025",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b963,003.40",
            "List Price": "\u20b971,898.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 99,
        "name": "Windows Server 2025 External Connector",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows Server 2025 External Connector",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 181891,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "An External Connector license permits access by any number of external users, as long as that access is for the benefit of the licensee and not the external user.",
        "description": "An External Connector license permits access by any number of external users, as long as that access is for the benefit of the licensee and not the external user. Each physical server that external users access requires only one EC license. One can purchase individual CALs or an EC license for external users. This decision on whether to acquire CALs or an EC for external users is primarily a financial one. The right to run instances of the server software is licensed separately; the EC, like the CAL, simply permits access.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 External Connector",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0XCZ4:0001",
            "Product ID": "1809688",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows Server 2025 External Connector",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b9181,891.24",
            "List Price": "\u20b9207,570.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 100,
        "name": "Windows Server 2025 Remote Desktop Services - 1 Device CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows Server 2025 Remote Desktop Services",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 12954,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Remote Desktop Services enables users to access session-based desktops, virtual machine-based desktops, or applications in the data center from both within a corporate network and from the Internet.",
        "description": "Remote Desktop Services enables users to access session-based desktops, virtual machine-based desktops, or applications in the data center from both within a corporate network and from the Internet.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Remote Desktop Services - 1 Device CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHB:0001",
            "Product ID": "1752050",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows Server 2025 Remote Desktop Services",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b912,954.18",
            "List Price": "\u20b914,783.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 101,
        "name": "Windows Server 2025 Remote Desktop Services - 1 User CAL",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows Server 2025 Remote Desktop Services",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 12954,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Remote Desktop Services enables users to access session-based desktops, virtual machine-based desktops, or applications in the data center from both within a corporate network and from the Internet.",
        "description": "Remote Desktop Services enables users to access session-based desktops, virtual machine-based desktops, or applications in the data center from both within a corporate network and from the Internet.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Remote Desktop Services - 1 User CAL",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHB:0004",
            "Product ID": "1752050",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows Server 2025 Remote Desktop Services",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b912,954.18",
            "List Price": "\u20b914,783.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 102,
        "name": "Windows Server 2025 Remote Desktop Services External Connector - License 1",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows Remote Desktop External Connector 2025",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 1300540,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Remote Desktop Services helps securely connect remote users from managed or unmanaged devices.",
        "description": "Remote Desktop Services helps securely connect remote users from managed or unmanaged devices.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Remote Desktop Services External Connector - License 1",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHS:0001",
            "Product ID": "1757130",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows Remote Desktop External Connector 2025",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b91,300,540.31",
            "List Price": "\u20b91,484,146.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 103,
        "name": "Windows Server 2025 Standard - 16 Core License Pack",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows Server Standard Core 2025",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 84928,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2025 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "description": "Windows Server 2025 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Standard - 16 Core License Pack",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHC:0003",
            "Product ID": "1752051",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows Server Standard Core 2025",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b984,927.75",
            "List Price": "\u20b999,915.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 104,
        "name": "Windows Server 2025 Standard - 2 Core",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Windows Server Standard Core 2025",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 10974,
        "badge": "Perpetual (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2025 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "description": "Windows Server 2025 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Standard - 2 Core",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHC:0006",
            "Product ID": "1752051",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Windows Server Standard Core 2025",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b910,973.76",
            "List Price": "\u20b912,523.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 105,
        "name": "Word LTSC 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Word LTSC 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/word.svg",
        "price": 14145,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "LTSC Long-Term Servicing Release with guaranteed stability",
            "Advanced formatting, modern typography and layout tools",
            "Seamless collaboration, co-authoring and PDF reflow support",
            "Perpetual commercial deployment rights with zero recurring fees"
        ],
        "shortDescription": "Word LTSC 2024 enables you to create compelling content more confidently with Document Recovery and updated themes.",
        "description": "Word LTSC 2024 enables you to create compelling content more confidently with Document Recovery and updated themes.",
        "additionalInfo": {
            "Product Edition": "Word LTSC 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN41:0002",
            "Product ID": "1741762",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Word LTSC 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b914,145.21",
            "List Price": "\u20b914,443.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 106,
        "name": "Word LTSC for Mac 2024",
        "category": "Software",
        "softwareType": "Perpetual Software",
        "family": "Word LTSC for Mac 2024",
        "term": "Perpetual",
        "brand": "Microsoft",
        "image": "/products/word.svg",
        "price": 14145,
        "badge": "Perpetual License",
        "moq": "Per user",
        "features": [
            "LTSC Long-Term Servicing Release with guaranteed stability",
            "Advanced formatting, modern typography and layout tools",
            "Seamless collaboration, co-authoring and PDF reflow support",
            "Perpetual commercial deployment rights with zero recurring fees"
        ],
        "shortDescription": "Word LTSC for Mac 2024 enables you to create compelling content more confidently with Document Recovery and updated themes.",
        "description": "Word LTSC for Mac 2024 enables you to create compelling content more confidently with Document Recovery and updated themes.",
        "additionalInfo": {
            "Product Edition": "Word LTSC for Mac 2024",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PN40:0001",
            "Product ID": "1741761",
            "Software Type": "Perpetual Software",
            "Product Type": "Perpetual Software",
            "Family": "Word LTSC for Mac 2024",
            "Agreement": "Microsoft CSP Perpetual Software",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "Perpetual",
            "Purchase Unit": "Per user/",
            "Purchase Price": "\u20b914,145.21",
            "List Price": "\u20b914,443.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Perpetual Software)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 107,
        "name": "Azure SQL Edge - 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Azure SQL Edge",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/azuresql.svg",
        "price": 7445,
        "badge": "1-Year Subscription",
        "moq": "Per useryear",
        "features": [
            "Optimized SQL engine for IoT and edge edge compute architectures",
            "Built-in streaming, time-series data handling and machine learning graph",
            "Native offline operation with cloud synchronization to Azure",
            "Commercial subscription with Microsoft enterprise support"
        ],
        "shortDescription": "Running on ARM and Intel architecture, Azure SQL Edge brings the most secure Microsoft SQL engine to the edge.",
        "description": "Running on ARM and Intel architecture, Azure SQL Edge brings the most secure Microsoft SQL engine to the edge. This productivity tool for edge computing combines new capabilities such as data streaming and time series with in-database machine learning and graph features. Develop your application once and deploy anywhere across the edge, your datacenter, and Azure.",
        "additionalInfo": {
            "Product Edition": "Azure SQL Edge - 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0GJC2:0003",
            "Product ID": "1254677",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Azure SQL Edge",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b97,444.95",
            "List Price": "\u20b98,496.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 108,
        "name": "Azure SQL Edge - 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Azure SQL Edge",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/azuresql.svg",
        "price": 13401,
        "badge": "3-Year Subscription",
        "moq": "Per user3 years",
        "features": [
            "Optimized SQL engine for IoT and edge edge compute architectures",
            "Built-in streaming, time-series data handling and machine learning graph",
            "Native offline operation with cloud synchronization to Azure",
            "Commercial subscription with Microsoft enterprise support"
        ],
        "shortDescription": "Running on ARM and Intel architecture, Azure SQL Edge brings the most secure Microsoft SQL engine to the edge.",
        "description": "Running on ARM and Intel architecture, Azure SQL Edge brings the most secure Microsoft SQL engine to the edge. This productivity tool for edge computing combines new capabilities such as data streaming and time series with in-database machine learning and graph features. Develop your application once and deploy anywhere across the edge, your datacenter, and Azure.",
        "additionalInfo": {
            "Product Edition": "Azure SQL Edge - 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0GJC2:0001",
            "Product ID": "1254677",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Azure SQL Edge",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b913,401.08",
            "List Price": "\u20b915,293.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 109,
        "name": "ESU for SQL 2014 EE 2 Core pack for 2nd Year EOS (Coverage July 9 2025 - July 14 2026) - OneTime",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Extended Security Updates for SQL Server",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 1125858,
        "badge": "Security Updates (ESU)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 EE 2 Core pack for 2nd Year EOS (Coverage July 9 2025 - July 14 2026) - OneTime",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000G",
            "Product ID": "1613059",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b91,125,858.30",
            "List Price": "\u20b91,284,803.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 110,
        "name": "ESU for SQL 2014 EE Per Server for 2nd Year EOS(Coverage July 9 2025 - July 14 2026) - OneTime",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Extended Security Updates for SQL Server",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 703553,
        "badge": "Security Updates (ESU)",
        "moq": "Per useryear",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 EE Per Server for 2nd Year EOS(Coverage July 9 2025 - July 14 2026) - OneTime",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000M",
            "Product ID": "1613059",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b9703,552.89",
            "List Price": "\u20b9802,878.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 111,
        "name": "ESU for SQL 2014 Std 2 Core pack for 2nd Year EOS (Coverage July 9 2025 - July 14 2026) - OneTime",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Extended Security Updates for SQL Server",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 293676,
        "badge": "Security Updates (ESU)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 Std 2 Core pack for 2nd Year EOS (Coverage July 9 2025 - July 14 2026) - OneTime",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000P",
            "Product ID": "1613059",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b9293,675.88",
            "List Price": "\u20b9335,136.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 112,
        "name": "ESU for SQL 2014 Std Per Server for 2nd Year EOS (Coverage July 9 2025 - July 14 2026) - OneTime",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Extended Security Updates for SQL Server",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 73419,
        "badge": "Security Updates (ESU)",
        "moq": "Per useryear",
        "features": [
            "Official Microsoft Extended Security Updates (ESU)",
            "Critical security vulnerability patches past End of Support",
            "Compliance protection for enterprise database environments",
            "Automated delivery via WSUS and Azure Arc integration"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "ESU for SQL 2014 Std Per Server for 2nd Year EOS (Coverage July 9 2025 - July 14 2026) - OneTime",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HX95:000N",
            "Product ID": "1613059",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Extended Security Updates for SQL Server",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b973,418.97",
            "List Price": "\u20b983,784.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 113,
        "name": "SQL Server 2022 Enterprise - 2 Core License Pack - 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "SQL Server Enterprise Core 2022",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/sqlserver.svg",
        "price": 531768,
        "badge": "1 Year (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Industry-leading relational database performance and In-Memory OLTP",
            "Always On Availability Groups for high availability and disaster recovery",
            "Transparent Data Encryption (TDE) and Always Encrypted data protection",
            "Built-in machine learning, Big Data cluster and analytics connectivity"
        ],
        "shortDescription": "SQL Server 2022 enterprise edition is built for mission critical workloads with unlimited cores of CPU and memory.",
        "description": "SQL Server 2022 enterprise edition is built for mission critical workloads with unlimited cores of CPU and memory. It enables you to gain intelligence over all your data both structured and unstructured by combining the power of the new Big Data Clusters capability with enhanced data virtualization. These powerful additions to the product enable enterprises to not only store and query big data at scale, but also combine it with customer data wherever it may reside (SQL Server, Oracle, Mongo, PostgreSQL etc.). SQL Server also includes built-in AI capabilities to enable a comprehensive analytics and AI solution for all a company\u2019s data needs.",
        "additionalInfo": {
            "Product Edition": "SQL Server 2022 Enterprise - 2 Core License Pack - 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0M7XV:0002",
            "Product ID": "1543997",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "SQL Server Enterprise Core 2022",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "2022",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b9531,767.89",
            "List Price": "\u20b9606,841.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 114,
        "name": "SQL Server 2025 Enterprise - 2 core License Pack - 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "SQL Server 2025 Enterprise - 2 core License Pack",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/sqlserver.svg",
        "price": 531768,
        "badge": "1 Year (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Industry-leading relational database performance and In-Memory OLTP",
            "Always On Availability Groups for high availability and disaster recovery",
            "Transparent Data Encryption (TDE) and Always Encrypted data protection",
            "Built-in machine learning, Big Data cluster and analytics connectivity"
        ],
        "shortDescription": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have.",
        "description": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have. Enterprise edition offers the highest performance and scalability for mission-critical workloads.",
        "additionalInfo": {
            "Product Edition": "SQL Server 2025 Enterprise - 2 core License Pack - 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0VNGX:0002",
            "Product ID": "1880691",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "SQL Server 2025 Enterprise - 2 core License Pack",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b9531,767.89",
            "List Price": "\u20b9606,841.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 115,
        "name": "SQL Server 2025 Enterprise - 2 core License Pack - 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "SQL Server 2025 Enterprise - 2 core License Pack",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/sqlserver.svg",
        "price": 1335070,
        "badge": "3 Years (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Industry-leading relational database performance and In-Memory OLTP",
            "Always On Availability Groups for high availability and disaster recovery",
            "Transparent Data Encryption (TDE) and Always Encrypted data protection",
            "Built-in machine learning, Big Data cluster and analytics connectivity"
        ],
        "shortDescription": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have.",
        "description": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have. Enterprise edition offers the highest performance and scalability for mission-critical workloads.",
        "additionalInfo": {
            "Product Edition": "SQL Server 2025 Enterprise - 2 core License Pack - 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0VNGX:0005",
            "Product ID": "1880691",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "SQL Server 2025 Enterprise - 2 core License Pack",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b91,335,070.46",
            "List Price": "\u20b91,523,551.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 116,
        "name": "SQL Server 2025 Standard - 2 core License Pack - 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "SQL Server 2025 Standard - 2 core License Pack",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/sqlserver.svg",
        "price": 138702,
        "badge": "1 Year (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Industry-leading relational database performance and In-Memory OLTP",
            "Always On Availability Groups for high availability and disaster recovery",
            "Transparent Data Encryption (TDE) and Always Encrypted data protection",
            "Built-in machine learning, Big Data cluster and analytics connectivity"
        ],
        "shortDescription": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have.",
        "description": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have. Standard edition offers a full-featured database with extensive scale for mid-tier applications.",
        "additionalInfo": {
            "Product Edition": "SQL Server 2025 Standard - 2 core License Pack - 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0VNH2:0003",
            "Product ID": "1880693",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "SQL Server 2025 Standard - 2 core License Pack",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b9138,702.47",
            "List Price": "\u20b9158,284.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 117,
        "name": "SQL Server 2025 Standard - 2 core License Pack - 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "SQL Server 2025 Standard - 2 core License Pack",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/sqlserver.svg",
        "price": 348386,
        "badge": "3 Years (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Industry-leading relational database performance and In-Memory OLTP",
            "Always On Availability Groups for high availability and disaster recovery",
            "Transparent Data Encryption (TDE) and Always Encrypted data protection",
            "Built-in machine learning, Big Data cluster and analytics connectivity"
        ],
        "shortDescription": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have.",
        "description": "Building on SQL Server\u2019s foundation of best-in-class security, performance, and availability, SQL Server 2025 accelerates secure, scalable AI application development using data customers already have. Standard edition offers a full-featured database with extensive scale for mid-tier applications.",
        "additionalInfo": {
            "Product Edition": "SQL Server 2025 Standard - 2 core License Pack - 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0VNH2:0006",
            "Product ID": "1880693",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "SQL Server 2025 Standard - 2 core License Pack",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b9348,386.08",
            "List Price": "\u20b9397,570.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 118,
        "name": "SQL Server Big Data Node Cores - 1 Year Subscription - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "SQL Server Big Data Node Cores",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/sqlserver.svg",
        "price": 27844,
        "badge": "1-Year Subscription",
        "moq": "Per useryear",
        "features": [
            "Industry-leading relational database performance and In-Memory OLTP",
            "Always On Availability Groups for high availability and disaster recovery",
            "Transparent Data Encryption (TDE) and Always Encrypted data protection",
            "Built-in machine learning, Big Data cluster and analytics connectivity"
        ],
        "shortDescription": "SQL Server Big Data Clusters consists of a SQL Server master pool, powered by the SQL Server 2019 Enterprise or Standard Edition database engine on Linux, and Big Data Nodes which are worker nodes tha...",
        "description": "SQL Server Big Data Clusters consists of a SQL Server master pool, powered by the SQL Server 2019 Enterprise or Standard Edition database engine on Linux, and Big Data Nodes which are worker nodes that integrate Apache Spark and components of Apache Hadoop with the SQL Server engine to provide scale-out compute and storage.",
        "additionalInfo": {
            "Product Edition": "SQL Server Big Data Node Cores - 1 Year Subscription - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0FKZX:0003",
            "Product ID": "1148682",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "SQL Server Big Data Node Cores",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b927,844.07",
            "List Price": "\u20b931,775.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 119,
        "name": "SQL Server Big Data Node Cores - 1 Year Subscription - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "SQL Server Big Data Node Cores",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/sqlserver.svg",
        "price": 27844,
        "badge": "1-Year Subscription",
        "moq": "Per useryear",
        "features": [
            "Industry-leading relational database performance and In-Memory OLTP",
            "Always On Availability Groups for high availability and disaster recovery",
            "Transparent Data Encryption (TDE) and Always Encrypted data protection",
            "Built-in machine learning, Big Data cluster and analytics connectivity"
        ],
        "shortDescription": "Big Data Clusters gives you the ability to combine structured and unstructured data  in SQL Server with the power Apache Spark\u2122 and HDFS built in to the SQL Server engine to gain transformative insights from your data.",
        "description": "Big Data Clusters gives you the ability to combine structured and unstructured data  in SQL Server with the power Apache Spark\u2122 and HDFS built in to the SQL Server engine to gain transformative insights from your data.  As a SA benefit, Big Data Clusters is included in the SQL Server 2019 Enterprise and Standard editions.",
        "additionalInfo": {
            "Product Edition": "SQL Server Big Data Node Cores - 1 Year Subscription - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0FKZX:0003",
            "Product ID": "1148682",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "SQL Server Big Data Node Cores",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b927,844.07",
            "List Price": "\u20b931,775.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 120,
        "name": "SQL Server Standard 2022- 2 Core License Pack - 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "SQL Server Standard Core 2022",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/sqlserver.svg",
        "price": 138702,
        "badge": "1 Year (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Industry-leading relational database performance and In-Memory OLTP",
            "Always On Availability Groups for high availability and disaster recovery",
            "Transparent Data Encryption (TDE) and Always Encrypted data protection",
            "Built-in machine learning, Big Data cluster and analytics connectivity"
        ],
        "shortDescription": "SQL Server 2022 standard edition is for mid-tier applications and data marts with up to 24 cores of CPU and 128 GBs of memory.",
        "description": "SQL Server 2022 standard edition is for mid-tier applications and data marts with up to 24 cores of CPU and 128 GBs of memory. It enables you to gain intelligence over all your data both structured and unstructured by combining the power of the new Big Data Clusters capability with enhanced data virtualization. These powerful additions to the product enable enterprises to not only store and query big data at scale, but also combine it with customer data wherever it may reside (SQL Server, Oracle, Mongo, PostgreSQL etc.). SQL Server also includes built-in AI capabilities to enable a comprehensive analytics and AI solution for all a company\u2019s data needs.",
        "additionalInfo": {
            "Product Edition": "SQL Server Standard 2022- 2 Core License Pack - 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0M7XW:0004",
            "Product ID": "1543998",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "SQL Server Standard Core 2022",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "2022",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b9138,702.47",
            "List Price": "\u20b9158,284.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 121,
        "name": "System Center 2025 Datacenter - 2 Core License Pack 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "System Center 2025 Datacenter",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/systemcenter.svg",
        "price": 11630,
        "badge": "1 Year (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Comprehensive datacenter management for hybrid cloud environments",
            "Virtual Machine Manager (VMM) for Hyper-V and private cloud fabric",
            "Operations Manager (SCOM) for deep infrastructure monitoring and alerting",
            "Configuration Manager and Data Protection Manager integration"
        ],
        "shortDescription": "Microsoft System Center (SC) 2025 Datacenter brings cloud learnings to the datacenter, enabling seamless management of complex environments.",
        "description": "Microsoft System Center (SC) 2025 Datacenter brings cloud learnings to the datacenter, enabling seamless management of complex environments. With comprehensive monitoring, hardware & virtual machine provisioning, robust automation, and configuration management, System Center (SC) 2025 offers a simplified datacenter management experience. Stay in control of your IT resources across the datacenter and the cloud.",
        "additionalInfo": {
            "Product Edition": "System Center 2025 Datacenter - 2 Core License Pack 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PP48:0001",
            "Product ID": "1791785",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "System Center 2025 Datacenter",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b911,630.10",
            "List Price": "\u20b913,272.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 122,
        "name": "System Center 2025 Datacenter - 2 core License Pack 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "System Center 2025 Datacenter",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/systemcenter.svg",
        "price": 29066,
        "badge": "3 Years (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Comprehensive datacenter management for hybrid cloud environments",
            "Virtual Machine Manager (VMM) for Hyper-V and private cloud fabric",
            "Operations Manager (SCOM) for deep infrastructure monitoring and alerting",
            "Configuration Manager and Data Protection Manager integration"
        ],
        "shortDescription": "Microsoft System Center (SC) 2025 Datacenter brings cloud learnings to the datacenter, enabling seamless management of complex environments.",
        "description": "Microsoft System Center (SC) 2025 Datacenter brings cloud learnings to the datacenter, enabling seamless management of complex environments. With comprehensive monitoring, hardware & virtual machine provisioning, robust automation, and configuration management, System Center (SC) 2025 offers a simplified datacenter management experience. Stay in control of your IT resources across the datacenter and the cloud.",
        "additionalInfo": {
            "Product Edition": "System Center 2025 Datacenter - 2 core License Pack 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PP48:0003",
            "Product ID": "1791785",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "System Center 2025 Datacenter",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b929,065.62",
            "List Price": "\u20b933,169.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 123,
        "name": "System Center 2025 Standard - 2 Core License Pack 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "System Center 2025 Standard",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/systemcenter.svg",
        "price": 4266,
        "badge": "1 Year (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Comprehensive datacenter management for hybrid cloud environments",
            "Virtual Machine Manager (VMM) for Hyper-V and private cloud fabric",
            "Operations Manager (SCOM) for deep infrastructure monitoring and alerting",
            "Configuration Manager and Data Protection Manager integration"
        ],
        "shortDescription": "Microsoft System Center (SC) 2025 Standard brings cloud learnings to the datacenter, enabling seamless management of complex environments.",
        "description": "Microsoft System Center (SC) 2025 Standard brings cloud learnings to the datacenter, enabling seamless management of complex environments. With comprehensive monitoring, hardware & virtual machine provisioning, robust automation, and configuration management, System Center (SC) 2025 offers a simplified datacenter management experience. Stay in control of your IT resources across the datacenter and the cloud.",
        "additionalInfo": {
            "Product Edition": "System Center 2025 Standard - 2 Core License Pack 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PP47:0001",
            "Product ID": "1791786",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "System Center 2025 Standard",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b94,265.77",
            "List Price": "\u20b94,868.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 124,
        "name": "System Center 2025 Standard - 2 Core License Pack 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "System Center 2025 Standard",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/systemcenter.svg",
        "price": 10648,
        "badge": "3 Years (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Comprehensive datacenter management for hybrid cloud environments",
            "Virtual Machine Manager (VMM) for Hyper-V and private cloud fabric",
            "Operations Manager (SCOM) for deep infrastructure monitoring and alerting",
            "Configuration Manager and Data Protection Manager integration"
        ],
        "shortDescription": "Microsoft System Center (SC) 2025 Standard brings cloud learnings to the datacenter, enabling seamless management of complex environments.",
        "description": "Microsoft System Center (SC) 2025 Standard brings cloud learnings to the datacenter, enabling seamless management of complex environments. With comprehensive monitoring, hardware & virtual machine provisioning, robust automation, and configuration management, System Center (SC) 2025 offers a simplified datacenter management experience. Stay in control of your IT resources across the datacenter and the cloud.",
        "additionalInfo": {
            "Product Edition": "System Center 2025 Standard - 2 Core License Pack 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PP47:0003",
            "Product ID": "1791786",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "System Center 2025 Standard",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b910,647.78",
            "List Price": "\u20b912,151.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 125,
        "name": "Win Server DC Core Ext Security 2012 2 Core Y3 (October 2025-2026) - OneTime",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Extended Security Updates for Windows Server DC Core",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 57252,
        "badge": "1 Year (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. This ESU can be applied to either WS 2012 or WS 2012 R2. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "Win Server DC Core Ext Security 2012 2 Core Y3 (October 2025-2026) - OneTime",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HPVW:000B",
            "Product ID": "1613062",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Extended Security Updates for Windows Server DC Core",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b957,252.32",
            "List Price": "\u20b965,335.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 126,
        "name": "Win Server DC Core Ext Security 2012 8 Core Y3 (October 2025-2026) - OneTime",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Extended Security Updates for Windows Server DC Core",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 229160,
        "badge": "1-Year Subscription",
        "moq": "Per useryear",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. This ESU can be applied to either WS 2012 or WS 2012 R2. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "Win Server DC Core Ext Security 2012 8 Core Y3 (October 2025-2026) - OneTime",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HPVW:0001",
            "Product ID": "1613062",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Extended Security Updates for Windows Server DC Core",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b9229,160.00",
            "List Price": "\u20b9261,512.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 127,
        "name": "Win Server Std Core Ext Security 2012 2 Core Y3 (October 2025-2026) - OneTime",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Extended Security Updates for Windows Server Standard Core",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 9976,
        "badge": "1 Year (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. This ESU can be applied to either WS 2012 or WS 2012 R2. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "Win Server Std Core Ext Security 2012 2 Core Y3 (October 2025-2026) - OneTime",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HPVV:0009",
            "Product ID": "1613060",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Extended Security Updates for Windows Server Standard Core",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b99,975.67",
            "List Price": "\u20b911,384.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 128,
        "name": "Win Server Std Core Ext Security 2012 8 Core Y3 (October 2025-2026) - OneTime",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Extended Security Updates for Windows Server Standard Core",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/esu.svg",
        "price": 39756,
        "badge": "1-Year Subscription",
        "moq": "Per useryear",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date.",
        "description": "With the purchase of Extended Security Updates (ESU), you will receive Critical security updates for up to three years past the end of the support date. This ESU can be applied to either WS 2012 or WS 2012 R2. You will also be able to use your existing support contract to receive technical support for covered servers.",
        "additionalInfo": {
            "Product Edition": "Win Server Std Core Ext Security 2012 8 Core Y3 (October 2025-2026) - OneTime",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0HPVV:000B",
            "Product ID": "1613060",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Extended Security Updates for Windows Server Standard Core",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b939,756.34",
            "List Price": "\u20b945,369.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 129,
        "name": "Windows Server 2022 Remote Desktop Services - 1 User CAL 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Remote Desktop Server CAL 2022",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 6747,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Remote Desktop Services enables users to access session-based desktops, virtual machine-based desktops, or applications in the data center from both within a corporate network and from the Internet.",
        "description": "Remote Desktop Services enables users to access session-based desktops, virtual machine-based desktops, or applications in the data center from both within a corporate network and from the Internet.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2022 Remote Desktop Services - 1 User CAL 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0D7HX:0007",
            "Product ID": "1357894",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Remote Desktop Server CAL 2022",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "2022",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b96,747.42",
            "List Price": "\u20b97,700.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 130,
        "name": "Windows Server 2022 Standard - 8 Core License Pack 1 Year",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server Standard Core 2022",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 21508,
        "badge": "1-Year Subscription",
        "moq": "Per useryear",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2022 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "description": "Windows Server 2022 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2022 Standard - 8 Core License Pack 1 Year",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0D5RK:0002",
            "Product ID": "1357897",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server Standard Core 2022",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b921,507.63",
            "List Price": "\u20b924,544.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 131,
        "name": "Windows Server 2022 Standard - 8 Core License Pack 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server Standard Core 2022",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 18709,
        "badge": "1-Year Subscription",
        "moq": "Per useryear",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2022 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "description": "Windows Server 2022 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2022 Standard - 8 Core License Pack 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0D5RK:0002",
            "Product ID": "1357897",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server Standard Core 2022",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "2022",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b918,708.76",
            "List Price": "\u20b921,350.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 132,
        "name": "Windows Server 2022 Standard - 8 Core License Pack 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server Standard Core 2022",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 47647,
        "badge": "3-Year Subscription",
        "moq": "Per user3 years",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2022 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "description": "Windows Server 2022 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2022 Standard - 8 Core License Pack 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0D5RK:0003",
            "Product ID": "1357897",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server Standard Core 2022",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "2022",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b947,647.32",
            "List Price": "\u20b954,374.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 133,
        "name": "Windows Server 2025 CAL - 1 Device CAL - 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server CAL 2025",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 901,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses Windows Server.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses Windows Server.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 CAL - 1 Device CAL - 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHT:0003",
            "Product ID": "1752047",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server CAL 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b9900.82",
            "List Price": "\u20b91,028.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 134,
        "name": "Windows Server 2025 CAL - 1 Device CAL - 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server CAL 2025",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 2702,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses Windows Server.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses Windows Server.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 CAL - 1 Device CAL - 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHT:0001",
            "Product ID": "1752047",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server CAL 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b92,702.47",
            "List Price": "\u20b93,084.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 135,
        "name": "Windows Server 2025 CAL - 1 User CAL - 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server CAL 2025",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 1064,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses Windows Server.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses Windows Server.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 CAL - 1 User CAL - 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHT:0004",
            "Product ID": "1752047",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server CAL 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b91,063.81",
            "List Price": "\u20b91,214.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 136,
        "name": "Windows Server 2025 CAL - 1 User CAL - 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server CAL 2025",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 3201,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses Windows Server.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses Windows Server.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 CAL - 1 User CAL - 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHT:0006",
            "Product ID": "1752047",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server CAL 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b93,201.08",
            "List Price": "\u20b93,653.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 137,
        "name": "Windows Server 2025 Datacenter - 2 Core License Pack 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server Data Center Core 2025",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 35622,
        "badge": "1 Year (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2025 Datacenter is for highly virtualized datacenter and cloud environments, including shielded virtual machines, software-defined networking, storage spaces direct, and storage replication.",
        "description": "Windows Server 2025 Datacenter is for highly virtualized datacenter and cloud environments, including shielded virtual machines, software-defined networking, storage spaces direct, and storage replication.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Datacenter - 2 Core License Pack 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHD:0002",
            "Product ID": "1752049",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server Data Center Core 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b935,622.01",
            "List Price": "\u20b940,651.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 138,
        "name": "Windows Server 2025 Datacenter - 2 Core License Pack 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server Data Center Core 2025",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 74450,
        "badge": "3 Years (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2025 Datacenter is for highly virtualized datacenter and cloud environments, including shielded virtual machines, software-defined networking, storage spaces direct, and storage replication.",
        "description": "Windows Server 2025 Datacenter is for highly virtualized datacenter and cloud environments, including shielded virtual machines, software-defined networking, storage spaces direct, and storage replication.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Datacenter - 2 Core License Pack 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHD:0005",
            "Product ID": "1752049",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server Data Center Core 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b974,450.36",
            "List Price": "\u20b984,961.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 139,
        "name": "Windows Server 2025 Datacenter - 8 Core License Pack 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server Data Center Core 2025",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 142490,
        "badge": "1-Year Subscription",
        "moq": "Per useryear",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2025 Datacenter is for highly virtualized datacenter and cloud environments, including shielded virtual machines, software-defined networking, storage spaces direct, and storage replication.",
        "description": "Windows Server 2025 Datacenter is for highly virtualized datacenter and cloud environments, including shielded virtual machines, software-defined networking, storage spaces direct, and storage replication.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Datacenter - 8 Core License Pack 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHD:0003",
            "Product ID": "1752049",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server Data Center Core 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b9142,489.79",
            "List Price": "\u20b9162,606.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 140,
        "name": "Windows Server 2025 Datacenter - 8 Core License Pack 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server Data Center Core 2025",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 297804,
        "badge": "3-Year Subscription",
        "moq": "Per user3 years",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2025 Datacenter is for highly virtualized datacenter and cloud environments, including shielded virtual machines, software-defined networking, storage spaces direct, and storage replication.",
        "description": "Windows Server 2025 Datacenter is for highly virtualized datacenter and cloud environments, including shielded virtual machines, software-defined networking, storage spaces direct, and storage replication.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Datacenter - 8 Core License Pack 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHD:0006",
            "Product ID": "1752049",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server Data Center Core 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b9297,804.07",
            "List Price": "\u20b9339,847.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 141,
        "name": "Windows Server 2025 RMS CAL - 1 Device CAL - 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Rights Management Services CAL 2025",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 1555,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 RMS CAL - 1 Device CAL - 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHF:0001",
            "Product ID": "1752048",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Rights Management Services CAL 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b91,555.41",
            "List Price": "\u20b91,775.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 142,
        "name": "Windows Server 2025 RMS CAL - 1 Device CAL - 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Rights Management Services CAL 2025",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 4586,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 RMS CAL - 1 Device CAL - 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHF:0002",
            "Product ID": "1752048",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Rights Management Services CAL 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b94,585.62",
            "List Price": "\u20b95,233.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 143,
        "name": "Windows Server 2025 RMS CAL - 1 User CAL - 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Rights Management Services CAL 2025",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 1883,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 RMS CAL - 1 User CAL - 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHF:0003",
            "Product ID": "1752048",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Rights Management Services CAL 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b91,883.14",
            "List Price": "\u20b92,149.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 144,
        "name": "Windows Server 2025 RMS CAL - 1 User CAL - 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Rights Management Services CAL 2025",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 5650,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "description": "A Client Access License (CAL) is required for each user or device that accesses the server software.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 RMS CAL - 1 User CAL - 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHF:0004",
            "Product ID": "1752048",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Rights Management Services CAL 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b95,650.31",
            "List Price": "\u20b96,448.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 145,
        "name": "Windows Server 2025 Remote Desktop Services - 1 User CAL 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server 2025 Remote Desktop Services",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 6747,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Remote Desktop Services enables users to access session-based desktops, virtual machine-based desktops, or applications in the data center from both within a corporate network and from the Internet.",
        "description": "Remote Desktop Services enables users to access session-based desktops, virtual machine-based desktops, or applications in the data center from both within a corporate network and from the Internet.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Remote Desktop Services - 1 User CAL 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHB:0002",
            "Product ID": "1752050",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server 2025 Remote Desktop Services",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b96,747.42",
            "List Price": "\u20b97,700.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 146,
        "name": "Windows Server 2025 Remote Desktop Services - 1 User CAL 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server 2025 Remote Desktop Services",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 15009,
        "badge": "Client Access License (CAL)",
        "moq": "1 CAL",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Remote Desktop Services enables users to access session-based desktops, virtual machine-based desktops, or applications in the data center from both within a corporate network and from the Internet.",
        "description": "Remote Desktop Services enables users to access session-based desktops, virtual machine-based desktops, or applications in the data center from both within a corporate network and from the Internet.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Remote Desktop Services - 1 User CAL 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHB:0003",
            "Product ID": "1752050",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server 2025 Remote Desktop Services",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b915,009.07",
            "List Price": "\u20b917,128.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 147,
        "name": "Windows Server 2025 Standard - 2 Core License Pack 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server Standard Core 2025",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 5118,
        "badge": "1 Year (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2025 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "description": "Windows Server 2025 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Standard - 2 Core License Pack 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHC:0004",
            "Product ID": "1752051",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server Standard Core 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b95,118.40",
            "List Price": "\u20b95,841.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 148,
        "name": "Windows Server 2025 Standard - 2 Core License Pack 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server Standard Core 2025",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 13082,
        "badge": "3 Years (2-Core Pack)",
        "moq": "1 Pack (2 Cores)",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2025 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "description": "Windows Server 2025 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Standard - 2 Core License Pack 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHC:0001",
            "Product ID": "1752051",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server Standard Core 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b913,082.11",
            "List Price": "\u20b914,929.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 149,
        "name": "Windows Server 2025 Standard - 8 Core License Pack 1 Year - Annual",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server Standard Core 2025",
        "term": "1 Year",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 20474,
        "badge": "1-Year Subscription",
        "moq": "Per useryear",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2025 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "description": "Windows Server 2025 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Standard - 8 Core License Pack 1 Year - Annual",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHC:0002",
            "Product ID": "1752051",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server Standard Core 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "1 Year",
            "Purchase Unit": "Per user/year",
            "Purchase Price": "\u20b920,473.61",
            "List Price": "\u20b923,364.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
    },
    {
        "id": 150,
        "name": "Windows Server 2025 Standard - 8 Core License Pack 3 Year - Triennial",
        "category": "Software",
        "softwareType": "Software Subscriptions",
        "family": "Windows Server Standard Core 2025",
        "term": "3 Years",
        "brand": "Microsoft",
        "image": "/products/windowsserver.svg",
        "price": 52413,
        "badge": "3-Year Subscription",
        "moq": "Per user3 years",
        "features": [
            "Enterprise-grade multi-core server operating system",
            "Advanced hybrid cloud integration with Azure Arc and Azure Automanage",
            "Multi-layer security with Secured-Core Server and TLS 1.3 encryption",
            "Hyper-V virtualization, Software-Defined Storage and Storage Spaces Direct"
        ],
        "shortDescription": "Windows Server 2025 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "description": "Windows Server 2025 is the cloud-ready operating system that supports your current workloads while introducing new technologies that make it easy to transition to cloud computing.",
        "additionalInfo": {
            "Product Edition": "Windows Server 2025 Standard - 8 Core License Pack 3 Year - Triennial",
            "Publisher / Brand": "Microsoft Corporation",
            "Part Number": "DG7GMGF0PWHC:0005",
            "Product ID": "1752051",
            "Software Type": "Software Subscriptions",
            "Product Type": "Software",
            "Family": "Windows Server Standard Core 2025",
            "Agreement": "Microsoft CSP Software Subscriptions",
            "Segment": "Commercial",
            "Version": "Non-Specific",
            "Term": "3 Years",
            "Purchase Unit": "Per user/3 years",
            "Purchase Price": "\u20b952,413.45",
            "List Price": "\u20b959,813.00",
            "Price List Valid To": "9/1/2026",
            "License Type": "Digital License (Microsoft CSP Software Subscriptions)",
            "Delivery": "Instant via Email (License Key & Setup)",
            "Supported OS": "Windows / Windows Server / macOS / Linux",
            "Compliance": "ISO 27001, SOC 2, HIPAA & GDPR Compliant",
            "Support & Updates": "Official Microsoft Product Support & Security Updates"
        },
        "warranty": "Official Microsoft Commercial Software License & Standard Product Assurance."
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