# 🚂 CONFIGURACIÓN DE RAILWAY - Variables de Entorno

## 📋 PROBLEMA DETECTADO

Tu frontend muestra 404 porque le falta una variable crítica:
- ❌ `NEXT_PUBLIC_SUPABASE_URL` no está configurada en el servicio de frontend

## ✅ SOLUCIÓN

### 🔴 SERVICIO: FRONTEND (Puerto 3000)

Añade esta variable que falta:

```bash
NEXT_PUBLIC_SUPABASE_URL="https://uxjjqrctxfajzicruvxc.supabase.co"
```

**Variables actuales del frontend:**
```bash
PORT="3000"
NEXT_PUBLIC_API_URL="http://nexus-api.railway.internal:8080"
NEXT_PUBLIC_SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
NEXT_PUBLIC_PUSHER_KEY="dda05a0dc630ab53ec2e"
NEXT_PUBLIC_PUSHER_CLUSTER="mt1"
NEXT_PUBLIC_SITE_URL="https://www.nexuscryptosignals.com"

# ⚠️ FALTA ESTA:
NEXT_PUBLIC_SUPABASE_URL="https://uxjjqrctxfajzicruvxc.supabase.co"
```

---

### 🟢 SERVICIO: BACKEND (Puerto 8080)

Añade estas variables que faltan para Python:

```bash
# Variables actuales (OK)
PORT="8080"
PYTHONUNBUFFERED="1"
NEXT_PUBLIC_SUPABASE_URL="https://tu-proyecto.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="tu_service_role_key_aqui"
OPENAI_API_KEY="sk-tu-key-aqui"
BINANCE_API_KEY="tu_binance_key_aqui"
BINANCE_SECRET="tu_binance_secret_aqui"
TRADING_MODE="PAPER"
PUSHER_APP_ID="tu_pusher_app_id_aqui"
NEXT_PUBLIC_PUSHER_KEY="tu_pusher_key_aqui"
PUSHER_SECRET="tu_pusher_secret_aqui"
NEXT_PUBLIC_PUSHER_CLUSTER="mt1"
CMC_PRO_API_KEY="tu_cmc_key_aqui"
REDIS_URL="redis://default:password@tu-host:6379"

# ⚠️ AÑADE ESTAS (Python las necesita con estos nombres):
SUPABASE_URL="https://tu-proyecto.supabase.co"
SUPABASE_KEY="tu_supabase_key_aqui"
PUSHER_KEY="tu_pusher_key_aqui"
PUSHER_CLUSTER="mt1"
```

---

## 🔧 CÓMO AÑADIR EN RAILWAY

### Paso 1: Ir al Dashboard
1. Abre https://railway.app/
2. Selecciona tu proyecto

### Paso 2: Configurar Frontend
1. Click en el servicio **Frontend** (puerto 3000)
2. Ve a la pestaña **Variables**
3. Click en **+ New Variable**
4. Añade:
   ```
   NEXT_PUBLIC_SUPABASE_URL
   https://uxjjqrctxfajzicruvxc.supabase.co
   ```
5. Click en **Add**

### Paso 3: Configurar Backend
1. Click en el servicio **Backend** (puerto 8080)
2. Ve a la pestaña **Variables**
3. Añade estas 4 variables:
   ```
   SUPABASE_URL
   https://uxjjqrctxfajzicruvxc.supabase.co
   
   SUPABASE_KEY
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4ampxcmN0eGZhanppY3J1dnhjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTAyMzU2NiwiZXhwIjoyMDg0NTk5NTY2fQ.YIekbMFhGMCUViJauFq-8dgBeSYAbpmMXSMOl9hkggk
   
   PUSHER_KEY
   dda05a0dc630ab53ec2e
   
   PUSHER_CLUSTER
   mt1
   ```

### Paso 4: Redeploy
1. Railway detectará los cambios automáticamente
2. O fuerza un redeploy:
   - Click en el servicio
   - Click en **Deploy** → **Redeploy**

---

## ✅ VERIFICACIÓN

Después de añadir las variables y redeploy:

### 1. Verifica el Frontend
- Abre: https://www.nexuscryptosignals.com
- Debería cargar sin 404
- Debería mostrar la interfaz

### 2. Verifica el Backend
- Revisa los logs del servicio backend en Railway
- Busca: "Supabase connected" o "Signal saved"
- No debería haber errores de "SUPABASE_URL not found"

### 3. Verifica Pusher
- Abre: https://dashboard.pusher.com/apps/2107673/getting_started
- Ve a **Debug Console**
- Deberías ver eventos llegando cuando el worker genera señales

---

## 🐛 TROUBLESHOOTING

### Frontend sigue mostrando 404
1. Verifica que añadiste `NEXT_PUBLIC_SUPABASE_URL`
2. Verifica que el servicio se redesployó
3. Limpia caché del navegador (Ctrl+Shift+R)

### Backend no guarda señales
1. Verifica logs en Railway
2. Busca errores de conexión a Supabase
3. Verifica que `SUPABASE_URL` y `SUPABASE_KEY` están configuradas

### Señales no llegan al UI
1. Verifica que Pusher está recibiendo eventos (dashboard)
2. Verifica que el frontend está suscrito al canal correcto
3. Revisa la consola del navegador (F12) para errores de Pusher

---

## 📊 RESUMEN DE VARIABLES POR SERVICIO

### Frontend (3000)
- ✅ PORT
- ✅ NEXT_PUBLIC_API_URL
- ✅ NEXT_PUBLIC_SUPABASE_ANON_KEY
- ✅ NEXT_PUBLIC_PUSHER_KEY
- ✅ NEXT_PUBLIC_PUSHER_CLUSTER
- ✅ NEXT_PUBLIC_SITE_URL
- ❌ **NEXT_PUBLIC_SUPABASE_URL** ← AÑADIR

### Backend (8080)
- ✅ PORT
- ✅ PYTHONUNBUFFERED
- ✅ NEXT_PUBLIC_SUPABASE_URL
- ✅ SUPABASE_SERVICE_ROLE_KEY
- ✅ OPENAI_API_KEY
- ✅ BINANCE_API_KEY
- ✅ BINANCE_SECRET
- ✅ TRADING_MODE
- ✅ PUSHER_APP_ID
- ✅ NEXT_PUBLIC_PUSHER_KEY
- ✅ PUSHER_SECRET
- ✅ NEXT_PUBLIC_PUSHER_CLUSTER
- ✅ CMC_PRO_API_KEY
- ✅ REDIS_URL
- ❌ **SUPABASE_URL** ← AÑADIR
- ❌ **SUPABASE_KEY** ← AÑADIR
- ❌ **PUSHER_KEY** ← AÑADIR
- ❌ **PUSHER_CLUSTER** ← AÑADIR

---

**Tiempo estimado**: 5 minutos  
**Impacto**: Resuelve el 404 y habilita las señales en tiempo real
