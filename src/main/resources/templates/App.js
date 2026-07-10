const STORAGE_KEY = "la-estancia-app-v1";
const LOW_STOCK_LIMIT = 15;

let modalState = null;

const modalConfigs = {
    producto: {
        kicker: "Inventario",
        createTitle: "Nuevo producto",
        editTitle: "Editar producto",
        createDescription: "Completa la informacion del producto. El codigo se genera automaticamente.",
        editDescription: "Actualiza la informacion del producto seleccionado.",
        createSubmit: "Guardar producto",
        editSubmit: "Guardar cambios",
        fields: [
            { name: "nombre", label: "Nombre", placeholder: "Nombre del producto", required: true, full: true },
            { name: "categoria", label: "Categoria", placeholder: "Abarrotes", required: true },
            { name: "stock", label: "Stock", type: "number", placeholder: "100", required: true, min: "0" },
            { name: "precio", label: "Precio (S/)", type: "number", placeholder: "5.50", required: true, min: "0", step: "0.01", full: true }
        ]
    },
    cliente: {
        kicker: "Clientes",
        createTitle: "Nuevo cliente",
        editTitle: "Editar cliente",
        createDescription: "Registra los datos principales del cliente con el mismo formato del directorio.",
        editDescription: "Actualiza los datos principales del cliente seleccionado.",
        createSubmit: "Guardar cliente",
        editSubmit: "Guardar cambios",
        fields: [
            { name: "documento", label: "DNI / RUC", placeholder: "72839401", required: true },
            { name: "nombre", label: "Nombre completo", placeholder: "Nombre del cliente", required: true, full: true },
            { name: "telefono", label: "Telefono", placeholder: "987654321" },
            { name: "correo", label: "Correo", type: "email", placeholder: "cliente@email.com" },
            { name: "puntos", label: "Puntos", type: "number", placeholder: "0", min: "0", value: "0", full: true }
        ]
    },
    usuario: {
        kicker: "Accesos",
        createTitle: "Nuevo usuario",
        editTitle: "Editar usuario",
        createDescription: "Agrega un usuario del sistema. El ID se genera automaticamente.",
        editDescription: "Actualiza los datos del usuario manteniendo su identificador actual.",
        createSubmit: "Guardar usuario",
        editSubmit: "Guardar cambios",
        fields: [
            { name: "nombre", label: "Nombre", placeholder: "Nombre del empleado", required: true, full: true },
            { name: "login", label: "Usuario", placeholder: "usuario_login", required: true },
            { name: "rol", label: "Rol", placeholder: "Administrador o Cajero", required: true },
            { name: "estado", label: "Estado", placeholder: "Activo", value: "Activo", required: true, full: true }
        ]
    }
};

document.addEventListener("DOMContentLoaded", () => {
    ensureStore();
    initializeModal();
    markActiveMenu();
    initializeScrollAnimations();
    initializePageActions();
    renderCurrentPage();
});

function createInitialStore() {
    const now = new Date();
    const saleOne = new Date(now.getTime() - (1000 * 60 * 25));
    const saleTwo = new Date(now.getTime() - (1000 * 60 * 38));

    return {
        products: [
            { code: "PRD-001", name: "Arroz Costeño 1kg", category: "Abarrotes", stock: 50, price: 4.5 },
            { code: "PRD-002", name: "Leche Gloria Evaporada", category: "Lácteos", stock: 120, price: 3.8 },
            { code: "PRD-003", name: "Azucar Rubia 1kg", category: "Abarrotes", stock: 18, price: 4.2 },
            { code: "PRD-004", name: "Aceite Primor 1L", category: "Despensa", stock: 9, price: 9.9 }
        ],
        clients: [
            { document: "72839401", name: "María González", phone: "987654321", email: "maria.g@email.com", points: 150 }
        ],
        users: [
            { id: "EMP-101", name: "Carlos Mendoza", login: "admin_carlos", role: "Administrador", status: "Activo" }
        ],
        sales: [
            { id: "VTA-001", voucher: "BOL-001452", cashier: "caja_lucia", total: 45.5, status: "Completado", paymentMethod: "Efectivo", createdAt: saleOne.toISOString(), items: [{ code: "PRD-002", name: "Leche Gloria Evaporada", price: 3.8, quantity: 2 }] },
            { id: "VTA-002", voucher: "FAC-000891", cashier: "admin_carlos", total: 120, status: "Completado", paymentMethod: "Tarjeta (Visa/Mastercard)", createdAt: saleTwo.toISOString(), items: [{ code: "PRD-001", name: "Arroz Costeño 1kg", price: 4.5, quantity: 10 }] }
        ],
        auditLogs: [
            { id: "LOG-001", createdAt: saleTwo.toISOString(), user: "admin_carlos", action: "Venta", detail: "Registro del comprobante FAC-000891" },
            { id: "LOG-002", createdAt: saleOne.toISOString(), user: "caja_lucia", action: "Venta", detail: "Registro del comprobante BOL-001452" }
        ],
        currentSale: {
            id: "VTA-003",
            paymentMethod: "Efectivo",
            items: []
        }
    };
}

