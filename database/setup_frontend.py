import os
import shutil

# Directorios de origen y destino
workspace = r"C:\Users\Anyel\OneDrive\Desktop\Base de datos 2-proyecto-market la estancia\Proyecto-BaseDeDatos"
templates_dir = os.path.join(workspace, "src", "main", "resources", "templates")
static_dir = os.path.join(workspace, "src", "main", "resources", "static")

# Crear directorios de destino
os.makedirs(os.path.join(static_dir, "Html"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "Css"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "Js"), exist_ok=True)

# 1. Copiar Style.css
shutil.copy(os.path.join(templates_dir, "Style.css"), os.path.join(static_dir, "Css", "Style.css"))

# 2. Copiar archivos HTML a static/Html/ (excepto index.html y reportes.html)
for file_name in os.listdir(templates_dir):
    if file_name.endswith(".html") and file_name != "index.html" and file_name != "reportes.html":
        shutil.copy(os.path.join(templates_dir, file_name), os.path.join(static_dir, "Html", file_name))

# 3. Crear index.html de redirección en static/
with open(os.path.join(static_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write("""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url=/Html/login.html">
</head>
<body>
    Redirigiendo a La Estancia...
</body>
</html>
""")

# 4. Modificar App.js para integrarlo con las APIs de base de datos
with open(os.path.join(templates_dir, "App.js"), "r", encoding="utf-8") as f:
    content = f.read()

# Definir variables globales e implementar caché y sync
cache_code = """const STORAGE_KEY = "la-estancia-app-v1";
const LOW_STOCK_LIMIT = 15;

// Variables de estado localizadas que sincronizan con las APIs
let state = {
    products: [],
    clients: [],
    users: [],
    sales: [],
    auditLogs: [],
    currentSale: {
        id: "VTA-003",
        paymentMethod: "Efectivo",
        items: []
    }
};

async function syncStateWithServer() {
    try {
        const authRes = await fetch("/api/auth/status");
        const status = await authRes.json();
        
        if (!status.loggedIn) {
            if (!window.location.pathname.includes("login.html")) {
                window.location.href = "login.html";
            }
            return;
        }

        // Mostrar usuario e identidad de base de datos conectada
        const heroText = document.querySelector(".dashboard-hero-copy h2");
        if (heroText) {
            heroText.textContent = `Hola, ${status.username} (${status.role.replace("rol_", "").toUpperCase()})`;
        }

        // Mostrar un badge de estado en el encabezado de las otras páginas
        const pageHeader = document.querySelector(".main-content");
        if (pageHeader) {
            const firstHeader = pageHeader.querySelector("h2, h3");
            if (firstHeader && !firstHeader.textContent.startsWith("Hola")) {
                let badge = document.getElementById("db-user-badge");
                if (!badge) {
                    badge = document.createElement("span");
                    badge.id = "db-user-badge";
                    badge.style.marginLeft = "15px";
                    badge.style.fontSize = "13px";
                    badge.style.padding = "4px 8px";
                    badge.style.background = "#e0f7fa";
                    badge.style.color = "#00838f";
                    badge.style.borderRadius = "4px";
                    badge.style.fontWeight = "bold";
                    badge.style.verticalAlign = "middle";
                    firstHeader.appendChild(badge);
                }
                badge.textContent = `Usuario BD: ${status.username} (${status.role.replace("rol_", "").toUpperCase()})`;
            }
        }

        // Sincronizar colecciones traduciendo del español (Java API) al inglés (JS UI)
        const prodRes = await fetch("/api/productos");
        if (prodRes.ok) {
            const rawProducts = await prodRes.json();
            state.products = rawProducts.map(p => ({
                id: p.id,
                code: p.code,
                name: p.nombre,
                category: p.categoria,
                price: p.precio,
                stock: p.stock,
                id_proveedor: p.id_proveedor
            }));
        }

        const clientRes = await fetch("/api/clientes");
        if (clientRes.ok) {
            const rawClients = await clientRes.json();
            state.clients = rawClients.map(c => ({
                id: c.id,
                document: c.documento,
                name: c.nombre,
                phone: c.telefono,
                email: c.correo,
                points: c.puntos
            }));
        }

        const userRes = await fetch("/api/usuarios");
        if (userRes.ok) {
            const rawUsers = await userRes.json();
            state.users = rawUsers.map(u => ({
                id: u.id,
                name: u.nombre,
                login: u.login,
                role: u.rol,
                status: u.estado
            }));
        }

        const salesRes = await fetch("/api/ventas");
        if (salesRes.ok) state.sales = await salesRes.json();

        const auditRes = await fetch("/api/auditoria");
        if (auditRes.ok) state.auditLogs = await auditRes.json();

        // Código correlativo siguiente para el POS
        const nextId = "VTA-" + String(state.sales.length + 1).padStart(3, "0");
        state.currentSale.id = nextId;

    } catch (e) {
        console.error("Error de sincronización con servidor:", e);
    }
}

function setupAuthHooks() {
    const loginForm = document.querySelector(".login-page form");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const inputs = loginForm.querySelectorAll("input");
            const username = inputs[0].value;
            const password = inputs[1].value;
            
            try {
                const res = await fetch("/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });
                
                if (res.ok) {
                    window.location.href = "dashboard.html";
                } else {
                    const data = await res.json();
                    alert("Acceso denegado: " + (data.error || "Usuario o contraseña de base de datos incorrectos."));
                }
            } catch (err) {
                alert("Error al conectar con la base de datos: " + err.message);
            }
        });
    }

    const logoutBtn = document.querySelector('a[href="login.html"]');
    if (logoutBtn && !window.location.pathname.includes("login.html")) {
        logoutBtn.addEventListener("click", async (e) => {
            e.preventDefault();
            await fetch("/api/auth/logout", { method: "POST" });
            window.location.href = "login.html";
        });
    }
}
"""

# Reemplazar la declaración inicial del store por el nuevo código
content = content.replace("""const STORAGE_KEY = "la-estancia-app-v1";
const LOW_STOCK_LIMIT = 15;""", cache_code)

# Reemplazar funciones del almacén local
store_funcs_old = """function ensureStore() {
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
}"""

store_funcs_new = """function ensureStore() {
    // Sincronizado dinámicamente con servidor
}

function readStore() {
    return state;
}

function writeStore(store) {
    state = store;
}

function updateStore(mutator) {
    mutator(state);
    return state;
}"""

content = content.replace(store_funcs_old, store_funcs_new)

# Reemplazar el submit del modal para invocar a la API
submit_modal_old = """function submitModal(event) {
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
}"""

submit_modal_new = """async function submitModal(event) {
    event.preventDefault();
    if (!modalState) return;

    if (modalState.mode === "delete") {
        await executeDeleteEntity(modalState.entity, modalState.key);
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

    let url = "";
    let method = "POST";
    let bodyData = {};

    if (modalState.entity === "producto") {
        url = "/api/productos";
        bodyData = {
            nombre: values.nombre,
            categoria: values.categoria,
            precio: values.precio,
            stock: values.stock,
            id_proveedor: 1
        };
        if (modalState.mode === "edit") {
            const p = state.products.find(item => item.code === modalState.key);
            url = `/api/productos/${p.id}`;
            method = "PUT";
        }
    } else if (modalState.entity === "cliente") {
        url = "/api/clientes";
        bodyData = {
            nombre: values.nombre,
            documento: values.documento,
            correo: values.correo,
            telefono: values.telefono,
            puntos: values.puntos
        };
        if (modalState.mode === "edit") {
            const c = state.clients.find(item => item.document === modalState.key);
            url = `/api/clientes/${c.id}`;
            method = "PUT";
        }
    } else if (modalState.entity === "usuario") {
        url = "/api/usuarios";
        bodyData = {
            login: values.login,
            password: values.password,
            rol: values.rol,
            estado: values.estado
        };
        if (modalState.mode === "edit") {
            url = `/api/usuarios/${modalState.key}`; // Key es EMP-101
            method = "PUT";
        }
    }

    try {
        const res = await fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(bodyData)
        });

        if (res.ok) {
            closeModal();
            await syncStateWithServer();
            renderCurrentPage();
        } else {
            const data = await res.json();
            setModalFeedback(data.error || "Error al procesar la operación.");
        }
    } catch (err) {
        setModalFeedback("Error de conexión: " + err.message);
    }
}

async function executeDeleteEntity(entity, key) {
    let url = "";
    if (entity === "producto") {
        const p = state.products.find(item => item.code === key);
        if (!p) return;
        url = `/api/productos/${p.id}`;
    } else if (entity === "cliente") {
        const c = state.clients.find(item => item.document === key);
        if (!c) return;
        url = `/api/clientes/${c.id}`;
    } else if (entity === "usuario") {
        url = `/api/usuarios/${key}`;
    }

    try {
        const res = await fetch(url, { method: "DELETE" });
        if (res.ok) {
            closeModal();
            await syncStateWithServer();
            renderCurrentPage();
        } else {
            const data = await res.json();
            alert(data.error || "Operación no autorizada.");
        }
    } catch (err) {
        alert("Error de conexión: " + err.message);
    }
}"""

content = content.replace(submit_modal_old, submit_modal_new)

# Reemplazar el checkout de ventas
checkout_sales_old = """function handleEmitSale() {
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
}"""

checkout_sales_new = """async function handleEmitSale() {
    const items = state.currentSale.items;

    if (!items.length) {
        setPosFeedback("Agrega productos antes de emitir el comprobante.", true);
        return;
    }

    const stockError = items.find((item) => {
        const product = state.products.find((productItem) => productItem.code === item.code);
        return !product || Number(product.stock) < Number(item.quantity);
    });

    if (stockError) {
        setPosFeedback(`No hay stock suficiente para ${stockError.name}.`, true);
        return;
    }

    const total = items.reduce((sum, item) => sum + (Number(item.price) * Number(item.quantity)), 0);

    // Obtener DNI del cliente e identificar si es nuevo
    let id_cliente = null;
    const clientInput = document.getElementById("pos-client-document");
    const clientNameInput = document.getElementById("pos-client-name");
    
    if (clientInput && clientInput.value.trim()) {
        const dniVal = clientInput.value.trim();
        let client = state.clients.find(c => c.document === dniVal);
        
        if (client) {
            id_cliente = client.id;
        } else {
            // El cliente no existe, debemos crearlo dinámicamente antes de registrar la venta
            const newName = clientNameInput ? clientNameInput.value.trim() : "";
            if (!newName) {
                setPosFeedback("El cliente no está registrado. Por favor ingrese su Nombre Completo para registrarlo en el sistema.", true);
                return;
            }
            
            setPosFeedback("Registrando nuevo cliente en la base de datos...");
            try {
                const clientRes = await fetch("/api/clientes", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        nombre: newName,
                        documento: dniVal,
                        correo: "",
                        telefono: "",
                        puntos: 0
                    })
                });
                
                if (clientRes.ok) {
                    const newClient = await clientRes.json();
                    id_cliente = newClient.id; // Asignamos el ID retornado de la creación
                    setPosFeedback("Cliente registrado correctamente. Emitiendo comprobante...");
                } else {
                    const errData = await clientRes.json();
                    setPosFeedback("Error al registrar cliente: " + (errData.error || "No autorizado"), true);
                    return;
                }
            } catch (err) {
                setPosFeedback("Error de red al registrar cliente: " + err.message, true);
                return;
            }
        }
    }

    const bodyData = {
        id_cliente: id_cliente,
        total: total,
        paymentMethod: state.currentSale.paymentMethod || "Efectivo",
        items: items.map(item => ({
            code: item.code,
            name: item.name,
            price: item.price,
            quantity: item.quantity
        }))
    };

    try {
        const res = await fetch("/api/ventas", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(bodyData)
        });

        if (res.ok) {
            const data = await res.json();
            state.currentSale.items = [];
            
            // Limpiar campos de cliente del POS
            if (clientInput) clientInput.value = "";
            if (clientNameInput) {
                clientNameInput.value = "";
                clientNameInput.disabled = false;
            }
            const autocompleteSection = document.getElementById("pos-client-autocomplete-section");
            if (autocompleteSection) autocompleteSection.style.display = "none";
            
            setPosFeedback(`Comprobante ${data.voucher} emitido correctamente y stock actualizado.`);
            await syncStateWithServer();
            renderCurrentPage();
        } else {
            const data = await res.json();
            setPosFeedback(data.error || "Error al emitir el comprobante.", true);
        }
    } catch (err) {
        setPosFeedback("Error de conexión: " + err.message, true);
    }
}"""

content = content.replace(checkout_sales_old, checkout_sales_new)

# Reemplazar el DOMContentLoaded al final del archivo
old_dom_listener = """document.addEventListener("DOMContentLoaded", () => {
    ensureStore();
    initializeModal();
    markActiveMenu();
    initializeScrollAnimations();
    initializePageActions();
    renderCurrentPage();
});"""

new_dom_listener = """document.addEventListener("DOMContentLoaded", async () => {
    setupAuthHooks();
    await syncStateWithServer();
    initializeModal();
    markActiveMenu();
    initializeScrollAnimations();
    initializePageActions();
    renderCurrentPage();
});"""

content = content.replace(old_dom_listener, new_dom_listener)

# Modificar initializePageActions() para añadir el listener de DNI
old_page_actions = """function initializePageActions() {
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
    }"""

new_page_actions = """function initializePageActions() {
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

    // Listener para buscar DNI del cliente y autocompletar o registrar
    const clientDocInput = document.getElementById("pos-client-document");
    if (clientDocInput) {
        clientDocInput.addEventListener("input", () => {
            const dniVal = clientDocInput.value.trim();
            const autocompleteSection = document.getElementById("pos-client-autocomplete-section");
            const clientNameInput = document.getElementById("pos-client-name");
            
            if (!dniVal) {
                if (autocompleteSection) autocompleteSection.style.display = "none";
                if (clientNameInput) clientNameInput.value = "";
                return;
            }
            
            const existingClient = state.clients.find(c => c.document === dniVal);
            if (existingClient) {
                if (autocompleteSection) autocompleteSection.style.display = "block";
                if (clientNameInput) {
                    clientNameInput.value = existingClient.name;
                    clientNameInput.disabled = true;
                }
            } else {
                if (autocompleteSection) autocompleteSection.style.display = "block";
                if (clientNameInput) {
                    clientNameInput.value = "";
                    clientNameInput.disabled = false;
                    clientNameInput.placeholder = "Cliente nuevo. Ingrese nombre para registrar.";
                }
            }
        });
    }"""

content = content.replace(old_page_actions, new_page_actions)

# Modificar el dashboard para contar ventas de hoy como "Tráfico de Clientes"
old_dashboard_metrics = """    ingresosNode.textContent = formatCurrency(totalToday);
    document.getElementById("dashboard-stock-critico").textContent = String(criticalStock);
    document.getElementById("dashboard-trafico").textContent = String(store.clients.length);"""

new_dashboard_metrics = """    ingresosNode.textContent = formatCurrency(totalToday);
    document.getElementById("dashboard-stock-critico").textContent = String(criticalStock);
    document.getElementById("dashboard-trafico").textContent = String(salesToday.length);"""

content = content.replace(old_dashboard_metrics, new_dashboard_metrics)

# 5. Agregar soporte para select dropdown en buildModalField
old_build_field = """function buildModalField(field, values) {
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
}"""

new_build_field = """function buildModalField(field, values) {
    const wrapperClass = field.full ? "form-group modal-field-full" : "form-group";
    const value = values[field.name] ?? field.value ?? "";

    if (field.type === "select") {
        const optionsHtml = field.options.map(opt => {
            const selected = String(opt.value) === String(value) ? "selected" : "";
            return `<option value="${escapeAttribute(String(opt.value))}" ${selected}>${escapeAttribute(String(opt.label))}</option>`;
        }).join("");
        
        return `
            <div class="${wrapperClass}">
                <label for="modal-${field.name}">${field.label}</label>
                <select id="modal-${field.name}" name="${field.name}" class="form-control">
                    ${optionsHtml}
                </select>
            </div>`;
    }

    const type = field.type || "text";
    const required = field.required ? "required" : "";
    const min = field.min ? `min="${field.min}"` : "";
    const step = field.step ? `step="${field.step}"` : "";

    return `
        <div class="${wrapperClass}">
            <label for="modal-${field.name}">${field.label}</label>
            <input id="modal-${field.name}" name="${field.name}" type="${type}" class="form-control" placeholder="${field.placeholder || ""}" value="${escapeAttribute(String(value))}" ${required} ${min} ${step}>
        </div>`;
}"""

content = content.replace(old_build_field, new_build_field)

# 6. Reconfigurar modalConfigs de usuarios
old_modal_configs = """const modalConfigs = {
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
};"""

new_modal_configs = """const modalConfigs = {
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
        createDescription: "Agrega un usuario del sistema y configúralo con accesos de base de datos.",
        editDescription: "Actualiza los datos del usuario y sus privilegios.",
        createSubmit: "Guardar usuario",
        editSubmit: "Guardar cambios",
        fields: [
            { name: "nombre", label: "Nombre Completo", placeholder: "Nombre del empleado", required: true, full: true },
            { name: "login", label: "Usuario de Acceso", placeholder: "usuario_login", required: true },
            { name: "password", label: "Contraseña", type: "password", placeholder: "Contraseña de acceso", required: true },
            { name: "rol", label: "Cargo / Rol", type: "select", options: [
                { value: "Administrador", label: "Administrador (Full Acceso)" },
                { value: "Supervisor", label: "Supervisor (Gestión Comercial)" },
                { value: "Cajero", label: "Cajero (Ventas y POS)" },
                { value: "Consultor", label: "Consultor (Solo Lectura)" },
                { value: "Auditor", label: "Auditor (Logs de Seguridad)" }
            ], required: true },
            { name: "estado", label: "Estado de Cuenta", type: "select", options: [
                { value: "Activo", label: "Activo" },
                { value: "Inactivo", label: "Inactivo" }
            ], required: true, full: true }
        ]
    }
};"""

content = content.replace(old_modal_configs, new_modal_configs)

# Quitar la simulación de login estático
static_login_old = """window.addEventListener("DOMContentLoaded", () => {
    
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
});"""

content = content.replace(static_login_old, "")

# Escribir el nuevo archivo App.js
with open(os.path.join(static_dir, "Js", "App.js"), "w", encoding="utf-8") as f:
    f.write(content)

print("Setup del frontend completado con éxito en static/.")
