// ==================== UTILITIES ====================
function showToast(message, type) {
    type = type || 'success';
    const icons = { success: 'bi-check-circle-fill', danger: 'bi-exclamation-circle-fill', warning: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill' };
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const id = 't' + Date.now();
    container.innerHTML += `<div id="${id}" class="toast align-items-center text-bg-${type} border-0 fade-in" role="alert">
        <div class="d-flex"><div class="toast-body"><i class="bi ${icons[type] || icons.info} me-2"></i>${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div></div>`;
    setTimeout(() => {
        const el = document.getElementById(id);
        if (el) { el.classList.remove('show'); setTimeout(() => el.remove(), 300); }
    }, 3000);
    const bsToast = new bootstrap.Toast(document.getElementById(id));
    bsToast.show();
}

function fmtMoney(n) { return (n || 0).toLocaleString('vi-VN') + 'đ'; }

// ==================== API HELPER ====================
async function api(url, method, body) {
    const opts = { method: method || 'GET', headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    try {
        const res = await fetch(url, opts);
        if (res.redirected) { window.location.href = res.url; return null; }
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return await res.json();
    } catch (e) {
        showToast('Lỗi: ' + e.message, 'danger');
        return null;
    }
}

// ==================== DASHBOARD ====================
async function loadDashboard() {
    const data = await api('/api/dashboard');
    if (!data) return;
    document.getElementById('statTables').textContent = data.total_tables;
    document.getElementById('statEmpty').textContent = data.empty_tables;
    document.getElementById('statOccupied').textContent = data.occupied_tables;
    document.getElementById('statRevenue').textContent = fmtMoney(data.today_revenue);
    document.getElementById('statTotalRevenue').textContent = fmtMoney(data.total_revenue);
    document.getElementById('statTotalOrders').textContent = data.total_orders;

    const list = document.getElementById('topItemsList');
    if (data.top_items && data.top_items.length) {
        list.innerHTML = data.top_items.map((item, i) =>
            `<div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                <span><span class="badge bg-warning text-dark me-2">${i + 1}</span>${item.name}</span>
                <span class="badge bg-coffee" style="background:var(--coffee-primary)">${item.qty} lượt</span>
            </div>`
        ).join('');
    } else {
        list.innerHTML = '<p class="text-muted">Chưa có dữ liệu</p>';
    }
}

// ==================== MENU MANAGEMENT ====================
let menuCategories = [];
let menuItems = [];

async function loadMenu() {
    const cats = await api('/api/menu/categories');
    if (cats) menuCategories = cats;
    const items = await api('/api/menu');
    if (items) menuItems = items;
    renderCategories();
    renderMenu('');
    populateCategorySelect('itemCategory');
    populateCategorySelect('editCategory');
}

function renderCategories() {
    const tabs = document.getElementById('categoryTabs');
    tabs.innerHTML = `<button class="btn btn-sm btn-outline-coffee menu-category-btn active" onclick="filterByCategory('')">Tất cả</button>`
        + menuCategories.map(c =>
            `<button class="btn btn-sm btn-outline-coffee menu-category-btn" onclick="filterByCategory('${c}')">${c}</button>`
        ).join('');
}

function filterByCategory(cat) {
    document.querySelectorAll('.menu-category-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    renderMenu(cat);
}

function filterMenu() {
    const q = document.getElementById('searchInput').value.toLowerCase();
    const filtered = menuItems.filter(i => i.name.toLowerCase().includes(q));
    renderMenuList(filtered);
}

function renderMenu(category) {
    const filtered = category ? menuItems.filter(i => i.category === category) : menuItems;
    renderMenuList(filtered);
}

function renderMenuList(items) {
    const list = document.getElementById('menuList');
    if (!items.length) {
        list.innerHTML = '<div class="p-3 text-muted">Không có món nào</div>';
        return;
    }
    list.innerHTML = items.map(item => {
        const isAdmin = document.body.dataset.isAdmin === 'true';
        return `<div class="menu-item">
            <div><div class="item-name">${item.name}</div>
                <small class="text-muted">${item.category}</small></div>
            <div class="d-flex align-items-center gap-2">
                <span class="item-price">${fmtMoney(item.price)}</span>
                ${isAdmin ? `
                <button class="btn btn-sm btn-outline-primary" onclick="editMenuItem(${item.id})" title="Sửa"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteMenuItem(${item.id})" title="Xóa"><i class="bi bi-trash"></i></button>
                ` : ''}
            </div>
        </div>`;
    }).join('');
}

function populateCategorySelect(selectId) {
    const sel = document.getElementById(selectId);
    if (!sel) return;
    sel.innerHTML = menuCategories.map(c => `<option value="${c}">${c}</option>`).join('');
}

let newCategoryAdded = false;
function showNewCategoryInput() {
    document.getElementById('newCategoryInput').classList.remove('d-none');
    document.getElementById('newCategoryInput').focus();
}
function addNewCategory() {
    const input = document.getElementById('newCategoryInput');
    const val = input.value.trim();
    if (val && !menuCategories.includes(val)) {
        menuCategories.push(val);
        renderCategories();
        populateCategorySelect('itemCategory');
        document.getElementById('itemCategory').value = val;
    }
    input.value = '';
    input.classList.add('d-none');
}

async function addMenuItem(e) {
    e.preventDefault();
    const name = document.getElementById('itemName').value.trim();
    const category = document.getElementById('itemCategory').value;
    const price = parseInt(document.getElementById('itemPrice').value);
    if (!name) return showToast('Tên món không được để trống', 'warning');
    const result = await api('/api/menu/add', 'POST', { name, category, price });
    if (result && result.success) {
        showToast('Đã thêm món thành công!');
        document.getElementById('addMenuForm').reset();
        loadMenu();
    }
}

async function editMenuItem(id) {
    const item = menuItems.find(i => i.id === id);
    if (!item) return;
    document.getElementById('editId').value = item.id;
    document.getElementById('editName').value = item.name;
    document.getElementById('editCategory').value = item.category;
    document.getElementById('editPrice').value = item.price;
    new bootstrap.Modal(document.getElementById('editModal')).show();
}

async function updateMenuItem() {
    const id = parseInt(document.getElementById('editId').value);
    const name = document.getElementById('editName').value.trim();
    const category = document.getElementById('editCategory').value;
    const price = parseInt(document.getElementById('editPrice').value);
    const result = await api('/api/menu/update', 'POST', { id, name, category, price });
    if (result && result.success) {
        showToast('Đã cập nhật món!');
        bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
        loadMenu();
    }
}

async function deleteMenuItem(id) {
    if (!confirm('Xóa món này?')) return;
    const result = await api('/api/menu/delete', 'POST', { id });
    if (result && result.success) {
        showToast('Đã xóa món!');
        loadMenu();
    }
}

// ==================== TABLE MANAGEMENT ====================
let tables = [];
let selectedTableId = null;

async function loadTables() {
    tables = await api('/api/tables') || [];
    renderTableGrid('tableGrid', tables, false);
}

function renderTableGrid(gridId, tables, clickable) {
    const grid = document.getElementById(gridId);
    if (!grid) return;
    grid.innerHTML = tables.map(t =>
        `<div class="table-item ${t.status} ${selectedTableId === t.id ? 'selected' : ''}"
            onclick="${clickable ? `selectTable(${t.id})` : `showTableInfo(${t.id})`}"
            title="${t.customer_name || 'Trống'}">
            <span class="table-number">B${t.id}</span>
            <span class="table-status">${t.status === 'empty' ? 'Trống' : t.customer_name || 'Có khách'}</span>
        </div>`
    ).join('');
}

function showTableInfo(id) {
    selectedTableId = id;
    renderTableGrid('tableGrid', tables, false);
    const t = tables.find(t => t.id === id);
    if (!t) return;
    document.getElementById('tdId').textContent = t.id;
    document.getElementById('tdStatus').textContent = t.status === 'empty' ? 'Trống' : 'Có khách';
    document.getElementById('tdStatus').className = t.status === 'empty' ? 'badge bg-success' : 'badge bg-danger';
    document.getElementById('tdCustomer').textContent = t.customer_name || '-';
    document.getElementById('tableDetails').classList.remove('d-none');
    document.getElementById('btnAssign').style.display = t.status === 'empty' ? 'block' : 'none';
    document.getElementById('btnFree').style.display = t.status === 'occupied' ? 'block' : 'none';
    document.getElementById('btnTransfer').style.display = t.status === 'occupied' ? 'block' : 'none';
    document.getElementById('btnMerge').style.display = t.status === 'occupied' ? 'block' : 'none';
    document.querySelector('#tableInfoCard .text-muted').classList.add('d-none');
}

function assignTable() {
    if (!selectedTableId) return;
    document.getElementById('assignTableId').value = selectedTableId;
    document.getElementById('assignName').value = '';
    new bootstrap.Modal(document.getElementById('assignModal')).show();
}

document.getElementById('assignForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const table_id = parseInt(document.getElementById('assignTableId').value);
    const customer_name = document.getElementById('assignName').value.trim() || `Khách Bàn ${table_id}`;
    const result = await api('/api/tables/assign', 'POST', { table_id, customer_name });
    if (result && result.success) {
        showToast(`Đã đặt bàn ${table_id} cho ${customer_name}`);
        bootstrap.Modal.getInstance(document.getElementById('assignModal')).hide();
        loadTables();
    }
});

async function freeTable() {
    if (!selectedTableId || !confirm(`Trả bàn ${selectedTableId}?`)) return;
    const result = await api('/api/tables/free', 'POST', { table_id: selectedTableId });
    if (result && result.success) {
        showToast(`Đã trả bàn ${selectedTableId}`);
        selectedTableId = null;
        document.getElementById('tableDetails').classList.add('d-none');
        document.querySelector('#tableInfoCard .text-muted').classList.remove('d-none');
        loadTables();
    }
}

function showTransferModal() {
    if (!selectedTableId) return;
    document.getElementById('transferFromId').value = selectedTableId;
    const sel = document.getElementById('transferToId');
    sel.innerHTML = tables.filter(t => t.status === 'empty' && t.id !== selectedTableId)
        .map(t => `<option value="${t.id}">Bàn ${t.id}</option>`).join('') || '<option value="">Không có bàn trống</option>';
    new bootstrap.Modal(document.getElementById('transferModal')).show();
}

document.getElementById('transferForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const from_id = parseInt(document.getElementById('transferFromId').value);
    const to_id = parseInt(document.getElementById('transferToId').value);
    if (!to_id) return showToast('Vui lòng chọn bàn đích', 'warning');
    const result = await api('/api/tables/transfer', 'POST', { from_id, to_id });
    if (result && result.success) {
        showToast(`Đã chuyển từ bàn ${from_id} sang bàn ${to_id}`);
        bootstrap.Modal.getInstance(document.getElementById('transferModal')).hide();
        selectedTableId = null;
        document.getElementById('tableDetails').classList.add('d-none');
        document.querySelector('#tableInfoCard .text-muted').classList.remove('d-none');
        loadTables();
    } else if (result) {
        showToast(result.error || 'Chuyển bàn thất bại', 'danger');
    }
});

function showMergeModal() {
    if (!selectedTableId) return;
    document.getElementById('mergeTargetId').value = selectedTableId;
    const div = document.getElementById('mergeSourceCheckboxes');
    const sources = tables.filter(t => t.status === 'occupied' && t.id !== selectedTableId);
    div.innerHTML = sources.length ?
        sources.map(t => `<div class="form-check"><input class="form-check-input" type="checkbox" value="${t.id}" id="ms${t.id}">
            <label class="form-check-label" for="ms${t.id}">Bàn ${t.id} - ${t.customer_name}</label></div>`
        ).join('') : '<p class="text-muted">Không có bàn nào để gộp</p>';
    new bootstrap.Modal(document.getElementById('mergeModal')).show();
}

document.getElementById('mergeForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const target_id = parseInt(document.getElementById('mergeTargetId').value);
    const checks = document.querySelectorAll('#mergeSourceCheckboxes input:checked');
    const source_ids = Array.from(checks).map(c => parseInt(c.value));
    if (!source_ids.length) return showToast('Chọn ít nhất một bàn để gộp', 'warning');
    const result = await api('/api/tables/merge', 'POST', { source_ids, target_id });
    if (result && result.success) {
        showToast(`Đã gộp ${source_ids.length} bàn vào bàn ${target_id}`);
        bootstrap.Modal.getInstance(document.getElementById('mergeModal')).hide();
        loadTables();
    }
});

