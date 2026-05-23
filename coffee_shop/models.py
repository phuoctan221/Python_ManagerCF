import json
import os
from dataclasses import dataclass, field, asdict
from typing import List


class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'


@dataclass
class User:
    username: str
    password: str
    role: str


@dataclass
class MenuItem:
    id: int
    name: str
    category: str
    price: int


@dataclass
class Table:
    id: int
    status: str = "empty"
    order: List[dict] = field(default_factory=list)
    customer_name: str = ""


@dataclass
class Voucher:
    code: str
    type: str
    value: int
    min_order: int
    expiry: str


@dataclass
class Invoice:
    invoice_id: str
    table_id: int
    customer_name: str
    items: List[dict]
    subtotal: int
    discount: int
    discount_type: str
    voucher_code: str
    total: int
    payment: int
    change: int
    created_at: str
    employee: str


class DataManager:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    INVOICES_DIR = os.path.join(DATA_DIR, "invoices")

    @staticmethod
    def ensure_dirs():
        os.makedirs(DataManager.DATA_DIR, exist_ok=True)
        os.makedirs(DataManager.INVOICES_DIR, exist_ok=True)

    @staticmethod
    def load_json(filename):
        path = os.path.join(DataManager.DATA_DIR, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    @staticmethod
    def save_json(filename, data):
        path = os.path.join(DataManager.DATA_DIR, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_users():
        return [User(**u) for u in DataManager.load_json("users.json")]

    @staticmethod
    def save_users(users):
        DataManager.save_json("users.json", [asdict(u) for u in users])

    @staticmethod
    def load_menu():
        return [MenuItem(**m) for m in DataManager.load_json("menu.json")]

    @staticmethod
    def save_menu(menu):
        DataManager.save_json("menu.json", [asdict(m) for m in menu])

    @staticmethod
    def load_tables():
        data = DataManager.load_json("tables.json")
        return [Table(t['id'], t.get('status', 'empty'), t.get('order', []), t.get('customer_name', '')) for t in data]

    @staticmethod
    def save_tables(tables):
        DataManager.save_json("tables.json", [{'id': t.id, 'status': t.status, 'order': t.order, 'customer_name': t.customer_name} for t in tables])

    @staticmethod
    def load_vouchers():
        return [Voucher(**v) for v in DataManager.load_json("vouchers.json")]

    @staticmethod
    def save_vouchers(vouchers):
        DataManager.save_json("vouchers.json", [asdict(v) for v in vouchers])

    @staticmethod
    def save_invoice(invoice: Invoice):
        path = os.path.join(DataManager.INVOICES_DIR, f"{invoice.invoice_id}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(asdict(invoice), f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_all_invoices():
        invoices = []
        if os.path.exists(DataManager.INVOICES_DIR):
            for fname in sorted(os.listdir(DataManager.INVOICES_DIR)):
                if fname.endswith('.json'):
                    with open(os.path.join(DataManager.INVOICES_DIR, fname), 'r', encoding='utf-8') as f:
                        invoices.append(Invoice(**json.load(f)))
        return invoices

    @staticmethod
    def init_default_data():
        DataManager.ensure_dirs()

        if not os.path.exists(os.path.join(DataManager.DATA_DIR, "users.json")):
            DataManager.save_users([
                User("admin", "admin123", "admin"),
                User("nhanvien1", "nv123", "employee"),
                User("nhanvien2", "nv456", "employee"),
            ])

        if not os.path.exists(os.path.join(DataManager.DATA_DIR, "menu.json")):
            DataManager.save_menu([
                MenuItem(1, "Ca phe den", "Ca phe", 25000),
                MenuItem(2, "Ca phe sua", "Ca phe", 30000),
                MenuItem(3, "Bac xiu", "Ca phe", 35000),
                MenuItem(4, "Espresso", "Ca phe", 40000),
                MenuItem(5, "Cappuccino", "Ca phe", 45000),
                MenuItem(6, "Tra dao", "Tra", 25000),
                MenuItem(7, "Tra chanh", "Tra", 20000),
                MenuItem(8, "Tra sua tran chau", "Tra", 35000),
                MenuItem(9, "Matcha latte", "Tra", 40000),
                MenuItem(10, "Sinh to bo", "Sinh to", 40000),
                MenuItem(11, "Sinh to xoai", "Sinh to", 35000),
                MenuItem(12, "Sinh to dau", "Sinh to", 35000),
                MenuItem(13, "Nuoc cam ep", "Nuoc ep", 30000),
                MenuItem(14, "Nuoc dua", "Nuoc ep", 25000),
                MenuItem(15, "Banh mi pate", "Banh", 15000),
                MenuItem(16, "Banh bong lan", "Banh", 20000),
                MenuItem(17, "Kem dua", "Trang mieng", 25000),
                MenuItem(18, "Sua chua", "Trang mieng", 15000),
                MenuItem(19, "Nuoc loc", "Nuoc ep", 10000),
                MenuItem(20, "Sting vang", "Nuoc ep", 15000),
            ])

        if not os.path.exists(os.path.join(DataManager.DATA_DIR, "tables.json")):
            DataManager.save_tables([Table(i + 1) for i in range(16)])

        if not os.path.exists(os.path.join(DataManager.DATA_DIR, "vouchers.json")):
            DataManager.save_vouchers([
                Voucher("WELCOME", "percent", 10, 50000, "2026-12-31"),
                Voucher("COFFEE50", "fixed", 5000, 30000, "2026-12-31"),
                Voucher("SALE20", "percent", 20, 100000, "2026-12-31"),
                Voucher("FREESHIP", "fixed", 10000, 100000, "2026-12-31"),
                Voucher("VIP30", "percent", 30, 200000, "2026-12-31"),
                Voucher("SENDAI", "percent", 15, 0, "2026-12-31"),
            ])
