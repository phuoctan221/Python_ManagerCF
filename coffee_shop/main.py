import os
import sys
from datetime import datetime, timedelta
from models import Colors as C
from services import AuthService, MenuService, TableService, OrderService, VoucherService, StatsService
from models import DataManager


def enable_ansi():
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title):
    width = 70
    print(f"{C.CYAN}{'=' * width}{C.RESET}")
    print(f"{C.BOLD}{C.YELLOW}{title:^{width}}{C.RESET}")
    print(f"{C.CYAN}{'=' * width}{C.RESET}")


def print_menu(options, title="MENU"):
    print(f"\n{C.BOLD}{C.BLUE}{'─' * 50}{C.RESET}")
    print(f"{C.BOLD}{C.YELLOW}{title:^50}{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}{'─' * 50}{C.RESET}")
    for i, opt in enumerate(options, 1):
        print(f"  {C.GREEN}{i}.{C.RESET} {opt}")
    print(f"{C.BOLD}{C.BLUE}{'─' * 50}{C.RESET}")


def get_int(prompt, min_val=None, max_val=None):
    while True:
        try:
            val = int(input(f"{C.YELLOW}{prompt}{C.RESET}"))
            if min_val is not None and val < min_val:
                print(f"{C.RED}Vui long nhap so >= {min_val}{C.RESET}")
                continue
            if max_val is not None and val > max_val:
                print(f"{C.RED}Vui long nhap so <= {max_val}{C.RESET}")
                continue
            return val
        except ValueError:
            print(f"{C.RED}Vui long nhap so hop le!{C.RESET}")


def get_input(prompt):
    return input(f"{C.YELLOW}{prompt}{C.RESET}").strip()


def format_currency(amount):
    return f"{amount:>10,}đ"


def show_login(auth):
    clear()
    print_header("QUAN LY QUAN CAFE - DANG NHAP")
    print(f"\n{C.DIM}Tai khoan mac dinh: admin / admin123 hoac nhanvien1 / nv123{C.RESET}\n")

    username = get_input("Ten dang nhap: ")
    password = get_input("Mat khau: ")

    user = auth.login(username, password)
    if user:
        print(f"\n{C.GREEN}{C.BOLD}Dang nhap thanh cong! Xin chao {user.username} ({user.role}){C.RESET}")
        input(f"\n{C.DIM}Nhan Enter de tiep tuc...{C.RESET}")
        return True
    else:
        print(f"\n{C.RED}{C.BOLD}Sai ten dang nhap hoac mat khau!{C.RESET}")
        input(f"\n{C.DIM}Nhan Enter de thu lai...{C.RESET}")
        return False


def show_menu_management():
    menu_service = MenuService()
    while True:
        clear()
        print_header("QUAN LY THUC DON")
        print_menu([
            "Xem thuc don",
            "Them mon moi",
            "Sua mon",
            "Xoa mon",
            "Quay lai"
        ], "QUAN LY THUC DON")

        choice = get_int("Chon chuc nang: ", 1, 5)

        if choice == 1:
            view_menu(menu_service)
        elif choice == 2:
            add_menu_item(menu_service)
        elif choice == 3:
            edit_menu_item(menu_service)
        elif choice == 4:
            delete_menu_item(menu_service)
        elif choice == 5:
            break


def view_menu(menu_service=None, show_back=True):
    if not menu_service:
        menu_service = MenuService()
    clear()
    print_header("THUC DON")
    categories = menu_service.get_categories()

    for cat in categories:
        items = menu_service.get_by_category(cat)
        print(f"\n{C.BOLD}{C.MAGENTA}--- {cat} ---{C.RESET}")
        print(f"{C.BLUE}{'ID':<5}{'Ten':<25}{'Gia':>15}{C.RESET}")
        print(f"{C.DIM}{'-' * 45}{C.RESET}")
        for item in items:
            print(f"{item.id:<5}{item.name:<25}{format_currency(item.price)}")

    if show_back:
        input(f"\n{C.DIM}Nhan Enter de tiep tuc...{C.RESET}")


def add_menu_item(menu_service):
    clear()
    print_header("THEM MON MOI")
    name = get_input("Ten mon: ")
    if not name:
        print(f"{C.RED}Ten mon khong duoc de trong!{C.RESET}")
        input("Nhan Enter...")
        return

    categories = menu_service.get_categories()
    print(f"\n{C.BOLD}Danh muc co san:{C.RESET}")
    for i, cat in enumerate(categories, 1):
        print(f"  {i}. {cat}")
    print(f"  {len(categories) + 1}. Them danh muc moi")

    choice = get_int("Chon danh muc: ", 1, len(categories) + 1)
    if choice == len(categories) + 1:
        category = get_input("Nhap ten danh muc moi: ")
    else:
        category = categories[choice - 1]

    price = get_int("Gia (VND): ", 1000)
    menu_service.add_item(name, category, price)
    print(f"\n{C.GREEN}Da them mon '{name}' thanh cong!{C.RESET}")
    input("\nNhan Enter de tiep tuc...")


