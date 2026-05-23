import os
from datetime import datetime, timedelta
from models import User, MenuItem, Table, Voucher, Invoice, DataManager


class AuthService:
    def __init__(self):
        self.current_user = None

    def login(self, username, password):
        users = DataManager.load_users()
        for u in users:
            if u.username == username and u.password == password:
                self.current_user = u
                return u
        return None

    def logout(self):
        self.current_user = None

    def is_admin(self):
        return self.current_user and self.current_user.role == "admin"

    def is_logged_in(self):
        return self.current_user is not None

    def change_password(self, old_pw, new_pw):
        users = DataManager.load_users()
        for u in users:
            if u.username == self.current_user.username and u.password == old_pw:
                u.password = new_pw
                DataManager.save_users(users)
                self.current_user.password = new_pw
                return True
        return False

    def add_user(self, username, password, role):
        users = DataManager.load_users()
        if any(u.username == username for u in users):
            return False
        users.append(User(username, password, role))
        DataManager.save_users(users)
        return True

    def list_users(self):
        return DataManager.load_users()

    def delete_user(self, username):
        if username == self.current_user.username:
            return False
        users = DataManager.load_users()
        users = [u for u in users if u.username != username]
        DataManager.save_users(users)
        return True


class MenuService:
    @staticmethod
    def get_all():
        return DataManager.load_menu()

    @staticmethod
    def get_categories():
        menu = DataManager.load_menu()
        cats = []
        for item in menu:
            if item.category not in cats:
                cats.append(item.category)
        return cats

    @staticmethod
    def get_by_category(category):
        return [item for item in DataManager.load_menu() if item.category == category]

    @staticmethod
    def get_by_id(item_id):
        for item in DataManager.load_menu():
            if item.id == item_id:
                return item
        return None

    @staticmethod
    def add_item(name, category, price):
        menu = DataManager.load_menu()
        new_id = max((item.id for item in menu), default=0) + 1
        menu.append(MenuItem(new_id, name, category, price))
        DataManager.save_menu(menu)
        return new_id

    @staticmethod
    def update_item(item_id, name, category, price):
        menu = DataManager.load_menu()
        for item in menu:
            if item.id == item_id:
                item.name = name
                item.category = category
                item.price = price
                DataManager.save_menu(menu)
                return True
        return False

    @staticmethod
    def delete_item(item_id):
        menu = DataManager.load_menu()
        menu = [item for item in menu if item.id != item_id]
        DataManager.save_menu(menu)
        return True


class TableService:
    @staticmethod
    def get_all():
        return DataManager.load_tables()

    @staticmethod
    def get_by_id(table_id):
        for t in DataManager.load_tables():
            if t.id == table_id:
                return t
        return None

    @staticmethod
    def assign_table(table_id, customer_name):
        tables = DataManager.load_tables()
        for t in tables:
            if t.id == table_id:
                t.status = "occupied"
                t.customer_name = customer_name
                DataManager.save_tables(tables)
                return True
        return False

    @staticmethod
    def free_table(table_id):
        tables = DataManager.load_tables()
        for t in tables:
            if t.id == table_id:
                t.status = "empty"
                t.order = []
                t.customer_name = ""
                DataManager.save_tables(tables)
                return True
        return False

    @staticmethod
    def merge_tables(source_ids, target_id):
        tables = DataManager.load_tables()
        target = None
        for t in tables:
            if t.id == target_id:
                target = t
                break
        if not target:
            return False

        for sid in source_ids:
            if sid == target_id:
                continue
            source = None
            for t in tables:
                if t.id == sid:
                    source = t
                    break
            if source:
                target.order.extend(source.order)
                source.status = "empty"
                source.order = []
                source.customer_name = ""

        DataManager.save_tables(tables)
        return True

    @staticmethod
    def get_empty_tables():
        return [t for t in DataManager.load_tables() if t.status == "empty"]

    @staticmethod
    def get_occupied_tables():
        return [t for t in DataManager.load_tables() if t.status == "occupied"]