function ensureStore() {
    const rawStore = localStorage.getItem(STORAGE_KEY);

    if (!rawStore) {
        writeStore(createInitialStore());
        return;
    }

    try {
        const store = JSON.parse(rawStore);
        const normalizedStore = {
            products: Array.isArray(store.products) ? store.products : [],
            clients: Array.isArray(store.clients) ? store.clients : [],
            users: Array.isArray(store.users) ? store.users : [],
            sales: Array.isArray(store.sales) ? store.sales : [],
            auditLogs: Array.isArray(store.auditLogs) ? store.auditLogs : [],
            currentSale: store.currentSale && Array.isArray(store.currentSale.items)
                ? store.currentSale
                : { id: generateNextCode(Array.isArray(store.sales) ? store.sales : [], "id", "VTA"), paymentMethod: "Efectivo", items: [] }
        };

        if (!normalizedStore.currentSale.id) {
            normalizedStore.currentSale.id = generateNextCode(normalizedStore.sales, "id", "VTA");
        }

        writeStore(normalizedStore);
    } catch (error) {
        writeStore(createInitialStore());
    }
}

function readStore() {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
}

function writeStore(store) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
}

function updateStore(mutator) {
    const store = readStore();
    mutator(store);
    writeStore(store);
    return store;
}

function initializeModal() {
    if (document.getElementById("modal-global")) return;

    const modal = document.createElement("div");
    modal.id = "modal-global";
    modal.className = "modal-overlay";
    modal.setAttribute("aria-hidden", "true");
    modal.innerHTML = `
        <div class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="modal-title">
            <div class="modal-header">
                <div class="modal-header-top">
                    <div>
                        <span class="modal-kicker" id="modal-kicker"></span>
                        <h3 id="modal-title"></h3>
                        <p id="modal-description"></p>
                    </div>
                    <button type="button" class="modal-close" aria-label="Cerrar modal">&times;</button>
                </div>
            </div>
            <form class="modal-form" id="modal-form">
                <div class="modal-grid" id="modal-fields"></div>
                <p class="modal-inline-feedback" id="modal-feedback"></p>
                <div class="modal-actions">
                    <button type="button" class="btn btn-secondary" id="modal-cancelar">Cancelar</button>
                    <button type="submit" class="btn" id="modal-submit">Guardar</button>
                </div>
            </form>
        </div>`;

    document.body.appendChild(modal);

    modal.addEventListener("click", (event) => {
        if (event.target === modal) closeModal();
    });

    modal.querySelector(".modal-close").addEventListener("click", closeModal);
    document.getElementById("modal-cancelar").addEventListener("click", closeModal);
    document.getElementById("modal-form").addEventListener("submit", submitModal);

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeModal();
    });
}

function initializeScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll(".animate-fade-up").forEach((element) => observer.observe(element));
}

function markActiveMenu() {
    let currentRoute = window.location.pathname.split("/").pop();
    if (!currentRoute) currentRoute = "dashboard.html";

    document.querySelectorAll(".nav-menu a").forEach((link) => {
        if (link.getAttribute("href") === currentRoute) {
            document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
            link.parentElement.classList.add("active");
        }
    });
}

function initializePageActions() {
    bindClick("btn-nuevo-producto", () => openEntityModal("producto", "create"));
    bindClick("btn-nuevo-cliente", () => openEntityModal("cliente", "create"));
    bindClick("btn-nuevo-usuario", () => openEntityModal("usuario", "create"));
    bindClick("btn-agregar-pos", handleAddProductToSale);
    bindClick("btn-emitir-comprobante", handleEmitSale);

    const productSearch = document.getElementById("pos-product-search");
    if (productSearch) {
        productSearch.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                handleAddProductToSale();
            }
        });
    }

    const paymentMethod = document.getElementById("pos-payment-method");
    if (paymentMethod) {
        paymentMethod.addEventListener("change", () => {
            updateStore((store) => {
                store.currentSale.paymentMethod = paymentMethod.value;
            });
        });
    }

    ["tabla-productos-body", "tabla-clientes-body", "tabla-usuarios-body"].forEach((tbodyId) => {
        const tbody = document.getElementById(tbodyId);
        if (tbody) tbody.addEventListener("click", handleManagementAction);
    });

    const salesBody = document.getElementById("tabla-ventas-body");
    if (salesBody) {
        salesBody.addEventListener("click", handleSaleTableClick);
        salesBody.addEventListener("input", handleSaleQuantityChange);
    }
}