def edit_menu_item(menu_service):
    clear()
    print_header("SUA MON")
    view_menu(menu_service, show_back=False)
    item_id = get_int("\nNhap ID mon can sua: ", 1)
    item = menu_service.get_by_id(item_id)
    if not item:
        print(f"{C.RED}Khong tim thay mon!{C.RESET}")
        input("Nhan Enter...")
        return

    print(f"\nThong tin hien tai: {item.name} - {item.category} - {item.price}đ")
    name = get_input(f"Ten moi ({item.name}): ") or item.name
    category = get_input(f"Danh muc moi ({item.category}): ") or item.category
    price_str = get_input(f"Gia moi ({item.price}): ")
    price = int(price_str) if price_str else item.price

    menu_service.update_item(item_id, name, category, price)
    print(f"{C.GREEN}Da cap nhat mon thanh cong!{C.RESET}")
    input("Nhan Enter...")


def delete_menu_item(menu_service):
    clear()
    print_header("XOA MON")
    view_menu(menu_service, show_back=False)
    item_id = get_int("\nNhap ID mon can xoa: ", 1)
    item = menu_service.get_by_id(item_id)
    if not item:
        print(f"{C.RED}Khong tim thay mon!{C.RESET}")
        input("Nhan Enter...")
        return

    confirm = get_input(f"Ban chac chan xoa '{item.name}'? (y/N): ")
    if confirm.lower() == 'y':
        menu_service.delete_item(item_id)
        print(f"{C.GREEN}Da xoa mon thanh cong!{C.RESET}")
    else:
        print(f"{C.YELLOW}Da huy xoa!{C.RESET}")
    input("Nhan Enter...")


def show_table_diagram():
    tables = TableService.get_all()
    clear()
    print_header("SO DO BAN")
    print()

    cols = 4
    for i in range(0, len(tables), cols):
        row_tables = tables[i:i + cols]
        row_parts = []
        for t in row_tables:
            if t.status == "empty":
                row_parts.append(f"{C.GREEN}[  Ban {t.id:>2}  ]{C.RESET}")
            else:
                row_parts.append(f"{C.RED}[X Ban {t.id:>2} X]{C.RESET}")
        print("   ".join(row_parts))

    print(f"\n  {C.GREEN}[  Trong  ]{C.RESET}     {C.RED}[X Co khach X]{C.RESET}")
    total = len(tables)
    empty = sum(1 for t in tables if t.status == "empty")
    occupied = total - empty
    print(f"\n  Tong: {total} ban | {C.GREEN}Con {empty} ban{C.RESET} | {C.RED}Co khach: {occupied} ban{C.RESET}")
    return tables


def show_table_management(auth):
    table_service = TableService()
    while True:
        clear()
        print_header("QUAN LY BAN")
        tables = show_table_diagram()

        options = [
            "Chon ban dat khach",
            "Xem chi tiet ban",
            "Tra ban",
            "Gop ban",
            "Quay lai"
        ]
        if auth.is_admin():
            options.append("Chuyen ban")
        print_menu(options, "QUAN LY BAN")

        max_choice = len(options)
        choice = get_int("Chon chuc nang: ", 1, max_choice)

        if choice == 1:
            assign_table(table_service)
        elif choice == 2:
            view_table_detail(table_service)
        elif choice == 3:
            free_table(table_service)
        elif choice == 4:
            merge_tables(table_service)
        elif choice == 5:
            break
        elif choice == 6 and auth.is_admin():
            transfer_table(table_service)


def assign_table(table_service):
    clear()
    print_header("DAT KHACH")
    table_id = get_int("Nhap so ban: ", 1, 16)
    table = table_service.get_by_id(table_id)
    if not table:
        print(f"{C.RED}Khong tim thay ban!{C.RESET}")
        input("Nhan Enter...")
        return
    if table.status == "occupied":
        print(f"{C.RED}Ban {table_id} da co khach!{C.RESET}")
        input("Nhan Enter...")
        return

    name = get_input("Ten khach hang: ")
    if not name:
        name = f"Khach Ban {table_id}"
    table_service.assign_table(table_id, name)
    print(f"{C.GREEN}Da dat ban {table_id} cho {name}!{C.RESET}")
    input("Nhan Enter...")


def view_table_detail(table_service):
    clear()
    print_header("CHI TIET BAN")
    table_id = get_int("Nhap so ban: ", 1, 16)
    table = table_service.get_by_id(table_id)
    if not table:
        print(f"{C.RED}Khong tim thay ban!{C.RESET}")
        input("Nhan Enter...")
        return

    print(f"\n{C.BOLD}Ban {table.id}:{C.RESET}")
    print(f"  Trang thai: {'Co khach' if table.status == 'occupied' else 'Trong'}")
    if table.customer_name:
        print(f"  Khach: {table.customer_name}")

    if table.order:
        print(f"\n  {C.CYAN}Mon da goi:{C.RESET}")
        print(f"  {'STT':<5}{'Ten':<25}{'SL':<5}{'Gia':<12}{'Thanh tien':<15}{'Ghi chu'}")
        print(f"  {'-' * 75}")
        for i, item in enumerate(table.order, 1):
            subtotal = item['price'] * item['quantity']
            note = item.get('note', '') or ''
            print(f"  {i:<5}{item['name']:<25}{item['quantity']:<5}{format_currency(item['price']):<12}{format_currency(subtotal):<15}{note}")

        total = OrderService.calculate_subtotal(table)
        print(f"\n  {C.BOLD}{'Tong cong:':<47}{format_currency(total)}{C.RESET}")

    input("\nNhan Enter...")


