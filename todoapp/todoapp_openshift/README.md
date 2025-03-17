# TodoApp (OpenShift + Node.js + MySQL)

Aplicación simple para gestionar tareas (To-Do) desarrollada con **Node.js**, **Express** y **MySQL**, desplegada en **OpenShift**.

---

## 📅 Características
- Rutas RESTful para CRUD de tareas
- Persistencia con Sequelize ORM y MySQL
- Despliegue automatizado con OpenShift

---

## 🚀 Despliegue en OpenShift

### 1. Clonar el repositorio
```bash
git clone https://github.com/superlinuxex/DO180-apps.git
cd DO180-apps/todoapp/todoapp_openshift
```

### 2. Aplicar los recursos YAML
```bash
oc apply -f openshift-deploy.yaml -n TU_PROYECTO
```

### 3. Lanzar el build de la app
```bash
oc start-build todoapp -n TU_PROYECTO --wait --follow
```

### 4. Verificar despliegue
```bash
oc get pods -n TU_PROYECTO
oc get route todoapp -n TU_PROYECTO
```
Accede vía navegador a la URL de la **route**.

---

## 🔄 API Endpoints

| Método | Ruta              | Descripción                    |
|---------|-------------------|---------------------------------|
| GET     | `/api/items`      | Listar todas las tareas         |
| POST    | `/api/items`      | Crear nueva tarea               |
| PUT     | `/api/items/:id`  | Actualizar tarea por ID         |
| DELETE  | `/api/items/:id`  | Eliminar tarea por ID           |
| GET     | `/info`           | Info del servidor (uptime etc.) |

---

## 📦 Ejemplos de uso con `curl`

### Crear una nueva tarea
```bash
curl -X POST http://URL_ROUTE/api/items \
     -H "Content-Type: application/json" \
     -d '{"description": "Aprender OpenShift"}'
```

### Listar tareas
```bash
curl http://URL_ROUTE/api/items
```

### Marcar tarea como realizada
```bash
curl -X PUT http://URL_ROUTE/api/items/1 \
     -H "Content-Type: application/json" \
     -d '{"done": true}'
```

### Eliminar tarea
```bash
curl -X DELETE http://URL_ROUTE/api/items/1
```

### Ver info del servidor
```bash
curl http://URL_ROUTE/info
```

> 🔄 Reemplaza `URL_ROUTE` por la URL obtenida con `oc get route`.

---

## 💪 Requisitos
- OpenShift 4+
- Node.js 20 (ya incluido en la imagen base `node:20-alpine`)
- MySQL 5.7 (provisionado por el despliegue YAML)

---

## 📒 Estructura del Proyecto
```
todoapp_openshift/
├── controladores/
│   ├── items.js
│   └── serverinfo.js
├── modelos/
│   └── db.js
├── Dockerfile
├── openshift-deploy.yaml
├── aplicación.js
├── package.json
```

---

## 🚜 Contacto
Superlinuxec ✨  
Email: superlinuxec@gmail.com  
GitHub: [superlinuxex](https://github.com/superlinuxex)

