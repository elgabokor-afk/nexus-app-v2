# 🎨 Variables de Entorno para el Frontend (Next.js)

## 📋 Variables Requeridas

El frontend de Next.js necesita estas variables de entorno para funcionar correctamente.

---

## 🔑 Variables para Vercel/Railway (Frontend)

### Opción 1: Deployment en Vercel (Recomendado para Frontend)

Ve a tu proyecto en Vercel → **Settings** → **Environment Variables**

```bash
# ============================================
# SUPABASE (REQUERIDO)
# ============================================
NEXT_PUBLIC_SUPABASE_URL=https://uxjjqrctxfajzicruvxc.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4ampxcmN0eGZhanppY3J1dnhjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkwMjM1NjYsImV4cCI6MjA4NDU5OTU2Nn0.MyzhM7h5xM45SwtZ40DoaS_Cg6SMByuYVrBkmIhNYPM

# ============================================
# PUSHER (REQUERIDO para Tiempo Real)
# ============================================
NEXT_PUBLIC_PUSHER_KEY=dda05a0dc630ab53ec2e
NEXT_PUBLIC_PUSHER_CLUSTER=mt1

# ============================================
# API BACKEND (Si está en Railway)
# ============================================
NEXT_PUBLIC_API_URL=https://tu-backend.railway.app
```

### Opción 2: Deployment en Railway (Frontend + Backend juntos)

Si despliegas todo en Railway, usa las mismas variables:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://uxjjqrctxfajzicruvxc.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Pusher
NEXT_PUBLIC_PUSHER_KEY=dda05a0dc630ab53ec2e
NEXT_PUBLIC_PUSHER_CLUSTER=mt1

# API URL (si backend está en otro servicio)
NEXT_PUBLIC_API_URL=http://nexus-api.railway.internal:8080
```

---

## 📝 Explicación de Variables

### NEXT_PUBLIC_SUPABASE_URL
- **Qué es**: URL de tu proyecto de Supabase
- **Dónde obtenerla**: Supabase Dashboard → Settings → API → Project URL
- **Ejemplo**: `https://uxjjqrctxfajzicruvxc.supabase.co`
- **Importante**: Debe empezar con `NEXT_PUBLIC_` para ser accesible en el navegador

### NEXT_PUBLIC_SUPABASE_ANON_KEY
- **Qué es**: Clave pública de Supabase (segura para el navegador)
- **Dónde obtenerla**: Supabase Dashboard → Settings → API → anon public
- **Ejemplo**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
- **Importante**: Esta es la clave ANON (pública), NO la service_role

### NEXT_PUBLIC_PUSHER_KEY
- **Qué es**: Clave pública de Pusher para WebSockets
- **Dónde obtenerla**: Pusher Dashboard → App Keys → key
- **Ejemplo**: `dda05a0dc630ab53ec2e`
- **Importante**: Debe empezar con `NEXT_PUBLIC_`

### NEXT_PUBLIC_PUSHER_CLUSTER
- **Qué es**: Región del servidor de Pusher
- **Dónde obtenerla**: Pusher Dashboard → App Keys → cluster
- **Ejemplo**: `mt1`, `us2`, `eu`, etc.
- **Importante**: Debe coincidir con tu configuración de Pusher

### NEXT_PUBLIC_API_URL (Opcional)
- **Qué es**: URL del backend API si está separado
- **Cuándo usarla**: Si el backend está en un servicio diferente
- **Ejemplo**: `https://nexus-api.railway.app`
- **Nota**: Si frontend y backend están juntos, no es necesaria

---

## 🚀 Configuración por Plataforma

### Vercel (Recomendado para Frontend)