function renderCurrentPage() {
    renderProductsTable();
    renderClientsTable();
    renderUsersTable();
    renderDashboard();
    renderAuditTable();
    renderPosSuggestions();
    renderCurrentSale();
}

function renderProductsTable() {
    const tbody = document.getElementById("tabla-productos-body");
    if (!tbody) return;

    const { products } = readStore();
    tbody.innerHTML = "";

    if (!products.length) {
        renderEmptyRow(tbody, 6, "No hay productos registrados.");
        return;
    }

    products.forEach((product) => {
        const row = document.createElement("tr");
        row.dataset.key = product.code;
        row.appendChild(createTextCell(product.code));
        row.appendChild(createTextCell(product.name));
        row.appendChild(createTextCell(product.category));
        row.appendChild(createTextCell(String(product.stock)));
        row.appendChild(createTextCell(formatCurrency(product.price)));
        row.appendChild(createActionsCell());
        tbody.appendChild(row);
    });
}

function renderClientsTable() {
    const tbody = document.getElementById("tabla-clientes-body");
    if (!tbody) return;

    const { clients } = readStore();
    tbody.innerHTML = "";

    if (!clients.length) {
        renderEmptyRow(tbody, 6, "No hay clientes registrados.");
        return;
    }

    clients.forEach((client) => {
        const row = document.createElement("tr");
        row.dataset.key = client.document;
        row.appendChild(createTextCell(client.document));
        row.appendChild(createTextCell(client.name));
        row.appendChild(createTextCell(client.phone || "-"));
        row.appendChild(createTextCell(client.email || "-"));
        row.appendChild(createTextCell(`${client.points || 0} pts`));
        row.appendChild(createActionsCell());
        tbody.appendChild(row);
    });
}

function renderUsersTable() {
    const tbody = document.getElementById("tabla-usuarios-body");
    if (!tbody) return;

    const { users } = readStore();
    tbody.innerHTML = "";

    if (!users.length) {
        renderEmptyRow(tbody, 6, "No hay usuarios registrados.");
        return;
    }

    users.forEach((user) => {
        const row = document.createElement("tr");
        row.dataset.key = user.id;
        row.appendChild(createTextCell(user.id));
        row.appendChild(createTextCell(user.name));
        row.appendChild(createTextCell(user.login));

        const roleCell = document.createElement("td");
        roleCell.appendChild(createStrongText(user.role));
        row.appendChild(roleCell);

        const statusCell = document.createElement("td");
        statusCell.appendChild(createUserStatus(user.status));
        row.appendChild(statusCell);

        row.appendChild(createActionsCell());
        tbody.appendChild(row);
    });
}

function renderDashboard() {
    const ingresosNode = document.getElementById("dashboard-ingresos");
    if (!ingresosNode) return;

    const store = readStore();
    const today = new Date().toDateString();
    const salesToday = store.sales.filter((sale) => new Date(sale.createdAt).toDateString() === today);
    const totalToday = salesToday.reduce((sum, sale) => sum + Number(sale.total || 0), 0);
    const criticalStock = store.products.filter((product) => Number(product.stock) <= LOW_STOCK_LIMIT).length;
    const latestSale = store.sales[0];

    ingresosNode.textContent = formatCurrency(totalToday);
    document.getElementById("dashboard-stock-critico").textContent = String(criticalStock);
    document.getElementById("dashboard-trafico").textContent = String(store.clients.length);
    document.getElementById("dashboard-last-update").textContent = latestSale
        ? `Actualizado ${formatDateTime(latestSale.createdAt)}`
        : "Sin movimientos recientes";

    const tbody = document.getElementById("dashboard-activity-body");
    tbody.innerHTML = "";

    if (!store.sales.length) {
        renderEmptyRow(tbody, 5, "Todavia no hay ventas registradas.");
        return;
    }

    store.sales.slice(0, 5).forEach((sale) => {
        const row = document.createElement("tr");
        row.appendChild(createTextCell(formatTime(sale.createdAt)));
        row.appendChild(createTextCell(sale.voucher));
        row.appendChild(createTextCell(sale.cashier));
        row.appendChild(createTextCell(formatCurrency(sale.total)));

        const statusCell = document.createElement("td");
        const pill = document.createElement("span");
        pill.className = "status-pill";
        pill.textContent = sale.status;
        statusCell.appendChild(pill);
        row.appendChild(statusCell);
        tbody.appendChild(row);
    });
}

