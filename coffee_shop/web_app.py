import io
import socket
import qrcode
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from functools import wraps
from datetime import datetime, timedelta
from models import DataManager
from services import AuthService, MenuService, TableService, OrderService, VoucherService, StatsService

app = Flask(__name__)
app.secret_key = 'coffee-shop-secret-key-2026'

DataManager.init_default_data()

ms = MenuService()
ts = TableService()
os = OrderService()
vs = VoucherService()
ss = StatsService()


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap


def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return wrap


# ============ PAGE ROUTES ============

@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        auth = AuthService()
        user = auth.login(username, password)
        if user:
            session['logged_in'] = True
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Sai tên đăng nhập hoặc mật khẩu!')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ============ CUSTOMER QR ORDERING (no login required) ============

def get_host_url():
    import os
    public_url = os.environ.get('PUBLIC_URL')
    if public_url:
        return public_url
    try:
        hostname = socket.gethostname()
        ips = socket.gethostbyname_ex(hostname)[2]
        for ip in ips:
            if ip.startswith('127.'):
                continue
            parts = ip.split('.')
            if parts[0] == '172' and 16 <= int(parts[1]) <= 31:
                continue
            return ip
        for ip in ips:
            if not ip.startswith('127.'):
                return ip
        return "127.0.0.1"
    except:
        return "127.0.0.1"


def get_base_url():
    import os
    public_url = os.environ.get('PUBLIC_URL')
    if public_url:
        return public_url.rstrip('/')
    return f"http://{get_host_url()}:5001"


@app.route('/customer/<int:table_id>')
def customer_menu(table_id):
    table = ts.get_by_id(table_id)
    if not table:
        return "Bàn không tồn tại", 404
    return render_template('customer_menu.html', table_id=table_id, host_url=get_base_url())


@app.route('/api/customer/menu')
def api_customer_menu():
    items = ms.get_all()
    return jsonify([{'id': i.id, 'name': i.name, 'category': i.category, 'price': i.price} for i in items])


@app.route('/api/customer/menu/categories')
def api_customer_menu_categories():
    return jsonify(ms.get_categories())


@app.route('/api/customer/menu/category/<category>')
def api_customer_menu_by_category(category):
    items = ms.get_by_category(category)
    return jsonify([{'id': i.id, 'name': i.name, 'category': i.category, 'price': i.price} for i in items])


@app.route('/api/customer/table/<int:table_id>')
def api_customer_table(table_id):
    table = ts.get_by_id(table_id)
    if not table:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'id': table.id, 'status': table.status,
        'customer_name': table.customer_name,
        'order': table.order,
        'subtotal': os.calculate_subtotal(table)
    })


@app.route('/api/customer/table/<int:table_id>/assign', methods=['POST'])
def api_customer_table_assign(table_id):
    data = request.get_json()
    name = data.get('customer_name', f"Khách Bàn {table_id}")
    ok = ts.assign_table(table_id, name)
    return jsonify({'success': ok})


@app.route('/api/customer/table/<int:table_id>/add-item', methods=['POST'])
def api_customer_add_item(table_id):
    data = request.get_json()
    item = ms.get_by_id(data['item_id'])
    if not item:
        return jsonify({'success': False, 'error': 'Không tìm thấy món'}), 404
    table = ts.get_by_id(table_id)
    if table.status == 'empty':
        ts.assign_table(table_id, f"Khách Bàn {table_id} (QR)")
    ok = os.add_item_to_table(table_id, item, data.get('quantity', 1), data.get('note', ''))
    return jsonify({'success': ok})


@app.route('/api/customer/table/<int:table_id>/remove-item', methods=['POST'])
def api_customer_remove_item(table_id):
    data = request.get_json()
    ok = os.remove_item_from_table(table_id, data['index'])
    return jsonify({'success': ok})


# ============ QR CODE MANAGEMENT (admin) ============

@app.route('/admin/qrcodes')
@login_required
@admin_required
def admin_qrcodes():
    return render_template('qrcodes.html', active_page='qrcodes')


@app.route('/api/qrcode/<int:table_id>')
@login_required
@admin_required
def api_generate_qrcode(table_id):
    table = ts.get_by_id(table_id)
    if not table:
        return jsonify({'error': 'Not found'}), 404
    url = f"{get_base_url()}/customer/{table_id}"
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/api/qrcodes/all')
@login_required
@admin_required
def api_qrcodes_all():
    tables = ts.get_all()
    return jsonify([{
        'id': t.id,
        'status': t.status,
        'url': f"{get_base_url()}/customer/{t.id}"
    } for t in tables])