def free_table(table_service):
    clear()
    print_header("TRA BAN")
    table_id = get_int("Nhap so ban: ", 1, 16)
    table = table_service.get_by_id(table_id)
    if not table or table.status == "empty":
        print(f"{C.RED}Ban nay dang trong!{C.RESET}")
        input("Nhan Enter...")
        return

    confirm = get_input(f"Tra ban {table_id} (khach: {table.customer_name})? (y/N): ")
    if confirm.lower() == 'y':
        table_service.free_table(table_id)
        print(f"{C.GREEN}Da tra ban {table_id}!{C.RESET}")
    else:
        print(f"{C.YELLOW}Da huy!{C.RESET}")
    input("Nhan Enter...")


def merge_tables(table_service):
    clear()
    print_header("GOP BAN")
    show_table_diagram()

    source_str = get_input("Nhap cac ban can gop (vd: 1,2,3): ")
    target_id = get_int("Nhap ban dich: ", 1, 16)

    source_ids = []
    for s in source_str.split(','):
        s = s.strip()
        if s:
            try:
                source_ids.append(int(s))
            except:
                pass

    if not source_ids:
        print(f"{C.RED}Danh sach ban khong hop le!{C.RESET}")
        input("Nhan Enter...")
        return

    source_ids = [s for s in source_ids if s != target_id]
    if not source_ids:
        print(f"{C.RED}Khong co ban nao de gop!{C.RESET}")
        input("Nhan Enter...")
        return

    table_service.merge_tables(source_ids, target_id)
    print(f"{C.GREEN}Da gop cac ban {', '.join(map(str, source_ids))} vao ban {target_id}!{C.RESET}")
    input("Nhan Enter...")


def transfer_table(table_service):
    clear()
    print_header("CHUYEN BAN")
    show_table_diagram()

    from_id = get_int("Chuyen tu ban: ", 1, 16)
    to_id = get_int("Den ban: ", 1, 16)

    if from_id == to_id:
        print(f"{C.RED}Cung mot ban!{C.RESET}")
        input("Nhan Enter...")
        return

    from_table = table_service.get_by_id(from_id)
    to_table = table_service.get_by_id(to_id)

    if not from_table or from_table.status != "occupied":
        print(f"{C.RED}Ban nguon khong co khach!{C.RESET}")
        input("Nhan Enter...")
        return

    if to_table.status != "empty":
        print(f"{C.RED}Ban dich dang co khach!{C.RESET}")
        input("Nhan Enter...")
        return

    tables = TableService.get_all()
    for t in tables:
        if t.id == from_id:
            t.status = "empty"
            t2 = None
            for tt in tables:
                if tt.id == to_id:
                    t2 = tt
                    break
            if t2:
                t2.status = "occupied"
                t2.customer_name = t.customer_name
                t2.order = t.order
                t.status = "empty"
                t.order = []
                t.customer_name = ""
                break
    DataManager.save_tables(tables)
    print(f"{C.GREEN}Da chuyen khach tu ban {from_id} sang ban {to_id}!{C.RESET}")
    input("Nhan Enter...")


def show_order_screen(auth):
    table_service = TableService()
    menu_service = MenuService()
    order_service = OrderService()

    while True:
        clear()
        print_header("GOI MON")
        tables = show_table_diagram()

        print_menu([
            "Chon ban de goi mon",
            "Xem hoa don ban",
            "Xoa mon khoi hoa don",
            "Quay lai"
        ], "GOI MON")

        choice = get_int("Chon chuc nang: ", 1, 4)

        if choice == 1:
            take_order(table_service, menu_service, order_service)
        elif choice == 2:
            view_bill(table_service)
        elif choice == 3:
            remove_order_item(table_service)
        elif choice == 4:
            break