// ==================== ORDER PAGE ====================
let orderSelectedTableId = null;
let orderTables = [];
let orderCatItems = [];

async function initOrderPage() {
    orderTables = await api('/api/tables') || [];
    renderOrderTables();
    const cats = await api('/api/menu/categories');
    if (cats) {
        const tabs = document.getElementById('orderCategoryTabs');
        tabs.innerHTML = cats.map((c, i) =>
            `<button class="btn btn-sm ${i === 0 ? 'btn-coffee' : 'btn-outline-coffee'} menu-category-btn"
                onclick="loadOrderCategory('${c}', this)">${c}</button>`
        ).join('');
        if (cats.length) loadOrderCategory(cats[0], tabs.querySelector('button'));
    }
}

function renderOrderTables() {
    const grid = document.getElementById('orderTableGrid');
    grid.innerHTML = orderTables.map(t =>
        `<div class="table-item ${t.status} ${orderSelectedTableId === t.id ? 'selected' : ''}"
            onclick="selectOrderTable(${t.id})">
            <span class="table-number">B${t.id}</span>
            <span class="table-status">${t.status === 'empty' ? 'Trống' : 'Có khách'}</span>
        </div>`
    ).join('');
}

function selectOrderTable(id) {
    orderSelectedTableId = id;
    renderOrderTables();
    document.getElementById('orderTableLabel').textContent = id;
    loadCurrentOrder(id);
}