1. Ve a [vercel.com](https://vercel.com)
2. Importa tu repositorio
3. Ve a **Settings** → **Environment Variables**
4. Agrega las 4 variables principales:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_PUSHER_KEY`
   - `NEXT_PUBLIC_PUSHER_CLUSTER`
5. Click en **Save**
6. Redeploy el proyecto

### Railway (Frontend + Backend)

Si usas Railway para todo:

1. Crea dos servicios:
   - **nexus-backend**: Para el Python/API
   - **nexus-frontend**: Para Next.js

2. En **nexus-frontend**, agrega:
   ```bash
   NEXT_PUBLIC_SUPABASE_URL=...
   NEXT_PUBLIC_SUPABASE_ANON_KEY=...
   NEXT_PUBLIC_PUSHER_KEY=...
   NEXT_PUBLIC_PUSHER_CLUSTER=...
   NEXT_PUBLIC_API_URL=http://nexus-backend.railway.internal:8080
   ```

3. En **nexus-backend**, agrega todas las variables del backend (ver DEPLOY_RAILWAY_AHORA.md)

### Netlify

Similar a Vercel:
1. Site Settings → Build & Deploy → Environment
2. Agrega las mismas 4 variables
3. Redeploy

---

## 🔒 Seguridad: ¿Qué NO incluir en el Frontend?

### ❌ NUNCA incluyas en variables NEXT_PUBLIC_:

- `SUPABASE_SERVICE_ROLE_KEY` (solo para backend)
- `BINANCE_SECRET` (solo para backend)
- `PUSHER_SECRET` (solo para backend)
- `OPENAI_API_KEY` (solo para backend)
- Cualquier clave privada o secret

### ✅ Solo incluye claves públicas:

- `NEXT_PUBLIC_SUPABASE_URL` ✅
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` ✅
- `NEXT_PUBLIC_PUSHER_KEY` ✅
- `NEXT_PUBLIC_PUSHER_CLUSTER` ✅

---

## 📁 Archivo .env.local para Desarrollo Local

Crea un archivo `.env.local` en la raíz del proyecto:

```bash
# .env.local (para desarrollo local)

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://uxjjqrctxfajzicruvxc.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4ampxcmN0eGZhanppY3J1dnhjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkwMjM1NjYsImV4cCI6MjA4NDU5OTU2Nn0.MyzhM7h5xM45SwtZ40DoaS_Cg6SMByuYVrBkmIhNYPM

# Pusher
NEXT_PUBLIC_PUSHER_KEY=dda05a0dc630ab53ec2e
NEXT_PUBLIC_PUSHER_CLUSTER=mt1

# API Local (si corres el backend localmente)
NEXT_PUBLIC_API_URL=http://localhost:8080
```

---

## ✅ Verificar que Funciona

### 1. Verificar en el navegador

Abre la consola del navegador (F12) y ejecuta:

```javascript
console.log(process.env.NEXT_PUBLIC_SUPABASE_URL)
console.log(process.env.NEXT_PUBLIC_PUSHER_KEY)
```

Deberías ver los valores correctos.

### 2. Verificar conexión a Supabase

En la consola del navegador:

```javascript
// Debería mostrar la URL de Supabase
console.log('Supabase URL:', process.env.NEXT_PUBLIC_SUPABASE_URL)
```

### 3. Verificar Pusher

En la consola del navegador, busca:
```
[Pusher] Bridge Active
```

Si ves este mensaje, Pusher está conectado correctamente.

---

## 🐛 Troubleshooting

### Problema: "process.env.NEXT_PUBLIC_SUPABASE_URL is undefined"

**Causa**: Variable no configurada o no empieza con `NEXT_PUBLIC_`

**Solución**:
1. Verifica que la variable empiece con `NEXT_PUBLIC_`
2. Reinicia el servidor de desarrollo: `npm run dev`
3. En producción, redeploy el proyecto

### Problema: "Failed to connect to Supabase"

**Causa**: URL o clave incorrecta

**Solución**:
1. Verifica que la URL sea correcta (sin espacios)
2. Verifica que uses la clave ANON, no la service_role
3. Verifica que Supabase esté accesible

### Problema: "Pusher connection failed"

**Causa**: Clave o cluster incorrecto

**Solución**:
1. Verifica que la clave sea correcta
2. Verifica que el cluster coincida con tu app de Pusher
3. Verifica en Pusher Dashboard que la app esté activa

---

## 📋 Checklist de Variables del Frontend

Antes de deployar, verifica:

- [ ] `NEXT_PUBLIC_SUPABASE_URL` configurada
- [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY` configurada (clave ANON, no service_role)
- [ ] `NEXT_PUBLIC_PUSHER_KEY` configurada
- [ ] `NEXT_PUBLIC_PUSHER_CLUSTER` configurada
- [ ] Todas las variables empiezan con `NEXT_PUBLIC_`
- [ ] No incluiste claves privadas (service_role, secrets, etc.)
- [ ] Probaste localmente con `.env.local`

---

## 🎯 Resumen Rápido

**Solo necesitas 4 variables para el frontend:**

1. `NEXT_PUBLIC_SUPABASE_URL` - URL de Supabase
2. `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Clave pública de Supabase
3. `NEXT_PUBLIC_PUSHER_KEY` - Clave pública de Pusher
4. `NEXT_PUBLIC_PUSHER_CLUSTER` - Región de Pusher

**Todas deben empezar con `NEXT_PUBLIC_` para ser accesibles en el navegador.**

---

**¿Dónde deployar el frontend?**

- **Vercel**: Recomendado, optimizado para Next.js
- **Railway**: Si quieres todo en un lugar
- **Netlify**: Alternativa a Vercel

**Backend (Python/API) va en Railway.**