def take_order(table_service, menu_service, order_service):
    clear()
    print_header("GOI MON")
    table_id = get_int("Nhap so ban: ", 1, 16)
    table = table_service.get_by_id(table_id)
    if not table or table.status != "occupied":
        print(f"{C.RED}Ban chua co khach hoac khong ton tai!{C.RESET}")
        input("Nhan Enter...")
        return

    while True:
        clear()
        print_header(f"GOI MON - Ban {table_id} ({table.customer_name})")
        categories = menu_service.get_categories()
        print(f"\n{C.BOLD}Danh muc:{C.RESET}")
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat}")

        cat_choice = get_int(f"\nChon danh muc (1-{len(categories)}), 0 de ket thuc: ", 0, len(categories))
        if cat_choice == 0:
            break

        category = categories[cat_choice - 1]
        items = menu_service.get_by_category(category)

        clear()
        print_header(f"{category}")
        print(f"{C.BLUE}{'ID':<5}{'Ten':<25}{'Gia':>15}{C.RESET}")
        print(f"{C.DIM}{'-' * 45}{C.RESET}")
        for item in items:
            print(f"{C.GREEN}{item.id:<5}{C.RESET}{item.name:<25}{format_currency(item.price)}")

        item_id = get_int("\nNhap ID mon: ", 1)
        item = menu_service.get_by_id(item_id)
        if not item:
            print(f"{C.RED}Khong tim thay mon!{C.RESET}")
            input("Nhan Enter...")
            continue

        quantity = get_int("So luong: ", 1, 100)
        note = get_input("Ghi chu (neu co): ")

        order_service.add_item_to_table(table_id, item, quantity, note)
        print(f"{C.GREEN}Da them {quantity} {item.name} vao ban {table_id}!{C.RESET}")

        cont = get_input("Goi them mon khac? (y/N): ")
        if cont.lower() != 'y':
            break


def view_bill(table_service):
    clear()
    print_header("XEM HOA DON")
    table_id = get_int("Nhap so ban: ", 1, 16)
    table = table_service.get_by_id(table_id)
    if not table or not table.order:
        print(f"{C.RED}Ban khong co mon nao!{C.RESET}")
        input("Nhan Enter...")
        return

    print(f"\n{C.BOLD}HOA DON BAN {table_id} - {table.customer_name}{C.RESET}")
    print(f"{C.DIM}{'=' * 60}{C.RESET}")
    print(f"{'STT':<5}{'Ten':<25}{'SL':<5}{'Gia':<12}{'Thanh tien':<15}")
    print(f"{C.DIM}{'-' * 60}{C.RESET}")
    for i, item in enumerate(table.order, 1):
        subtotal = item['price'] * item['quantity']
        note = item.get('note', '') or ''
        note_str = f" ({note})" if note else ''
        print(f"{i:<5}{item['name']:<25}{item['quantity']:<5}{format_currency(item['price']):<12}{format_currency(subtotal)}")
        if note:
            print(f"{'':5}{C.DIM}Ghi chu: {note}{C.RESET}")

    total = OrderService.calculate_subtotal(table)
    print(f"{C.DIM}{'-' * 60}{C.RESET}")
    print(f"{C.BOLD}{'Tong cong:':<47}{format_currency(total)}{C.RESET}")
    input("\nNhan Enter...")


def remove_order_item(table_service):
    clear()
    print_header("XOA MON KHOI HOA DON")
    table_id = get_int("Nhap so ban: ", 1, 16)
    table = table_service.get_by_id(table_id)
    if not table or not table.order:
        print(f"{C.RED}Ban khong co mon nao!{C.RESET}")
        input("Nhan Enter...")
        return

    print(f"\n{C.BOLD}Cac mon ban {table_id}:{C.RESET}")
    for i, item in enumerate(table.order, 1):
        print(f"  {i}. {item['name']} x{item['quantity']} - {format_currency(item['price'] * item['quantity'])}")

    idx = get_int("\nChon STT mon can xoa (0 de huy): ", 0, len(table.order))
    if idx == 0:
        return

    table_service2 = TableService()
    tables = table_service2.get_all()
    for t in tables:
        if t.id == table_id:
            if 0 <= idx - 1 < len(t.order):
                removed = t.order.pop(idx - 1)
                DataManager.save_tables(tables)
                print(f"{C.GREEN}Da xoa '{removed['name']}' khoi hoa don!{C.RESET}")
            break
    input("Nhan Enter...")


def show_billing_screen(auth):
    voucher_service = VoucherService()
    order_service = OrderService()
    table_service = TableService()

    while True:
        clear()
        print_header("TINH TIEN")
        tables = show_table_diagram()
        print_menu([
            "Chon ban de tinh tien",
            "Quay lai"
        ], "TINH TIEN")

        choice = get_int("Chon chuc nang: ", 1, 2)
        if choice == 1:
            process_bill(auth, voucher_service, order_service, table_service)
        elif choice == 2:
            break