async function loadCurrentOrder(tableId) {
    const data = await api(`/api/orders/table/${tableId}`);
    if (!data) return;
    const div = document.getElementById('currentOrder');
    if (!data.order || !data.order.length) {
        div.innerHTML = '<p class="text-muted p-3">Chưa có món nào</p>';
        document.getElementById('orderFooter').style.display = 'none';
        document.getElementById('orderItemCount').textContent = '0';
        return;
    }
    div.innerHTML = data.order.map((item, i) =>
        `<div class="order-item-row">
            <div><span class="item-qty">${item.quantity}</span> ${item.name}
                ${item.note ? `<br><small class="text-muted">📝 ${item.note}</small>` : ''}</div>
            <div class="d-flex align-items-center gap-2">
                <span class="fw-bold">${fmtMoney(item.price * item.quantity)}</span>
                <button class="btn btn-sm btn-outline-danger" onclick="removeOrderItem(${i})"><i class="bi bi-x"></i></button>
            </div>
        </div>`
    ).join('');
    document.getElementById('orderSubtotal').textContent = fmtMoney(data.subtotal);
    document.getElementById('orderFooter').style.display = 'block';
    document.getElementById('orderItemCount').textContent = data.order.length;
}

async function removeOrderItem(index) {
    if (!orderSelectedTableId) return;
    const result = await api('/api/orders/remove-item', 'POST', { table_id: orderSelectedTableId, index });
    if (result && result.success) {
        loadCurrentOrder(orderSelectedTableId);
        orderTables = await api('/api/tables') || [];
        renderOrderTables();
    }
}