function renderAuditTable() {
    const tbody = document.getElementById("tabla-auditoria-body");
    if (!tbody) return;

    const { auditLogs } = readStore();
    tbody.innerHTML = "";

    if (!auditLogs.length) {
        renderEmptyRow(tbody, 4, "No hay registros de auditoria todavia.");
        return;
    }

    auditLogs.slice(0, 25).forEach((log) => {
        const row = document.createElement("tr");
        row.appendChild(createTextCell(formatDateTime(log.createdAt)));
        row.appendChild(createTextCell(log.user));
        row.appendChild(createTextCell(log.action));
        row.appendChild(createTextCell(log.detail));
        tbody.appendChild(row);
    });
}

function renderPosSuggestions() {
    const datalist = document.getElementById("pos-products-list");
    if (!datalist) return;

    const { products } = readStore();
    datalist.innerHTML = "";

    products.forEach((product) => {
        const option = document.createElement("option");
        option.value = product.name;
        option.label = `${product.code} | Stock ${product.stock} | ${formatCurrency(product.price)}`;
        datalist.appendChild(option);
    });
}

function renderCurrentSale() {
    const tbody = document.getElementById("tabla-ventas-body");
    if (!tbody) return;

    const { currentSale } = readStore();
    tbody.innerHTML = "";

    if (!currentSale.items.length) {
        renderEmptyRow(tbody, 6, "Aun no hay productos en la venta actual.");
    } else {
        currentSale.items.forEach((item) => {
            const row = document.createElement("tr");
            row.dataset.key = item.code;
            row.appendChild(createTextCell(item.code));
            row.appendChild(createTextCell(item.name));
            row.appendChild(createTextCell(formatCurrency(item.price), "precio-unitario"));

            const quantityCell = document.createElement("td");
            const quantityInput = document.createElement("input");
            quantityInput.type = "number";
            quantityInput.className = "form-control pos-table-quantity";
            quantityInput.min = "1";
            quantityInput.value = String(item.quantity);
            quantityInput.dataset.code = item.code;
            quantityCell.appendChild(quantityInput);
            row.appendChild(quantityCell);

            row.appendChild(createTextCell(formatCurrency(item.price * item.quantity), "subtotal-fila"));

            const deleteCell = document.createElement("td");
            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.className = "table-action-btn is-danger";
            deleteButton.dataset.saleAction = "remove";
            deleteButton.dataset.code = item.code;
            deleteButton.textContent = "Eliminar";
            deleteCell.appendChild(deleteButton);
            row.appendChild(deleteCell);

            tbody.appendChild(row);
        });
    }

    const total = currentSale.items.reduce((sum, item) => sum + (Number(item.price) * Number(item.quantity)), 0);
    document.getElementById("monto-total-pos").textContent = `Total: ${formatCurrency(total)}`;
    document.getElementById("pos-sale-code").textContent = `Venta: ${currentSale.id}`;

    const paymentMethod = document.getElementById("pos-payment-method");
    if (paymentMethod) paymentMethod.value = currentSale.paymentMethod || "Efectivo";
}

function openEntityModal(entity, mode, key = null) {
    const config = modalConfigs[entity];
    const modal = document.getElementById("modal-global");
    const fields = document.getElementById("modal-fields");
    const submit = document.getElementById("modal-submit");

    if (!config || !modal || !fields || !submit) return;

    modalState = { entity, mode, key };

    document.getElementById("modal-kicker").textContent = config.kicker;
    document.getElementById("modal-title").textContent = mode === "edit" ? config.editTitle : config.createTitle;
    document.getElementById("modal-description").textContent = mode === "edit" ? config.editDescription : config.createDescription;
    setModalFeedback("");
    submit.className = "btn";
    submit.textContent = mode === "edit" ? config.editSubmit : config.createSubmit;

    const record = key ? getEntityRecord(entity, key) : {};
    fields.innerHTML = config.fields.map((field) => buildModalField(field, record)).join("");

    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");

    const firstInput = fields.querySelector("input");
    if (firstInput) firstInput.focus();
}