def process_bill(auth, voucher_service, order_service, table_service):
    clear()
    print_header("TINH TIEN")
    table_id = get_int("Nhap so ban: ", 1, 16)
    table = table_service.get_by_id(table_id)
    if not table or table.status != "occupied" or not table.order:
        print(f"{C.RED}Ban khong co mon hoac dang trong!{C.RESET}")
        input("Nhan Enter...")
        return

    subtotal = OrderService.calculate_subtotal(table)

    print(f"\n{C.BOLD}HOA DON BAN {table_id} - {table.customer_name}{C.RESET}")
    print(f"{C.DIM}{'=' * 60}{C.RESET}")
    print(f"{'Ten':<25}{'SL':<5}{'Gia':<12}{'Thanh tien':<15}")
    print(f"{C.DIM}{'-' * 60}{C.RESET}")
    for item in table.order:
        subtotal_item = item['price'] * item['quantity']
        note = item.get('note', '') or ''
        print(f"{item['name']:<25}{item['quantity']:<5}{format_currency(item['price']):<12}{format_currency(subtotal_item)}")
        if note:
            print(f"{C.DIM}  Ghi chu: {note}{C.RESET}")

    print(f"{C.DIM}{'-' * 60}{C.RESET}")
    print(f"{C.BOLD}{'TAM TINH:':<47}{format_currency(subtotal)}{C.RESET}")

    voucher_code = ""
    discount = 0
    discount_type = "none"
    voucher = None

    use_voucher = get_input("\nCo ma giam gia khong? (y/N): ")
    if use_voucher.lower() == 'y':
        voucher_code = get_input("Nhap ma giam gia: ")
        valid, result = voucher_service.validate(voucher_code, subtotal)
        if valid:
            voucher = result
            discount = voucher_service.apply(voucher, subtotal)
            discount_type = "voucher"
            print(f"{C.GREEN}Ma giam gia hop le! Giam {discount:,}đ ({voucher.type} - {voucher.value}{'%' if voucher.type == 'percent' else 'đ'}){C.RESET}")
        else:
            print(f"{C.RED}{result}{C.RESET}")
            voucher_code = ""
            use_manual = get_input("Co ap dung giam gia thu cong khong? (y/N): ")
            if use_manual.lower() == 'y':
                manual = get_int("Nhap so tien giam: ", 0, subtotal)
                if manual > 0:
                    discount = manual
                    discount_type = "manual"
                    print(f"{C.YELLOW}Giam gia thu cong: {format_currency(discount)}{C.RESET}")
    else:
        use_manual = get_input("Co ap dung giam gia thu cong khong? (y/N): ")
        if use_manual.lower() == 'y':
            manual = get_int("Nhap so tien giam: ", 0, subtotal)
            if manual > 0:
                discount = manual
                discount_type = "manual"
                print(f"{C.YELLOW}Giam gia thu cong: {format_currency(discount)}{C.RESET}")

    total = subtotal - discount
    print(f"\n{C.BOLD}{'THANH TOAN':=^60}{C.RESET}")
    print(f"  {'Tam tinh:':<30}{format_currency(subtotal)}")
    print(f"  {'Giam gia:':<30}{format_currency(discount)}")
    print(f"  {C.BOLD}{C.GREEN}{'TONG CONG:':<30}{format_currency(total)}{C.RESET}")

    payment = get_int(f"\nKhach dua: ", total)
    change = payment - total
    print(f"  {'Tien thua:':<30}{format_currency(change)}")

    confirm = get_input(f"\nXac nhan thanh toan? (Y/n): ")
    if confirm.lower() == 'n':
        print(f"{C.YELLOW}Da huy thanh toan!{C.RESET}")
        input("Nhan Enter...")
        return

    invoice = order_service.save_invoice(
        table, discount, discount_type, voucher_code,
        total, payment, change, auth.current_user.username
    )

    table_service.free_table(table_id)

    print(f"\n{C.GREEN}{C.BOLD}{'=' * 60}{C.RESET}")
    print(f"{C.GREEN}{C.BOLD}{'HOA DON THANH TOAN':^60}{C.RESET}")
    print(f"{C.GREEN}{C.BOLD}{'=' * 60}{C.RESET}")
    print(f"  Ma HD: {invoice.invoice_id}")
    print(f"  Ban: {table_id} | Khach: {table.customer_name}")
    print(f"  Nhan vien: {auth.current_user.username}")
    print(f"  Thoi gian: {invoice.created_at}")
    print(f"{C.DIM}{'-' * 60}{C.RESET}")
    for item in table.order:
        subtotal_item = item['price'] * item['quantity']
        print(f"  {item['name']:<25}x{item['quantity']:<5}{format_currency(subtotal_item)}")
    print(f"{C.DIM}{'-' * 60}{C.RESET}")
    print(f"  {'Tong:':<35}{format_currency(subtotal)}")
    if discount > 0:
        print(f"  {'Giam gia:':<35}{format_currency(discount)}")
    print(f"  {C.BOLD}{'Phai tra:':<35}{format_currency(total)}{C.RESET}")
    print(f"  {'Khach dua:':<35}{format_currency(payment)}")
    print(f"  {C.GREEN}{'Tien thua:':<35}{format_currency(change)}{C.RESET}")
    print(f"{C.GREEN}{'=' * 60}{C.RESET}")
    print(f"\n{C.BOLD}{C.GREEN}Da luu hoa don thanh cong!{C.RESET}")
    input("\nNhan Enter...")