async function loadOrderCategory(category, btn) {
    document.querySelectorAll('#orderCategoryTabs button').forEach(b => {
        b.className = 'btn btn-sm btn-outline-coffee menu-category-btn';
    });
    if (btn) btn.className = 'btn btn-sm btn-coffee menu-category-btn';
    const items = await api(`/api/menu/category/${encodeURIComponent(category)}`);
    if (!items) return;
    orderCatItems = items;
    const div = document.getElementById('orderMenuItems');
    div.innerHTML = items.map(item =>
        `<div class="menu-item" onclick="showAddItemModal(${item.id}, '${item.name}', ${item.price})">
            <div><div class="item-name">${item.name}</div>
                <small class="text-muted">${fmtMoney(item.price)}</small></div>
            <i class="bi bi-plus-circle" style="color:var(--coffee-primary);font-size:1.2rem;"></i>
        </div>`
    ).join('');
}

function showAddItemModal(id, name, price) {
    document.getElementById('addItemId').value = id;
    document.getElementById('addItemModalTitle').textContent = `Thêm: ${name} - ${fmtMoney(price)}`;
    document.getElementById('addItemQty').value = 1;
    document.getElementById('addItemNote').value = '';
    new bootstrap.Modal(document.getElementById('addItemModal')).show();
}