function openDeleteModal(entity, key) {
    const modal = document.getElementById("modal-global");
    const fields = document.getElementById("modal-fields");
    const submit = document.getElementById("modal-submit");
    const config = modalConfigs[entity];
    const record = getEntityRecord(entity, key);

    if (!modal || !fields || !submit || !config || !record) return;

    modalState = { entity, mode: "delete", key };
    document.getElementById("modal-kicker").textContent = config.kicker;
    document.getElementById("modal-title").textContent = `Eliminar ${entity}`;
    document.getElementById("modal-description").textContent = "Confirma la eliminacion del registro seleccionado.";
    setModalFeedback("");
    submit.className = "btn btn-danger";
    submit.textContent = "Eliminar";
    fields.innerHTML = `
        <div class="modal-confirmation modal-field-full">
            <strong>Esta accion eliminara el registro de forma local.</strong>
            <p>${getDeleteMessage(entity, record)}</p>
        </div>`;

    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
}

function closeModal() {
    const modal = document.getElementById("modal-global");
    const form = document.getElementById("modal-form");
    const submit = document.getElementById("modal-submit");

    if (!modal) return;

    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    if (form) form.reset();
    if (submit) submit.className = "btn";
    setModalFeedback("");
    modalState = null;
}

function buildModalField(field, values) {
    const type = field.type || "text";
    const wrapperClass = field.full ? "form-group modal-field-full" : "form-group";
    const required = field.required ? "required" : "";
    const min = field.min ? `min="${field.min}"` : "";
    const step = field.step ? `step="${field.step}"` : "";
    const value = values[field.name] ?? field.value ?? "";

    return `
        <div class="${wrapperClass}">
            <label for="modal-${field.name}">${field.label}</label>
            <input id="modal-${field.name}" name="${field.name}" type="${type}" class="form-control" placeholder="${field.placeholder || ""}" value="${escapeAttribute(String(value))}" ${required} ${min} ${step}>
        </div>`;
}

function submitModal(event) {
    event.preventDefault();
    if (!modalState) return;

    if (modalState.mode === "delete") {
        deleteEntity(modalState.entity, modalState.key);
        closeModal();
        renderCurrentPage();
        return;
    }

    const formData = new FormData(event.target);
    const values = Object.fromEntries(formData.entries());
    const validationError = validateEntityValues(modalState.entity, values, modalState.key, modalState.mode);

    if (validationError) {
        setModalFeedback(validationError);
        return;
    }

    setModalFeedback("");

    if (modalState.entity === "producto") {
        modalState.mode === "edit" ? updateProduct(modalState.key, values) : createProduct(values);
    }

    if (modalState.entity === "cliente") {
        modalState.mode === "edit" ? updateClient(modalState.key, values) : createClient(values);
    }

    if (modalState.entity === "usuario") {
        modalState.mode === "edit" ? updateUser(modalState.key, values) : createUser(values);
    }

    closeModal();
    renderCurrentPage();
}

function validateEntityValues(entity, values, currentKey, mode) {
    const store = readStore();

    if (entity === "producto") {
        if (Number(values.stock) < 0) return "El stock no puede ser negativo.";
        if (Number(values.precio) <= 0) return "El precio debe ser mayor que cero.";
    }

    if (entity === "cliente") {
        const exists = store.clients.some((client) => client.document === values.documento && (mode === "create" || client.document !== currentKey));
        if (exists) return "Ya existe un cliente con ese DNI o RUC.";
    }

    if (entity === "usuario") {
        const exists = store.users.some((user) => user.login.toLowerCase() === values.login.toLowerCase() && (mode === "create" || user.id !== currentKey));
        if (exists) return "Ya existe un usuario con ese login.";
    }

    return "";
}

function createProduct(values) {
    updateStore((store) => {
        const product = {
            code: generateNextCode(store.products, "code", "PRD"),
            name: values.nombre.trim(),
            category: values.categoria.trim(),
            stock: Number(values.stock),
            price: Number(values.precio)
        };

        store.products.push(product);
        pushAuditLog(store, "Producto", `Creacion del producto ${product.code} - ${product.name}`);
    });
}

function updateProduct(code, values) {
    updateStore((store) => {
        const product = store.products.find((item) => item.code === code);
        if (!product) return;

        product.name = values.nombre.trim();
        product.category = values.categoria.trim();
        product.stock = Number(values.stock);
        product.price = Number(values.precio);

        syncCurrentSaleItem(store, product);
        pushAuditLog(store, "Producto", `Actualizacion del producto ${product.code} - ${product.name}`);
    });
}

