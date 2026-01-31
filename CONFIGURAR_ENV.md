# 🔧 CONFIGURAR VARIABLES DE ENTORNO

## 🔴 PROBLEMA DETECTADO

Tu sistema NO tiene configuradas las variables de entorno. Por eso:
- ❌ El frontend muestra 404
- ❌ Las señales no llegan al UI
- ❌ El worker no puede guardar en Supabase
- ❌ Pusher no puede enviar eventos

## ✅ SOLUCIÓN (5 minutos)

### Paso 1: Crear archivo `.env.local`

1. Copia el archivo de ejemplo:
```bash
copy .env.local.example .env.local
```

2. Abre `.env.local` con un editor de texto

### Paso 2: Obtener Credenciales de Supabase

1. Ve a https://app.supabase.com/
2. Selecciona tu proyecto
3. Ve a **Settings** → **API**
4. Copia:
   - **Project URL** → `NEXT_PUBLIC_SUPABASE_URL`
   - **anon public** → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - **service_role** → `SUPABASE_SERVICE_ROLE_KEY`

### Paso 3: Obtener Credenciales de Pusher

1. Ve a https://dashboard.pusher.com/
2. Selecciona tu app (o crea una nueva)
3. Ve a **App Keys**
4. Copia:
   - **app_id** → `PUSHER_APP_ID`
   - **key** → `PUSHER_KEY`
   - **secret** → `PUSHER_SECRET`
   - **cluster** → `PUSHER_CLUSTER` (ej: "us2", "eu", "ap1")

### Paso 4: Configurar Binance (Opcional)

Si quieres trading real:
1. Ve a https://www.binance.com/en/my/settings/api-management
2. Crea una API Key
3. Copia:
   - **API Key** → `BINANCE_API_KEY`
   - **Secret Key** → `BINANCE_SECRET`

⚠️ **IMPORTANTE**: Deja `TRADING_MODE=PAPER` hasta que estés seguro

### Paso 5: Configurar OpenAI (Para AI)

1. Ve a https://platform.openai.com/api-keys
2. Crea una API Key
3. Copia:
   - **API Key** → `OPENAI_API_KEY`

---

## 📝 EJEMPLO DE `.env.local` COMPLETO

```bash
# ============================================================================
# SUPABASE CONFIG
# ============================================================================
NEXT_PUBLIC_SUPABASE_URL=https://tuproyecto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Para Python (mismo que arriba)
SUPABASE_URL=https://tuproyecto.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ============================================================================
# PUSHER CONFIG (Realtime)
# ============================================================================
NEXT_PUBLIC_PUSHER_KEY=tu_pusher_key
NEXT_PUBLIC_PUSHER_CLUSTER=us2

# Para Python
PUSHER_APP_ID=123456
PUSHER_KEY=tu_pusher_key
PUSHER_SECRET=tu_pusher_secret
PUSHER_CLUSTER=us2

# ============================================================================
# BINANCE CONFIG
# ============================================================================
BINANCE_API_KEY=tu_binance_api_key
BINANCE_SECRET=tu_binance_secret
TRADING_MODE=PAPER

# ============================================================================
# OPENAI CONFIG
# ============================================================================
OPENAI_API_KEY=sk-proj-...

# ============================================================================
# TELEGRAM (Opcional - Para alertas)
# ============================================================================
TELEGRAM_BOT_TOKEN=tu_bot_token
TELEGRAM_CHAT_ID=tu_chat_id
```

---

## ✅ VERIFICAR CONFIGURACIÓN

Después de configurar, ejecuta:

```bash
python diagnose_system.py
```

Deberías ver:
```
✅ SUPABASE_URL: https://...
✅ SUPABASE_KEY: eyJhbGci...
✅ PUSHER_APP_ID: 123456
✅ PUSHER_KEY: abc123...
✅ PUSHER_SECRET: def456...
✅ PUSHER_CLUSTER: us2
```

---

## 🚀 DESPUÉS DE CONFIGURAR

1. **Reinicia el worker**:
```bash
cd data-engine
python cosmos_worker.py
```

2. **Reinicia el frontend** (si está corriendo localmente):
```bash
npm run dev
```

3. **Redeploy** (si está en producción):
```bash
DEPLOY.bat
```

---

## 🔍 TROUBLESHOOTING

### Error: "Invalid API key"
- Verifica que copiaste la key completa (sin espacios)
- Verifica que usaste la key correcta (anon vs service_role)

### Error: "Project not found"
- Verifica que la URL de Supabase es correcta
- Verifica que el proyecto existe y está activo

### Pusher no funciona
- Verifica que el cluster es correcto (us2, eu, ap1, etc.)
- Verifica que la app está activa en Pusher dashboard

---

## 📞 AYUDA

Si necesitas ayuda para obtener las credenciales:
1. **Supabase**: https://supabase.com/docs/guides/api
2. **Pusher**: https://pusher.com/docs/channels/getting_started/
3. **Binance**: https://www.binance.com/en/support/faq/360002502072

---

**Tiempo estimado**: 5 minutos  
**Prioridad**: 🔴 CRÍTICA - Sin esto el sistema NO funciona