# ============ ADMIN PAGES ============

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', active_page='dashboard')


@app.route('/menu')
@login_required
def menu_page():
    return render_template('menu.html', active_page='menu', is_admin=session.get('role') == 'admin')


@app.route('/tables')
@login_required
def tables_page():
    return render_template('tables.html', active_page='tables', is_admin=session.get('role') == 'admin')


@app.route('/order')
@login_required
def order_page():
    return render_template('order.html', active_page='order')


@app.route('/billing')
@login_required
def billing_page():
    return render_template('billing.html', active_page='billing')


@app.route('/vouchers')
@login_required
def vouchers_page():
    return render_template('vouchers.html', active_page='vouchers', is_admin=session.get('role') == 'admin')


@app.route('/statistics')
@login_required
def statistics_page():
    return render_template('statistics.html', active_page='statistics')


@app.route('/users')
@login_required
@admin_required
def users_page():
    return render_template('users.html', active_page='users')


# ============ API ROUTES ============

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    auth = AuthService()
    user = auth.login(data.get('username', ''), data.get('password', ''))
    if user:
        session['logged_in'] = True
        session['username'] = user.username
        session['role'] = user.role
        return jsonify({'success': True, 'username': user.username, 'role': user.role})
    return jsonify({'success': False, 'error': 'Sai tài khoản hoặc mật khẩu'})


@app.route('/api/dashboard')
@login_required
def api_dashboard():
    tables = ts.get_all()
    total_tables = len(tables)
    empty_tables = sum(1 for t in tables if t.status == 'empty')
    occupied_tables = total_tables - empty_tables

    today = datetime.now().strftime('%Y-%m-%d')
    today_invoices = [inv for inv in DataManager.load_all_invoices() if inv.created_at.startswith(today)]
    today_revenue = sum(inv.total for inv in today_invoices)
    today_orders = len(today_invoices)

    top, _ = ss.get_top_selling(limit=5)
    total_rev, _, total_count = ss.get_revenue()

    return jsonify({
        'total_tables': total_tables,
        'empty_tables': empty_tables,
        'occupied_tables': occupied_tables,
        'today_revenue': today_revenue,
        'today_orders': today_orders,
        'top_items': [{'name': n, 'qty': q} for n, q in top],
        'total_revenue': total_rev,
        'total_orders': total_count
    })


# ---- Menu API ----

@app.route('/api/menu')
@login_required
def api_menu():
    items = ms.get_all()
    return jsonify([{'id': i.id, 'name': i.name, 'category': i.category, 'price': i.price} for i in items])


@app.route('/api/menu/categories')
@login_required
def api_menu_categories():
    return jsonify(ms.get_categories())


@app.route('/api/menu/category/<category>')
@login_required
def api_menu_by_category(category):
    items = ms.get_by_category(category)
    return jsonify([{'id': i.id, 'name': i.name, 'category': i.category, 'price': i.price} for i in items])


@app.route('/api/menu/add', methods=['POST'])
@login_required
@admin_required
def api_menu_add():
    data = request.get_json()
    new_id = ms.add_item(data['name'], data['category'], data['price'])
    return jsonify({'success': True, 'id': new_id})


@app.route('/api/menu/update', methods=['POST'])
@login_required
@admin_required
def api_menu_update():
    data = request.get_json()
    ok = ms.update_item(data['id'], data['name'], data['category'], data['price'])
    return jsonify({'success': ok})


@app.route('/api/menu/delete', methods=['POST'])
@login_required
@admin_required
def api_menu_delete():
    data = request.get_json()
    ms.delete_item(data['id'])
    return jsonify({'success': True})


# ---- Tables API ----

@app.route('/api/tables')
@login_required
def api_tables():
    tables = ts.get_all()
    return jsonify([{
        'id': t.id, 'status': t.status,
        'customer_name': t.customer_name,
        'order': t.order
    } for t in tables])


@app.route('/api/tables/assign', methods=['POST'])
@login_required
def api_tables_assign():
    data = request.get_json()
    name = data.get('customer_name', f"Khách Bàn {data['table_id']}")
    ok = ts.assign_table(data['table_id'], name)
    return jsonify({'success': ok})