function createClient(values) {
    updateStore((store) => {
        const client = {
            document: values.documento.trim(),
            name: values.nombre.trim(),
            phone: values.telefono.trim(),
            email: values.correo.trim(),
            points: Number(values.puntos || 0)
        };

        store.clients.push(client);
        pushAuditLog(store, "Cliente", `Creacion del cliente ${client.document} - ${client.name}`);
    });
}

function updateClient(document, values) {
    updateStore((store) => {
        const client = store.clients.find((item) => item.document === document);
        if (!client) return;

        client.document = values.documento.trim();
        client.name = values.nombre.trim();
        client.phone = values.telefono.trim();
        client.email = values.correo.trim();
        client.points = Number(values.puntos || 0);

        pushAuditLog(store, "Cliente", `Actualizacion del cliente ${client.document} - ${client.name}`);
    });
}

function createUser(values) {
    updateStore((store) => {
        const user = {
            id: generateNextCode(store.users, "id", "EMP"),
            name: values.nombre.trim(),
            login: values.login.trim(),
            role: values.rol.trim(),
            status: values.estado.trim()
        };

        store.users.push(user);
        pushAuditLog(store, "Usuario", `Creacion del usuario ${user.id} - ${user.login}`);
    });
}

function updateUser(id, values) {
    updateStore((store) => {
        const user = store.users.find((item) => item.id === id);
        if (!user) return;

        user.name = values.nombre.trim();
        user.login = values.login.trim();
        user.role = values.rol.trim();
        user.status = values.estado.trim();

        pushAuditLog(store, "Usuario", `Actualizacion del usuario ${user.id} - ${user.login}`);
    });
}

function deleteEntity(entity, key) {
    updateStore((store) => {
        if (entity === "producto") {
            const product = store.products.find((item) => item.code === key);
            store.products = store.products.filter((item) => item.code !== key);
            store.currentSale.items = store.currentSale.items.filter((item) => item.code !== key);
            if (product) pushAuditLog(store, "Producto", `Eliminacion del producto ${product.code} - ${product.name}`);
        }

        if (entity === "cliente") {
            const client = store.clients.find((item) => item.document === key);
            store.clients = store.clients.filter((item) => item.document !== key);
            if (client) pushAuditLog(store, "Cliente", `Eliminacion del cliente ${client.document} - ${client.name}`);
        }

        if (entity === "usuario") {
            const user = store.users.find((item) => item.id === key);
            store.users = store.users.filter((item) => item.id !== key);
            if (user) pushAuditLog(store, "Usuario", `Eliminacion del usuario ${user.id} - ${user.login}`);
        }
    });
}

function handleManagementAction(event) {
    const button = event.target.closest("[data-action]");
    if (!button) return;

    const row = button.closest("tr");
    const tbody = button.closest("tbody");
    if (!row || !tbody) return;

    const entity = tbody.dataset.entity;
    const key = row.dataset.key;
    if (!entity || !key) return;

    if (button.dataset.action === "edit") openEntityModal(entity, "edit", key);
    if (button.dataset.action === "delete") openDeleteModal(entity, key);
}

function handleAddProductToSale() {
    const searchInput = document.getElementById("pos-product-search");
    const quantityInput = document.getElementById("pos-product-quantity");
    if (!searchInput || !quantityInput) return;

    const query = searchInput.value.trim();
    const quantity = Number(quantityInput.value || 1);
    const store = readStore();
    const product = findProductByQuery(query, store.products);

    if (!query) {
        setPosFeedback("Escribe un producto antes de intentar agregarlo.", true);
        return;
    }

    if (!product) {
        setPosFeedback("No encontramos ese producto en inventario. Usa el nombre o el codigo registrado.", true);
        return;
    }

    if (!Number.isInteger(quantity) || quantity <= 0) {
        setPosFeedback("La cantidad debe ser mayor que cero.", true);
        return;
    }

    const currentItem = store.currentSale.items.find((item) => item.code === product.code);
    const requestedQuantity = (currentItem ? currentItem.quantity : 0) + quantity;

    if (requestedQuantity > Number(product.stock)) {
        setPosFeedback(`Stock insuficiente para ${product.name}. Disponible: ${product.stock}.`, true);
        return;
    }

    updateStore((currentStore) => {
        const saleItem = currentStore.currentSale.items.find((item) => item.code === product.code);

        if (saleItem) {
            saleItem.quantity += quantity;
        } else {
            currentStore.currentSale.items.push({
                code: product.code,
                name: product.name,
                price: product.price,
                quantity
            });
        }
    });

    searchInput.value = "";
    quantityInput.value = "1";
    setPosFeedback(`${product.name} se agrego a la venta actual.`);
    renderCurrentSale();
}