async function confirmAddItem() {
    if (!orderSelectedTableId) return showToast('Vui lòng chọn bàn!', 'warning');
    const item_id = parseInt(document.getElementById('addItemId').value);
    const quantity = parseInt(document.getElementById('addItemQty').value) || 1;
    const note = document.getElementById('addItemNote').value.trim();

    const table = orderTables.find(t => t.id === orderSelectedTableId);
    if (!table || table.status === 'empty') {
        const name = prompt('Nhập tên khách hàng:', `Khách Bàn ${orderSelectedTableId}`);
        if (!name) return;
        await api('/api/tables/assign', 'POST', { table_id: orderSelectedTableId, customer_name: name });
        orderTables = await api('/api/tables') || [];
        renderOrderTables();
    }

    const result = await api('/api/orders/add-item', 'POST', { table_id: orderSelectedTableId, item_id, quantity, note });
    if (result && result.success) {
        showToast('Đã thêm vào giỏ hàng!');
        bootstrap.Modal.getInstance(document.getElementById('addItemModal')).hide();
        loadCurrentOrder(orderSelectedTableId);
        orderTables = await api('/api/tables') || [];
        renderOrderTables();
    }
}

// ==================== BILLING PAGE ====================
let billTables = [];
let billSelectedId = null;
let billData = null;
let appliedVoucher = null;

async function initBillingPage() {
    billTables = await api('/api/tables') || [];
    renderBillTables();
}

function renderBillTables() {
    const grid = document.getElementById('billTableGrid');
    grid.innerHTML = billTables.map(t =>
        `<div class="table-item ${t.status} ${billSelectedId === t.id ? 'selected' : ''}"
            onclick="selectBillTable(${t.id})">
            <span class="table-number">B${t.id}</span>
            <span class="table-status">${t.status === 'empty' ? 'Trống' : t.customer_name || 'Có khách'}</span>
        </div>`
    ).join('');
}

async function selectBillTable(id) {
    billSelectedId = id;
    renderBillTables();
    document.getElementById('billTableLabel').textContent = id;
    document.getElementById('billTableId').value = id;
    document.getElementById('invoiceResult').style.display = 'none';
    document.getElementById('billForm').style.display = 'none';
    document.getElementById('billPlaceholder').style.display = 'block';
    document.getElementById('voucherInput').value = '';
    document.getElementById('voucherResult').innerHTML = '';
    document.getElementById('manualDiscount').value = '0';
    document.getElementById('appliedVoucherCode').value = '';
    appliedVoucher = null;
    billData = null;

    const data = await api(`/api/orders/table/${id}`);
    if (!data || !data.order || !data.order.length) {
        document.getElementById('billOrderItems').innerHTML = '<p class="text-muted p-3">Bàn này không có món</p>';
        document.getElementById('billFooter').style.display = 'none';
        return;
    }
    billData = data;
    document.getElementById('billOrderItems').innerHTML = data.order.map(item =>
        `<div class="order-item-row">
            <div><span class="item-qty">${item.quantity}</span> ${item.name}
                ${item.note ? `<br><small class="text-muted">📝 ${item.note}</small>` : ''}</div>
            <span class="fw-bold">${fmtMoney(item.price * item.quantity)}</span>
        </div>`
    ).join('');
    document.getElementById('billSubtotal').textContent = fmtMoney(data.subtotal);
    document.getElementById('billTotal').textContent = fmtMoney(data.subtotal);
    document.getElementById('billFooter').style.display = 'block';
    document.getElementById('billItemCount').textContent = data.order.length;
    document.getElementById('billForm').style.display = 'block';
    document.getElementById('billPlaceholder').style.display = 'none';
    document.getElementById('paymentAmount').value = '';
    document.getElementById('changeAmount').textContent = '0đ';
    document.getElementById('billDiscountRow').style.display = 'none';
}