class OrderService:
    @staticmethod
    def add_item_to_table(table_id, menu_item, quantity, note):
        tables = DataManager.load_tables()
        for t in tables:
            if t.id == table_id:
                t.order.append({
                    "item_id": menu_item.id,
                    "name": menu_item.name,
                    "price": menu_item.price,
                    "quantity": quantity,
                    "note": note
                })
                DataManager.save_tables(tables)
                return True
        return False

    @staticmethod
    def remove_item_from_table(table_id, index):
        tables = DataManager.load_tables()
        for t in tables:
            if t.id == table_id:
                if 0 <= index < len(t.order):
                    t.order.pop(index)
                    DataManager.save_tables(tables)
                    return True
                return False
        return False

    @staticmethod
    def calculate_subtotal(table):
        return sum(item["price"] * item["quantity"] for item in table.order)

    @staticmethod
    def calculate_discount(subtotal, voucher_type, voucher_value, manual_discount=0):
        discount = 0
        discount_type = "none"

        if manual_discount > 0:
            discount = manual_discount if manual_discount <= subtotal else subtotal
            discount_type = "manual"
            if voucher_type and voucher_value:
                if voucher_type == "percent":
                    v_discount = subtotal * voucher_value // 100
                else:
                    v_discount = voucher_value
                discount = max(discount, v_discount)
                discount_type = "voucher"
        elif voucher_type and voucher_value:
            if voucher_type == "percent":
                discount = subtotal * voucher_value // 100
            else:
                discount = voucher_value
            discount_type = "voucher"

        discount = min(discount, subtotal)
        return discount, discount_type

    @staticmethod
    def save_invoice(table, discount, discount_type, voucher_code, total, payment, change, employee):
        subtotal = OrderService.calculate_subtotal(table)
        now = datetime.now()
        invoice_id = f"HD{now.strftime('%y%m%d%H%M%S')}"

        invoice = Invoice(
            invoice_id=invoice_id,
            table_id=table.id,
            customer_name=table.customer_name,
            items=table.order.copy(),
            subtotal=subtotal,
            discount=discount,
            discount_type=discount_type,
            voucher_code=voucher_code or "",
            total=total,
            payment=payment,
            change=change,
            created_at=now.strftime("%Y-%m-%d %H:%M:%S"),
            employee=employee
        )
        DataManager.save_invoice(invoice)
        return invoice


class VoucherService:
    @staticmethod
    def get_all():
        return DataManager.load_vouchers()

    @staticmethod
    def validate(code, subtotal):
        vouchers = DataManager.load_vouchers()
        for v in vouchers:
            if v.code.upper() == code.upper():
                if subtotal < v.min_order:
                    return False, f"Don hang toi thieu {v.min_order}đ de ap dung ma nay"
                try:
                    expiry = datetime.strptime(v.expiry, "%Y-%m-%d")
                    if expiry < datetime.now():
                        return False, "Ma giam gia da het han"
                except:
                    pass
                return True, v
        return False, "Ma giam gia khong ton tai"

    @staticmethod
    def apply(voucher, subtotal):
        if voucher.type == "percent":
            return subtotal * voucher.value // 100
        else:
            return voucher.value

    @staticmethod
    def add_voucher(code, v_type, value, min_order, expiry):
        vouchers = DataManager.load_vouchers()
        vouchers.append(Voucher(code.upper(), v_type, value, min_order, expiry))
        DataManager.save_vouchers(vouchers)
        return True


class StatsService:
    @staticmethod
    def get_invoices_by_date(from_date, to_date):
        invoices = DataManager.load_all_invoices()
        result = []
        for inv in invoices:
            try:
                inv_date = datetime.strptime(inv.created_at[:10], "%Y-%m-%d")
                if from_date <= inv_date <= to_date:
                    result.append(inv)
            except:
                continue
        return result

    @staticmethod
    def get_all_invoices():
        return DataManager.load_all_invoices()

    @staticmethod
    def get_top_selling(from_date=None, to_date=None, limit=5):
        if from_date and to_date:
            invoices = StatsService.get_invoices_by_date(from_date, to_date)
        else:
            invoices = DataManager.load_all_invoices()

        item_counts = {}
        for inv in invoices:
            for item in inv.items:
                name = item["name"]
                qty = item["quantity"]
                item_counts[name] = item_counts.get(name, 0) + qty

        sorted_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:limit], sorted_items[-limit:] if len(sorted_items) >= limit else sorted_items

    @staticmethod
    def get_revenue(from_date=None, to_date=None):
        if from_date and to_date:
            invoices = StatsService.get_invoices_by_date(from_date, to_date)
        else:
            invoices = DataManager.load_all_invoices()

        total_revenue = sum(inv.total for inv in invoices)
        revenue_by_item = {}
        for inv in invoices:
            for item in inv.items:
                name = item["name"]
                rev = item["price"] * item["quantity"]
                revenue_by_item[name] = revenue_by_item.get(name, 0) + rev

        return total_revenue, revenue_by_item, len(invoices)

    @staticmethod
    def get_daily_revenue(days=7):
        today = datetime.now()
        result = {}
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            result[day.strftime("%Y-%m-%d")] = 0

        invoices = DataManager.load_all_invoices()
        for inv in invoices:
            try:
                inv_date = datetime.strptime(inv.created_at[:10], "%Y-%m-%d")
                day_key = inv_date.strftime("%Y-%m-%d")
                if day_key in result:
                    result[day_key] += inv.total
            except:
                continue

        return result