function handleSaleTableClick(event) {
    const button = event.target.closest("[data-sale-action='remove']");
    if (!button) return;

    const code = button.dataset.code;
    updateStore((store) => {
        store.currentSale.items = store.currentSale.items.filter((item) => item.code !== code);
    });

    setPosFeedback("Producto retirado de la venta actual.");
    renderCurrentSale();
}

function handleSaleQuantityChange(event) {
    const input = event.target.closest("input[data-code]");
    if (!input) return;

    const code = input.dataset.code;
    const quantity = Number(input.value || 0);
    const store = readStore();
    const product = store.products.find((item) => item.code === code);

    if (!product) return;

    if (!Number.isInteger(quantity) || quantity <= 0) {
        setPosFeedback("La cantidad debe ser mayor que cero.", true);
        return;
    }

    if (quantity > Number(product.stock)) {
        input.value = String(store.currentSale.items.find((item) => item.code === code)?.quantity || 1);
        setPosFeedback(`Stock insuficiente para ${product.name}. Disponible: ${product.stock}.`, true);
        return;
    }

    updateStore((currentStore) => {
        const item = currentStore.currentSale.items.find((saleItem) => saleItem.code === code);
        if (item) item.quantity = quantity;
    });

    renderCurrentSale();
}

function handleEmitSale() {
    const store = readStore();
    const items = store.currentSale.items;

    if (!items.length) {
        setPosFeedback("Agrega productos antes de emitir el comprobante.", true);
        return;
    }

    const stockError = items.find((item) => {
        const product = store.products.find((productItem) => productItem.code === item.code);
        return !product || Number(product.stock) < Number(item.quantity);
    });

    if (stockError) {
        setPosFeedback(`No hay stock suficiente para ${stockError.name}.`, true);
        return;
    }

    const total = items.reduce((sum, item) => sum + (Number(item.price) * Number(item.quantity)), 0);

    updateStore((currentStore) => {
        currentStore.products.forEach((product) => {
            const saleItem = currentStore.currentSale.items.find((item) => item.code === product.code);
            if (saleItem) product.stock = Number(product.stock) - Number(saleItem.quantity);
        });

        const saleRecord = {
            id: currentStore.currentSale.id,
            voucher: generateNextCode(currentStore.sales, "voucher", "BOL"),
            cashier: "admin_carlos",
            total,
            status: "Completado",
            paymentMethod: currentStore.currentSale.paymentMethod || "Efectivo",
            createdAt: new Date().toISOString(),
            items: currentStore.currentSale.items.map((item) => ({ ...item }))
        };

        currentStore.sales.unshift(saleRecord);
        pushAuditLog(currentStore, "Venta", `Registro del comprobante ${saleRecord.voucher} por ${formatCurrency(total)}`);
        currentStore.currentSale = {
            id: generateNextCode(currentStore.sales, "id", "VTA"),
            paymentMethod: currentStore.currentSale.paymentMethod || "Efectivo",
            items: []
        };
    });

    setPosFeedback("Comprobante emitido correctamente y stock actualizado.");
    renderCurrentPage();
}

function getEntityRecord(entity, key) {
    const store = readStore();

    if (entity === "producto") {
        const product = store.products.find((item) => item.code === key);
        return product ? { nombre: product.name, categoria: product.category, stock: product.stock, precio: product.price } : null;
    }

    if (entity === "cliente") {
        const client = store.clients.find((item) => item.document === key);
        return client ? { documento: client.document, nombre: client.name, telefono: client.phone, correo: client.email, puntos: client.points } : null;
    }

    if (entity === "usuario") {
        const user = store.users.find((item) => item.id === key);
        return user ? { nombre: user.name, login: user.login, rol: user.role, estado: user.status } : null;
    }

    return null;
}

function getDeleteMessage(entity, record) {
    if (entity === "producto") return `Se eliminara el producto ${record.nombre || record.name}.`;
    if (entity === "cliente") return `Se eliminara el cliente ${record.nombre || record.name}.`;
    if (entity === "usuario") return `Se eliminara el usuario ${record.login}.`;
    return "Se eliminara el registro seleccionado.";
}