async function applyVoucher() {
    const code = document.getElementById('voucherInput').value.trim();
    if (!code || !billData) return;
    const result = await api('/api/vouchers/validate', 'POST', { code, subtotal: billData.subtotal });
    const vdiv = document.getElementById('voucherResult');
    if (result && result.valid) {
        appliedVoucher = result;
        document.getElementById('appliedVoucherCode').value = code;
        vdiv.innerHTML = `<span class="text-success"><i class="bi bi-check-circle"></i> Giảm ${fmtMoney(result.discount)} (${result.type === 'percent' ? result.value + '%' : fmtMoney(result.value)})</span>`;
        recalcBill();
    } else {
        appliedVoucher = null;
        document.getElementById('appliedVoucherCode').value = '';
        vdiv.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle"></i> ${result ? result.error : 'Mã không hợp lệ'}</span>`;
        recalcBill();
    }
}

function recalcBill() {
    if (!billData) return;
    let subtotal = billData.subtotal;
    let discount = 0;
    let discountType = 'none';

    if (appliedVoucher) {
        discount = appliedVoucher.discount;
        discountType = 'voucher';
    }

    const manual = parseInt(document.getElementById('manualDiscount').value) || 0;
    if (manual > discount) {
        discount = Math.min(manual, subtotal);
        discountType = 'manual';
    }

    const total = subtotal - discount;
    document.getElementById('billDiscount').textContent = '-' + fmtMoney(discount);
    document.getElementById('billTotal').textContent = fmtMoney(total);
    document.getElementById('billDiscountRow').style.display = discount > 0 ? 'flex' : 'none';
    document.getElementById('billDiscount').value = discount;
    document.getElementById('billDiscountType').value = discountType;

    if (document.getElementById('paymentAmount').value) calcChange();
}

function calcChange() {
    const totalText = document.getElementById('billTotal').textContent;
    const total = parseInt(totalText.replace(/[^0-9]/g, '')) || 0;
    const payment = parseInt(document.getElementById('paymentAmount').value) || 0;
    const change = payment - total;
    document.getElementById('changeAmount').textContent = fmtMoney(Math.max(0, change));
    document.getElementById('changeAmount').style.color = change >= 0 ? '#28a745' : '#dc3545';
}

async function processPayment() {
    const table_id = parseInt(document.getElementById('billTableId').value);
    const totalText = document.getElementById('billTotal').textContent;
    const total = parseInt(totalText.replace(/[^0-9]/g, '')) || 0;
    const payment = parseInt(document.getElementById('paymentAmount').value) || 0;
    const discount = parseInt(document.getElementById('billDiscount').value) || 0;
    const discountType = document.getElementById('billDiscountType').value;
    const voucherCode = document.getElementById('appliedVoucherCode').value;

    if (payment < total) return showToast('Số tiền khách đưa không đủ!', 'warning');

    const result = await api('/api/billing/pay', 'POST', {
        table_id, total, payment, discount, discount_type: discountType, voucher_code: voucherCode
    });

    if (result && result.success) {
        showInvoice(result.invoice);
        billTables = await api('/api/tables') || [];
        renderBillTables();
        document.getElementById('billForm').style.display = 'none';
        document.getElementById('billFooter').style.display = 'none';
        document.getElementById('billOrderItems').innerHTML = '<p class="text-muted p-3">Đã thanh toán</p>';
        showToast('Thanh toán thành công!');
    }
}

function showInvoice(inv) {
    document.getElementById('invoiceResult').style.display = 'block';
    const div = document.getElementById('invoiceContent');
    let itemsHtml = inv.items.map(item =>
        `<tr><td>${item.name}</td><td>${item.quantity}</td><td>${fmtMoney(item.price)}</td><td>${fmtMoney(item.price * item.quantity)}</td></tr>`
    ).join('');

    div.innerHTML = `
        <div class="invoice-header"><h4>HÓA ĐƠN THANH TOÁN</h4>
            <p class="mb-1">Mã HD: ${inv.id} | Bàn ${inv.table_id}</p>
            <p class="mb-1">Khách: ${inv.customer_name} | NV: ${inv.employee}</p>
            <small class="text-muted">${inv.created_at}</small>
        </div>
        <table><thead><tr><th>Món</th><th>SL</th><th>Đơn giá</th><th>Thành tiền</th></tr></thead>
        <tbody>${itemsHtml}</tbody></table>
        <div style="text-align:right;margin-top:10px;">
            <div>Tạm tính: ${fmtMoney(inv.subtotal)}</div>
            ${inv.discount > 0 ? `<div style="color:#dc3545;">Giảm giá: -${fmtMoney(inv.discount)}</div>` : ''}
            <div style="font-size:1.3rem;font-weight:700;color:var(--coffee-primary);">Tổng: ${fmtMoney(inv.total)}</div>
            <div>Khách đưa: ${fmtMoney(inv.payment)}</div>
            <div style="color:#28a745;font-weight:600;">Tiền thừa: ${fmtMoney(inv.change)}</div>
        </div>`;
}