def show_voucher_management():
    voucher_service = VoucherService()
    while True:
        clear()
        print_header("QUAN LY MA GIAM GIA")
        vouchers = voucher_service.get_all()

        if vouchers:
            print(f"\n{C.BOLD}Danh sach ma giam gia:{C.RESET}")
            print(f"{C.BLUE}{'Ma':<15}{'Loai':<10}{'Gia tri':<12}{'DH toi thieu':<15}{'Han su dung'}{C.RESET}")
            print(f"{C.DIM}{'-' * 65}{C.RESET}")
            for v in vouchers:
                val_str = f"{v.value}{'%' if v.type == 'percent' else 'đ'}"
                print(f"{v.code:<15}{v.type:<10}{val_str:<12}{format_currency(v.min_order):<15}{v.expiry}")
        else:
            print(f"\n{C.YELLOW}Chua co ma giam gia nao!{C.RESET}")

        print_menu([
            "Them ma giam gia",
            "Quay lai"
        ], "MA GIAM GIA")

        choice = get_int("Chon chuc nang: ", 1, 2)
        if choice == 1:
            add_voucher(voucher_service)
        elif choice == 2:
            break


def add_voucher(voucher_service):
    clear()
    print_header("THEM MA GIAM GIA")
    code = get_input("Nhap ma giam gia: ").upper()
    if not code:
        print(f"{C.RED}Ma khong duoc de trong!{C.RESET}")
        input("Nhan Enter...")
        return

    print("\nLoai giam gia:")
    print("  1. Phan tram (%)")
    print("  2. Tien mat (VND)")
    type_choice = get_int("Chon loai: ", 1, 2)
    v_type = "percent" if type_choice == 1 else "fixed"

    value = get_int("Gia tri giam: ", 1000 if v_type == "fixed" else 1)
    min_order = get_int("Don hang toi thieu (0 = khong gioi han): ", 0)
    year = get_int("Nam het han (vd: 2026): ", 2025, 2030)
    month = get_int("Thang het han (1-12): ", 1, 12)
    day = get_int("Ngay het han (1-31): ", 1, 31)
    expiry = f"{year}-{month:02d}-{day:02d}"

    voucher_service.add_voucher(code, v_type, value, min_order, expiry)
    print(f"{C.GREEN}Da them ma giam gia '{code}' thanh cong!{C.RESET}")
    input("Nhan Enter...")


def show_statistics(auth):
    stats_service = StatsService()

    while True:
        clear()
        print_header("THONG KE")

        print_menu([
            "Top mon ban chay",
            "Mon it duoc goi nhat",
            "Tong doanh thu",
            "Doanh thu theo mon",
            "Doanh thu theo ngay (7 ngay gan nhat)",
            "Thong ke theo khoang thoi gian",
            "Quay lai"
        ], "THONG KE")

        choice = get_int("Chon chuc nang: ", 1, 7)

        if choice == 1:
            show_top_selling(stats_service)
        elif choice == 2:
            show_least_sold(stats_service)
        elif choice == 3:
            show_total_revenue(stats_service)
        elif choice == 4:
            show_revenue_by_item(stats_service)
        elif choice == 5:
            show_daily_revenue(stats_service)
        elif choice == 6:
            show_stats_by_date(stats_service)
        elif choice == 7:
            break


def show_top_selling(stats_service):
    clear()
    print_header("TOP MON BAN CHAY")
    top, _ = stats_service.get_top_selling(limit=10)

    if not top:
        print(f"\n{C.YELLOW}Chua co du lieu!{C.RESET}")
    else:
        print(f"\n{C.BOLD}{'STT':<5}{'Ten mon':<25}{'So luong':<15}{C.RESET}")
        print(f"{C.DIM}{'-' * 45}{C.RESET}")
        for i, (name, qty) in enumerate(top, 1):
            print(f"{i:<5}{name:<25}{qty:<15}")
    input("\nNhan Enter...")


def show_least_sold(stats_service):
    clear()
    print_header("MON IT DUOC GOI NHAT")
    _, least = stats_service.get_top_selling(limit=5)

    if not least:
        print(f"\n{C.YELLOW}Chua co du lieu!{C.RESET}")
    else:
        print(f"\n{C.BOLD}{'STT':<5}{'Ten mon':<25}{'So luong':<15}{C.RESET}")
        print(f"{C.DIM}{'-' * 45}{C.RESET}")
        for i, (name, qty) in enumerate(least, 1):
            print(f"{i:<5}{name:<25}{qty:<15}")
    input("\nNhan Enter...")


def show_total_revenue(stats_service):
    clear()
    print_header("TONG DOANH THU")
    total, _, count = stats_service.get_revenue()

    print(f"\n  {C.BOLD}{'Tong so hoa don:':<30}{count}{C.RESET}")
    print(f"  {C.BOLD}{C.GREEN}{'Tong doanh thu:':<30}{format_currency(total)}{C.RESET}")
    if count > 0:
        print(f"  {'Trung binh / hoa don:':<30}{format_currency(total // count)}")
    input("\nNhan Enter...")