function findProductByQuery(query, products) {
    const normalizedQuery = normalizeText(query);
    if (!normalizedQuery) return null;

    return products.find((product) => normalizeText(product.code) === normalizedQuery)
        || products.find((product) => normalizeText(product.name) === normalizedQuery)
        || products.find((product) => normalizeText(product.name).includes(normalizedQuery))
        || products.find((product) => normalizeText(product.code).includes(normalizedQuery));
}

function syncCurrentSaleItem(store, product) {
    const item = store.currentSale.items.find((saleItem) => saleItem.code === product.code);
    if (!item) return;

    item.name = product.name;
    item.price = product.price;
    if (Number(product.stock) <= 0) {
        store.currentSale.items = store.currentSale.items.filter((saleItem) => saleItem.code !== product.code);
        return;
    }

    if (item.quantity > product.stock) item.quantity = Number(product.stock);
}

function pushAuditLog(store, action, detail, user = "admin_carlos") {
    const log = {
        id: generateNextCode(store.auditLogs, "id", "LOG"),
        createdAt: new Date().toISOString(),
        user,
        action,
        detail
    };

    store.auditLogs.unshift(log);
    store.auditLogs = store.auditLogs.slice(0, 50);
}

function generateNextCode(items, field, prefix) {
    const maxValue = items.reduce((max, item) => {
        const value = typeof item[field] === "string" ? item[field] : "";
        const match = value.match(new RegExp(`^${prefix}-(\\d+)$`));
        if (!match) return max;
        return Math.max(max, Number(match[1]));
    }, 0);

    return `${prefix}-${String(maxValue + 1).padStart(3, "0")}`;
}

function bindClick(id, handler) {
    const element = document.getElementById(id);
    if (element) element.addEventListener("click", handler);
}

function createTextCell(text, className = "") {
    const cell = document.createElement("td");
    cell.textContent = text;
    if (className) cell.className = className;
    return cell;
}

function createStrongText(text) {
    const strong = document.createElement("strong");
    strong.textContent = text;
    return strong;
}

function createUserStatus(text) {
    const status = document.createElement("span");
    status.style.color = "#009EB3";
    status.style.fontWeight = "600";
    status.textContent = text;
    return status;
}

function createActionsCell() {
    const cell = document.createElement("td");
    const wrapper = document.createElement("div");
    wrapper.className = "table-actions";
    wrapper.appendChild(createActionButton("Editar", "edit"));
    wrapper.appendChild(createActionButton("Eliminar", "delete", true));
    cell.appendChild(wrapper);
    return cell;
}

function createActionButton(label, action, danger = false) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `table-action-btn${danger ? " is-danger" : ""}`;
    button.dataset.action = action;
    button.textContent = label;
    return button;
}

function renderEmptyRow(tbody, colspan, message) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = colspan;
    cell.className = "empty-state-cell";
    cell.textContent = message;
    row.appendChild(cell);
    tbody.appendChild(row);
}

function setPosFeedback(message, isError = false) {
    const feedback = document.getElementById("pos-feedback");
    if (!feedback) return;

    feedback.textContent = message;
    feedback.classList.toggle("is-error", isError);
    feedback.classList.toggle("is-success", !isError);
}

function setModalFeedback(message) {
    const feedback = document.getElementById("modal-feedback");
    if (!feedback) return;

    feedback.textContent = message;
    feedback.classList.toggle("has-message", Boolean(message));
}

function formatCurrency(value) {
    return `S/ ${Number(value || 0).toFixed(2)}`;
}

function formatTime(isoDate) {
    return new Date(isoDate).toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" });
}

function formatDateTime(isoDate) {
    return new Date(isoDate).toLocaleString("es-PE", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });
}

function normalizeText(value) {
    return String(value || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .trim();
}

function escapeAttribute(value) {
    return value
        .replace(/&/g, "&amp;")
        .replace(/"/g, "&quot;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}
window.addEventListener("DOMContentLoaded", () => {
    
    const loginForm = document.querySelector(".login-box form");
    
    if (loginForm) {
        loginForm.addEventListener("submit", (evento) => {
            
            const usuario = loginForm.querySelector("input[type='text']").value;
            const password = loginForm.querySelector("input[type='password']").value;
            
            
            if (usuario !== "Admin" || password !== "Waza123") {
                evento.preventDefault(); // Detiene la acción por defecto (ir a dashboard.html)
                alert("Acceso denegado: Usuario o contraseña incorrectos.");
            }
            
        });
    }
});