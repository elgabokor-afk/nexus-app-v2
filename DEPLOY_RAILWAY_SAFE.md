# 🚂 Deploy en Railway - Variables de Entorno

## 🔑 Variables Requeridas para Railway

Configura estas variables en Railway Dashboard → Settings → Variables

### Supabase (REQUERIDO)
```bash
NEXT_PUBLIC_SUPABASE_URL=tu_supabase_url_aqui
NEXT_PUBLIC_SUPABASE_ANON_KEY=tu_anon_key_aqui
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key_aqui
SUPABASE_URL=tu_supabase_url_aqui
SUPABASE_KEY=tu_service_role_key_aqui
```

### OpenAI (REQUERIDO)
```bash
OPENAI_API_KEY=sk-tu-openai-key-aqui
```

### Binance (REQUERIDO)
```bash
BINANCE_API_KEY=tu_binance_api_key
BINANCE_SECRET=tu_binance_secret
TRADING_MODE=LIVE
```

### Pusher (REQUERIDO para tiempo real)
```bash
NEXT_PUBLIC_PUSHER_KEY=tu_pusher_key
NEXT_PUBLIC_PUSHER_CLUSTER=mt1
PUSHER_APP_ID=tu_pusher_app_id
PUSHER_KEY=tu_pusher_key
PUSHER_SECRET=tu_pusher_secret
PUSHER_CLUSTER=mt1
```

### Sistema
```bash
PORT=8080
PYTHONUNBUFFERED=1
```

### Redis (Opcional)
```bash
REDIS_URL=redis://default:password@redis.railway.internal:6379
```

---

## 📋 Cómo Obtener las Claves

### Supabase:
1. Ve a tu proyecto en supabase.com
2. Settings → API
3. Copia Project URL y las keys

### OpenAI:
1. Ve a platform.openai.com
2. API Keys → Create new key

### Binance:
1. Ve a binance.com
2. Account → API Management
3. Create API Key

### Pusher:
1. Ve a dashboard.pusher.com
2. App Keys
3. Copia las credenciales

---

## ⚠️ IMPORTANTE

**NO subas estas claves a GitHub**

Configúralas directamente en Railway Dashboard.

---

## 🚀 Pasos para Deploy

1. Configura todas las variables en Railway
2. Conecta tu repositorio de GitHub
3. Railway hará deploy automáticamente

O usa Railway CLI:
```bash
railway up
```

---

**Nota**: Copia tus claves reales de tu archivo `.env.local`