@app.route('/api/tables/free', methods=['POST'])
@login_required
def api_tables_free():
    data = request.get_json()
    ok = ts.free_table(data['table_id'])
    return jsonify({'success': ok})


@app.route('/api/tables/merge', methods=['POST'])
@login_required
@admin_required
def api_tables_merge():
    data = request.get_json()
    ok = ts.merge_tables(data['source_ids'], data['target_id'])
    return jsonify({'success': ok})


@app.route('/api/tables/transfer', methods=['POST'])
@login_required
@admin_required
def api_tables_transfer():
    data = request.get_json()
    from_id, to_id = data['from_id'], data['to_id']
    tables = ts.get_all()
    t_from = next((t for t in tables if t.id == from_id), None)
    t_to = next((t for t in tables if t.id == to_id), None)
    if not t_from or t_from.status != 'occupied':
        return jsonify({'success': False, 'error': 'Bàn nguồn không có khách'})
    if t_to.status != 'empty':
        return jsonify({'success': False, 'error': 'Bàn đích đang có khách'})
    t_to.status = 'occupied'
    t_to.customer_name = t_from.customer_name
    t_to.order = t_from.order
    t_from.status = 'empty'
    t_from.order = []
    t_from.customer_name = ''
    DataManager.save_tables(tables)
    return jsonify({'success': True})


# ---- Order API ----

@app.route('/api/orders/add-item', methods=['POST'])
@login_required
def api_order_add():
    data = request.get_json()
    item = ms.get_by_id(data['item_id'])
    if not item:
        return jsonify({'success': False, 'error': 'Không tìm thấy món'})
    ok = os.add_item_to_table(data['table_id'], item, data.get('quantity', 1), data.get('note', ''))
    return jsonify({'success': ok})


@app.route('/api/orders/remove-item', methods=['POST'])
@login_required
def api_order_remove():
    data = request.get_json()
    ok = os.remove_item_from_table(data['table_id'], data['index'])
    return jsonify({'success': ok})


@app.route('/api/orders/table/<int:table_id>')
@login_required
def api_order_table(table_id):
    table = ts.get_by_id(table_id)
    if not table:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'id': table.id, 'status': table.status,
        'customer_name': table.customer_name,
        'order': table.order,
        'subtotal': os.calculate_subtotal(table)
    })


# ---- Voucher API ----

@app.route('/api/vouchers')
@login_required
def api_vouchers():
    vouchers = vs.get_all()
    return jsonify([{
        'code': v.code, 'type': v.type, 'value': v.value,
        'min_order': v.min_order, 'expiry': v.expiry
    } for v in vouchers])


@app.route('/api/vouchers/validate', methods=['POST'])
@login_required
def api_voucher_validate():
    data = request.get_json()
    valid, result = vs.validate(data['code'], data['subtotal'])
    if valid:
        v = result
        discount = vs.apply(v, data['subtotal'])
        return jsonify({'valid': True, 'discount': discount, 'type': v.type, 'value': v.value})
    return jsonify({'valid': False, 'error': result if isinstance(result, str) else 'Mã không hợp lệ'})


@app.route('/api/vouchers/add', methods=['POST'])
@login_required
@admin_required
def api_voucher_add():
    data = request.get_json()
    vs.add_voucher(data['code'], data['type'], data['value'], data['min_order'], data['expiry'])
    return jsonify({'success': True})


# ---- Billing API ----

@app.route('/api/billing/calculate', methods=['POST'])
@login_required
def api_billing_calculate():
    data = request.get_json()
    table = ts.get_by_id(data['table_id'])
    if not table:
        return jsonify({'error': 'Not found'}), 404
    subtotal = os.calculate_subtotal(table)
    voucher_code = data.get('voucher_code', '')
    manual_discount = data.get('manual_discount', 0)
    discount = 0
    discount_type = 'none'

    if voucher_code:
        valid, result = vs.validate(voucher_code, subtotal)
        if valid:
            discount = vs.apply(result, subtotal)
            discount_type = 'voucher'

    if manual_discount and manual_discount > discount:
        discount = manual_discount
        discount_type = 'manual'

    total = subtotal - discount
    return jsonify({
        'subtotal': subtotal,
        'discount': discount,
        'discount_type': discount_type,
        'total': total,
        'items': table.order
    })