def show_revenue_by_item(stats_service):
    clear()
    print_header("DOANH THU THEO MON")
    _, revenue_by_item, _ = stats_service.get_revenue()

    if not revenue_by_item:
        print(f"\n{C.YELLOW}Chua co du lieu!{C.RESET}")
    else:
        sorted_rev = sorted(revenue_by_item.items(), key=lambda x: x[1], reverse=True)
        print(f"\n{C.BOLD}{'STT':<5}{'Ten mon':<25}{'Doanh thu':<15}{C.RESET}")
        print(f"{C.DIM}{'-' * 45}{C.RESET}")
        for i, (name, rev) in enumerate(sorted_rev, 1):
            print(f"{i:<5}{name:<25}{format_currency(rev)}")

        total = sum(rev for _, rev in sorted_rev)
        print(f"{C.DIM}{'-' * 45}{C.RESET}")
        print(f"{C.BOLD}{'Tong:':<30}{format_currency(total)}{C.RESET}")
    input("\nNhan Enter...")


def show_daily_revenue(stats_service):
    clear()
    print_header("DOANH THU 7 NGAY GAN NHAT")
    daily = stats_service.get_daily_revenue(7)

    print(f"\n{C.BOLD}{'Ngay':<15}{'Doanh thu':<15}{C.RESET}")
    print(f"{C.DIM}{'-' * 30}{C.RESET}")
    for day, rev in daily.items():
        print(f"{day:<15}{format_currency(rev)}")

    total = sum(daily.values())
    print(f"{C.DIM}{'-' * 30}{C.RESET}")
    print(f"{C.BOLD}{'Tong:':<15}{format_currency(total)}{C.RESET}")
    input("\nNhan Enter...")


def show_stats_by_date(stats_service):
    clear()
    print_header("THONG KE THEO KHOANG THOI GIAN")

    print(f"\n{C.BOLD}Tu ngay:{C.RESET}")
    from_y = get_int("  Nam: ", 2020, 2030)
    from_m = get_int("  Thang: ", 1, 12)
    from_d = get_int("  Ngay: ", 1, 31)

    print(f"\n{C.BOLD}Den ngay:{C.RESET}")
    to_y = get_int("  Nam: ", 2020, 2030)
    to_m = get_int("  Thang: ", 1, 12)
    to_d = get_int("  Ngay: ", 1, 31)

    from_date = datetime(from_y, from_m, from_d)
    to_date = datetime(to_y, to_m, to_d)

    if from_date > to_date:
        print(f"{C.RED}Ngay bat dau phai truoc ngay ket thuc!{C.RESET}")
        input("Nhan Enter...")
        return

    total, rev_by_item, count = stats_service.get_revenue(from_date, to_date)
    top, least = stats_service.get_top_selling(from_date, to_date, limit=5)

    clear()
    print_header(f"THONG KE TU {from_date.strftime('%d/%m/%Y')} DEN {to_date.strftime('%d/%m/%Y')}")

    print(f"\n{C.BOLD}1. TONG QUAN{C.RESET}")
    print(f"  {C.DIM}{'-' * 40}{C.RESET}")
    print(f"  So hoa don: {count}")
    print(f"  {C.GREEN}{C.BOLD}Tong doanh thu: {format_currency(total)}{C.RESET}")

    if top:
        print(f"\n{C.BOLD}2. TOP MON BAN CHAY{C.RESET}")
        print(f"  {C.DIM}{'-' * 40}{C.RESET}")
        for i, (name, qty) in enumerate(top, 1):
            print(f"  {i}. {name:<25} - {qty} luot")

    if least and least != top:
        print(f"\n{C.BOLD}3. MON IT DUOC GOI{C.RESET}")
        print(f"  {C.DIM}{'-' * 40}{C.RESET}")
        for i, (name, qty) in enumerate(least, 1):
            print(f"  {i}. {name:<25} - {qty} luot")

    if rev_by_item:
        print(f"\n{C.BOLD}4. DOANH THU THEO MON{C.RESET}")
        print(f"  {C.DIM}{'-' * 40}{C.RESET}")
        sorted_rev = sorted(rev_by_item.items(), key=lambda x: x[1], reverse=True)
        for name, rev in sorted_rev:
            print(f"  {name:<25}{format_currency(rev)}")

    input("\nNhan Enter...")


def show_user_management(auth):
    while True:
        clear()
        print_header("QUAN LY NGUOI DUNG")
        users = auth.list_users()

        if users:
            print(f"\n{C.BOLD}Danh sach nguoi dung:{C.RESET}")
            print(f"{C.BLUE}{'STT':<5}{'Ten dang nhap':<20}{'Vai tro':<15}{C.RESET}")
            print(f"{C.DIM}{'-' * 40}{C.RESET}")
            for i, u in enumerate(users, 1):
                role_str = f"{C.GREEN}Admin{C.RESET}" if u.role == "admin" else f"{C.YELLOW}Nhan vien{C.RESET}"
                print(f"{i:<5}{u.username:<20}{role_str}")

        print_menu([
            "Them nguoi dung",
            "Xoa nguoi dung",
            "Doi mat khau",
            "Quay lai"
        ], "QUAN LY NGUOI DUNG")

        choice = get_int("Chon chuc nang: ", 1, 4)

        if choice == 1:
            add_user(auth)
        elif choice == 2:
            delete_user(auth)
        elif choice == 3:
            change_password(auth)
        elif choice == 4:
            break