// ==================== VOUCHER PAGE ====================
async function loadVouchers() {
    const vouchers = await api('/api/vouchers');
    if (!vouchers) return;
    const tbody = document.getElementById('voucherList');
    tbody.innerHTML = vouchers.map(v =>
        `<tr>
            <td><span class="badge" style="background:var(--coffee-primary)">${v.code}</span></td>
            <td>${v.type === 'percent' ? '%' : 'VND'}</td>
            <td>${v.type === 'percent' ? v.value + '%' : fmtMoney(v.value)}</td>
            <td>${fmtMoney(v.min_order)}</td>
            <td>${v.expiry}</td>
        </tr>`
    ).join('');
}

async function addVoucher(e) {
    e.preventDefault();
    const code = document.getElementById('vCode').value.trim().toUpperCase();
    const type = document.getElementById('vType').value;
    const value = parseInt(document.getElementById('vValue').value);
    const min_order = parseInt(document.getElementById('vMinOrder').value) || 0;
    const expiry = document.getElementById('vExpiry').value;
    if (!code) return showToast('Nhập mã giảm giá', 'warning');
    if (!expiry) return showToast('Chọn ngày hết hạn', 'warning');
    const result = await api('/api/vouchers/add', 'POST', { code, type, value, min_order, expiry });
    if (result && result.success) {
        showToast(`Đã thêm mã ${code}`);
        document.getElementById('addVoucherForm').reset();
        loadVouchers();
    }
}

// ==================== STATISTICS PAGE ====================
async function loadStatistics() {
    const rev = await api('/api/stats/revenue');
    if (rev) {
        document.getElementById('statTotalRevenue').textContent = fmtMoney(rev.total_revenue);
        document.getElementById('statTotalOrders').textContent = rev.total_orders;
        document.getElementById('statAvgOrder').textContent = rev.total_orders > 0 ? fmtMoney(Math.round(rev.total_revenue / rev.total_orders)) : '0đ';

        const revTbody = document.getElementById('revenueByItemTable');
        revTbody.innerHTML = rev.revenue_by_item.slice(0, 15).map((item, i) =>
            `<tr><td>${i + 1}</td><td>${item.name}</td><td class="fw-bold" style="color:var(--coffee-primary)">${fmtMoney(item.revenue)}</td></tr>`
        ).join('');
    }

    const topData = await api('/api/stats/top-selling?limit=10');
    if (topData) {
        if (topData.top && topData.top.length) {
            document.getElementById('statTopSeller').textContent = topData.top[0].name;
            const topTbody = document.getElementById('topSellingTable');
            topTbody.innerHTML = topData.top.map((item, i) =>
                `<tr><td>${i + 1}</td><td>${item.name}</td><td><span class="badge bg-warning text-dark">${item.qty}</span></td></tr>`
            ).join('');
        }
        if (topData.least && topData.least.length) {
            const leastTbody = document.getElementById('leastSellingTable');
            leastTbody.innerHTML = topData.least.map((item, i) =>
                `<tr><td>${i + 1}</td><td>${item.name}</td><td><span class="badge bg-secondary">${item.qty}</span></td></tr>`
            ).join('');
        }
    }

    const daily = await api('/api/stats/daily-revenue?days=7');
    if (daily && daily.daily) {
        const bars = document.getElementById('dailyRevenueBars');
        const maxRev = Math.max(...daily.daily.map(d => d.revenue), 1);
        bars.innerHTML = daily.daily.map(d =>
            `<div class="d-flex flex-column align-items-center" style="flex:1;">
                <div style="height:${Math.max(5, (d.revenue / maxRev) * 180)}px;width:100%;background:linear-gradient(to top,var(--coffee-primary),var(--coffee-light));border-radius:5px 5px 0 0;transition:height 0.5s;"></div>
                <small style="font-size:0.65rem;margin-top:5px;text-align:center;">${d.date.slice(5)}<br>${fmtMoney(d.revenue)}</small>
            </div>`
        ).join('');
    }
}