@app.route('/api/billing/pay', methods=['POST'])
@login_required
def api_billing_pay():
    data = request.get_json()
    table = ts.get_by_id(data['table_id'])
    if not table:
        return jsonify({'error': 'Not found'}), 404
    subtotal = os.calculate_subtotal(table)
    total = data['total']
    discount = subtotal - total
    discount_type = data.get('discount_type', 'none')
    voucher_code = data.get('voucher_code', '')
    payment = data['payment']
    change = payment - total

    invoice = os.save_invoice(
        table, discount, discount_type, voucher_code,
        total, payment, change, session['username']
    )
    ts.free_table(data['table_id'])

    return jsonify({
        'success': True,
        'invoice_id': invoice.invoice_id,
        'invoice': {
            'id': invoice.invoice_id,
            'table_id': invoice.table_id,
            'customer_name': invoice.customer_name,
            'items': invoice.items,
            'subtotal': invoice.subtotal,
            'discount': invoice.discount,
            'total': invoice.total,
            'payment': invoice.payment,
            'change': invoice.change,
            'created_at': invoice.created_at,
            'employee': invoice.employee
        }
    })


# ---- Statistics API ----

@app.route('/api/stats/top-selling')
@login_required
def api_stats_top_selling():
    limit = request.args.get('limit', 5, type=int)
    top, least = ss.get_top_selling(limit=limit)
    return jsonify({
        'top': [{'name': n, 'qty': q} for n, q in top],
        'least': [{'name': n, 'qty': q} for n, q in least]
    })


@app.route('/api/stats/revenue')
@login_required
def api_stats_revenue():
    total, rev_by_item, count = ss.get_revenue()
    sorted_rev = sorted(rev_by_item.items(), key=lambda x: x[1], reverse=True)
    return jsonify({
        'total_revenue': total,
        'total_orders': count,
        'revenue_by_item': [{'name': n, 'revenue': r} for n, r in sorted_rev]
    })


@app.route('/api/stats/daily-revenue')
@login_required
def api_stats_daily_revenue():
    days = request.args.get('days', 7, type=int)
    daily = ss.get_daily_revenue(days)
    return jsonify({
        'daily': [{'date': d, 'revenue': r} for d, r in daily.items()]
    })


@app.route('/api/stats/by-date', methods=['POST'])
@login_required
def api_stats_by_date():
    data = request.get_json()
    from_date = datetime.strptime(data['from'], '%Y-%m-%d')
    to_date = datetime.strptime(data['to'], '%Y-%m-%d')
    total, rev_by_item, count = ss.get_revenue(from_date, to_date)
    top, least = ss.get_top_selling(from_date, to_date, limit=5)
    sorted_rev = sorted(rev_by_item.items(), key=lambda x: x[1], reverse=True)
    return jsonify({
        'total_revenue': total,
        'total_orders': count,
        'top': [{'name': n, 'qty': q} for n, q in top],
        'least': [{'name': n, 'qty': q} for n, q in least],
        'revenue_by_item': [{'name': n, 'revenue': r} for n, r in sorted_rev]
    })


# ---- Users API ----

@app.route('/api/users')
@login_required
@admin_required
def api_users():
    auth = AuthService()
    users = auth.list_users()
    return jsonify([{'username': u.username, 'role': u.role} for u in users])


@app.route('/api/users/add', methods=['POST'])
@login_required
@admin_required
def api_users_add():
    auth = AuthService()
    data = request.get_json()
    ok = auth.add_user(data['username'], data['password'], data['role'])
    return jsonify({'success': ok, 'error': '' if ok else 'Tên đăng nhập đã tồn tại'})


@app.route('/api/users/delete', methods=['POST'])
@login_required
@admin_required
def api_users_delete():
    auth = AuthService()
    data = request.get_json()
    ok = auth.delete_user(data['username'])
    return jsonify({'success': ok})


@app.route('/api/users/change-password', methods=['POST'])
@login_required
def api_users_change_password():
    auth = AuthService()
    data = request.get_json()
    auth.current_user = type('obj', (object,), {'username': session['username']})()
    ok = auth.change_password(data['old_password'], data['new_password'])
    return jsonify({'success': ok})


# ============ MAIN ============

if __name__ == '__main__':
    print("== QUAN LY QUAN COFFEE - WEB APP ==")
    print(f"Truy cap: http://{get_host_url()}:5001")
    print("Tai khoan: admin / admin123 hoac nhanvien1 / nv123")
    app.run(debug=True, host='0.0.0.0', port=5001)