def add_user(auth):
    clear()
    print_header("THEM NGUOI DUNG")
    username = get_input("Ten dang nhap: ")
    if not username:
        print(f"{C.RED}Ten khong duoc de trong!{C.RESET}")
        input("Nhan Enter...")
        return

    password = get_input("Mat khau: ")
    if not password:
        print(f"{C.RED}Mat khau khong duoc de trong!{C.RESET}")
        input("Nhan Enter...")
        return

    print("\nVai tro:")
    print("  1. Admin")
    print("  2. Nhan vien")
    role_choice = get_int("Chon vai tro: ", 1, 2)
    role = "admin" if role_choice == 1 else "employee"

    if auth.add_user(username, password, role):
        print(f"{C.GREEN}Da them nguoi dung '{username}' thanh cong!{C.RESET}")
    else:
        print(f"{C.RED}Ten dang nhap da ton tai!{C.RESET}")
    input("Nhan Enter...")


def delete_user(auth):
    clear()
    print_header("XOA NGUOI DUNG")
    username = get_input("Nhap ten nguoi dung can xoa: ")
    if auth.delete_user(username):
        print(f"{C.GREEN}Da xoa nguoi dung '{username}'!{C.RESET}")
    else:
        print(f"{C.RED}Khong the xoa (khong tim thay hoac dang la tai khoan hien tai)!{C.RESET}")
    input("Nhan Enter...")


def change_password(auth):
    clear()
    print_header("DOI MAT KHAU")
    old_pw = get_input("Mat khau cu: ")
    new_pw = get_input("Mat khau moi: ")
    confirm = get_input("Xac nhan mat khau moi: ")

    if new_pw != confirm:
        print(f"{C.RED}Mat khau xac nhan khong khop!{C.RESET}")
    elif auth.change_password(old_pw, new_pw):
        print(f"{C.GREEN}Doi mat khau thanh cong!{C.RESET}")
    else:
        print(f"{C.RED}Sai mat khau cu!{C.RESET}")
    input("Nhan Enter...")


def admin_menu(auth):
    while True:
        clear()
        print_header(f"QUAN LY QUAN CAFE")
        print(f"\n{C.BOLD}{C.GREEN}  Xin chao Admin: {auth.current_user.username}{C.RESET}")
        print_menu([
            "Quan ly thuc don (Them/Sua/Xoa mon)",
            "Quan ly ban (So do ban/Dat/Tra/Gop/Chuyen ban)",
            "Goi mon",
            "Tinh tien",
            "Quan ly ma giam gia (Voucher)",
            "Thong ke",
            "Quan ly nguoi dung",
            "Dang xuat"
        ], "MENU CHINH - ADMIN")

        choice = get_int("Chon chuc nang: ", 1, 8)

        if choice == 1:
            show_menu_management()
        elif choice == 2:
            show_table_management(auth)
        elif choice == 3:
            show_order_screen(auth)
        elif choice == 4:
            show_billing_screen(auth)
        elif choice == 5:
            show_voucher_management()
        elif choice == 6:
            show_statistics(auth)
        elif choice == 7:
            show_user_management(auth)
        elif choice == 8:
            auth.logout()
            break


def employee_menu(auth):
    while True:
        clear()
        print_header(f"QUAN LY QUAN CAFE")
        print(f"\n{C.BOLD}{C.YELLOW}  Xin chao Nhan vien: {auth.current_user.username}{C.RESET}")
        print_menu([
            "Xem thuc don",
            "Xem so do ban",
            "Goi mon",
            "Tinh tien",
            "Xem thong ke",
            "Doi mat khau",
            "Dang xuat"
        ], "MENU CHINH - NHAN VIEN")

        choice = get_int("Chon chuc nang: ", 1, 7)

        if choice == 1:
            view_menu()
        elif choice == 2:
            clear()
            show_table_diagram()
            input(f"\n{C.DIM}Nhan Enter de tiep tuc...{C.RESET}")
        elif choice == 3:
            show_order_screen(auth)
        elif choice == 4:
            show_billing_screen(auth)
        elif choice == 5:
            show_statistics(auth)
        elif choice == 6:
            change_password(auth)
        elif choice == 7:
            auth.logout()
            break


def main():
    enable_ansi()
    DataManager.init_default_data()

    auth = AuthService()
    while True:
        if show_login(auth):
            if auth.is_admin():
                admin_menu(auth)
            else:
                employee_menu(auth)
        else:
            cont = get_input("Ban muon thu lai khong? (Y/n): ")
            if cont.lower() == 'n':
                break


if __name__ == '__main__':
    main()