async function filterByDate(e) {
    e.preventDefault();
    const from = document.getElementById('filterFrom').value;
    const to = document.getElementById('filterTo').value;
    if (!from || !to) return showToast('Chọn ngày hợp lệ', 'warning');
    const result = await api('/api/stats/by-date', 'POST', { from, to });
    const div = document.getElementById('dateFilterResult');
    if (!result) return;
    div.style.display = 'block';
    div.innerHTML = `
        <div class="card card-body">
            <h6>Kết quả từ ${from} đến ${to}</h6>
            <div class="row g-2">
                <div class="col-md-4"><strong>Doanh thu:</strong> ${fmtMoney(result.total_revenue)}</div>
                <div class="col-md-4"><strong>Hóa đơn:</strong> ${result.total_orders}</div>
                <div class="col-md-4"><strong>TB/HD:</strong> ${result.total_orders > 0 ? fmtMoney(Math.round(result.total_revenue / result.total_orders)) : '0đ'}</div>
            </div>
            ${result.top && result.top.length ? `
            <hr><h6>Top bán chạy</h6>
            ${result.top.map((item, i) => `<span class="badge bg-warning text-dark me-1">${i+1}. ${item.name} (${item.qty})</span>`).join('')}
            ` : ''}
            ${result.revenue_by_item && result.revenue_by_item.length ? `
            <hr><h6>Doanh thu theo món</h6>
            <div style="max-height:200px;overflow-y:auto;">
            <table class="table table-sm mb-0"><thead><tr><th>Món</th><th>Doanh thu</th></tr></thead>
            <tbody>${result.revenue_by_item.map(item =>
                `<tr><td>${item.name}</td><td class="fw-bold">${fmtMoney(item.revenue)}</td></tr>`
            ).join('')}</tbody></table></div>
            ` : ''}
        </div>`;
}

// ==================== USERS PAGE ====================
async function loadUsers() {
    const users = await api('/api/users');
    if (!users) return;
    const tbody = document.getElementById('userList');
    tbody.innerHTML = users.map((u, i) =>
        `<tr>
            <td>${i + 1}</td>
            <td><i class="bi bi-person-circle me-1"></i>${u.username}</td>
            <td><span class="badge ${u.role === 'admin' ? 'bg-danger' : 'bg-warning'}">${u.role === 'admin' ? 'Admin' : 'Nhân viên'}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteUser('${u.username}')">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>`
    ).join('');
}

async function addUser(e) {
    e.preventDefault();
    const username = document.getElementById('newUsername').value.trim();
    const password = document.getElementById('newPassword').value;
    const role = document.getElementById('newRole').value;
    if (!username || !password) return showToast('Vui lòng nhập đầy đủ thông tin', 'warning');
    const result = await api('/api/users/add', 'POST', { username, password, role });
    if (result && result.success) {
        showToast('Đã thêm người dùng!');
        document.getElementById('addUserForm').reset();
        loadUsers();
    } else if (result) {
        showToast(result.error || 'Thêm thất bại', 'danger');
    }
}

async function deleteUser(username) {
    if (!confirm(`Xóa người dùng "${username}"?`)) return;
    const result = await api('/api/users/delete', 'POST', { username });
    if (result && result.success) {
        showToast('Đã xóa người dùng!');
        loadUsers();
    } else {
        showToast('Không thể xóa!', 'danger');
    }
}

async function changePassword(e) {
    e.preventDefault();
    const old = document.getElementById('oldPassword').value;
    const pw1 = document.getElementById('newPassword1').value;
    const pw2 = document.getElementById('newPassword2').value;
    if (pw1 !== pw2) return showToast('Mật khẩu mới không khớp!', 'warning');
    if (!old || !pw1) return showToast('Vui lòng nhập đầy đủ!', 'warning');
    const result = await api('/api/users/change-password', 'POST', { old_password: old, new_password: pw1 });
    if (result && result.success) {
        showToast('Đổi mật khẩu thành công!');
        document.getElementById('changePwForm').reset();
    } else {
        showToast('Sai mật khẩu cũ!', 'danger');
    }
}
