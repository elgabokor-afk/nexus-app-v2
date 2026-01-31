# 🚂 Guía de Deployment en Railway

## 📋 Pre-requisitos

1. Cuenta en Railway.app
2. Repositorio Git conectado
3. Variables de entorno configuradas

---

## 🔧 Configuración de Variables de Entorno en Railway

Ve a tu proyecto en Railway → Settings → Variables y agrega:

### Supabase (REQUERIDO)
```
NEXT_PUBLIC_SUPABASE_URL=https://uxjjqrctxfajzicruvxc.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_URL=https://uxjjqrctxfajzicruvxc.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Binance (REQUERIDO para trading)
```
BINANCE_API_KEY=tu_api_key
BINANCE_SECRET=tu_secret_key
TRADING_MODE=LIVE
```

### Pusher (REQUERIDO para tiempo real)
```
NEXT_PUBLIC_PUSHER_KEY=dda05a0dc630ab53ec2e
NEXT_PUBLIC_PUSHER_CLUSTER=mt1
PUSHER_APP_ID=2107673
PUSHER_KEY=dda05a0dc630ab53ec2e
PUSHER_SECRET=e4747199473f7ff11690
PUSHER_CLUSTER=mt1
```

### OpenAI (REQUERIDO para AI)
```
OPENAI_API_KEY=sk-...
```

### Redis (OPCIONAL - Railway puede proveerlo)
```
REDIS_URL=redis://default:password@redis.railway.internal:6379
```

### Otras APIs (OPCIONAL)
```
CMC_PRO_API_KEY=tu_coinmarketcap_key
HELIUS_API_KEY=tu_helius_key
BIRDEYE_API_KEY=tu_birdeye_key
```

### Sistema
```
PORT=8080
PYTHONUNBUFFERED=1
```

---

## 🚀 Deployment Steps

### Opción 1: Deployment Automático (Recomendado)

1. **Conecta tu repositorio a Railway**
   - Ve a Railway Dashboard
   - Click en "New Project"
   - Selecciona "Deploy from GitHub repo"
   - Autoriza y selecciona tu repositorio

2. **Railway detectará automáticamente:**
   - `Dockerfile` para el build
   - `Procfile` para el comando de inicio
   - `requirements.txt` para las dependencias

3. **Configura las variables de entorno**
   - Ve a Settings → Variables
   - Agrega todas las variables listadas arriba

4. **Deploy**
   - Railway hará el deploy automáticamente
   - Monitorea los logs en tiempo real

### Opción 2: Railway CLI

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Inicializar proyecto
railway init

# Agregar variables de entorno
railway variables set SUPABASE_URL=https://...
railway variables set BINANCE_API_KEY=...
# ... (todas las demás)

# Deploy
railway up
```

---

## 📊 Verificación del Deployment

### 1. Verificar que los servicios están corriendo

Revisa los logs en Railway Dashboard:

```
✅ Cosmos Worker started (PID: xxx)
✅ AI Oracle started (PID: xxx)
✅ Macro Feed started (PID: xxx)
✅ Nexus Executor started (PID: xxx)
✅ STARTING NEXUS UNIFIED API
```

### 2. Verificar el Health Check

Accede a tu URL de Railway:
```
https://tu-app.railway.app/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "version": "v5.0",
  "services": {
    "supabase": "connected",
    "redis": "connected",
    "pusher": "configured",
    "websocket_clients": 0
  }
}
```

### 3. Verificar que genera señales

Espera 2-3 minutos y verifica en Supabase:
```sql
SELECT * FROM signals 
ORDER BY created_at DESC 
LIMIT 5;
```

Deberías ver señales recientes (menos de 5 minutos).

---

## 🔍 Troubleshooting

### Problema: Worker no inicia

**Síntomas**: No hay logs de "Cosmos Worker started"

**Solución**:
1. Verifica que todas las variables de entorno estén configuradas
2. Revisa los logs completos en Railway
3. Verifica que `requirements.txt` tenga todas las dependencias

### Problema: "Module not found"

**Síntomas**: Error de importación en los logs

**Solución**:
```bash
# Asegúrate de que requirements.txt esté actualizado
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

### Problema: No genera señales

**Síntomas**: Worker corre pero no hay señales nuevas

**Solución**:
1. Verifica que Binance API esté configurada correctamente
2. Revisa los logs del worker para errores
3. Verifica que el Circuit Breaker no esté activado:
   ```sql
   SELECT * FROM error_logs 
   WHERE message LIKE '%CIRCUIT BREAKER%' 
   ORDER BY created_at DESC;
   ```

### Problema: Frontend no recibe actualizaciones

**Síntomas**: Página no se actualiza en tiempo real

**Solución**:
1. Verifica que Pusher esté configurado correctamente
2. Verifica en Pusher Dashboard que los eventos se están enviando
3. Revisa la consola del navegador para errores de WebSocket

---

## 📈 Monitoreo

### Logs en Railway

Railway proporciona logs en tiempo real:
- Click en tu servicio
- Ve a la pestaña "Logs"
- Filtra por servicio si es necesario

### Métricas importantes

Monitorea:
- **CPU Usage**: Debería estar < 50%
- **Memory Usage**: Debería estar < 512 MB
- **Request Rate**: Depende del tráfico
- **Error Rate**: Debería ser < 1%

### Alertas

Configura alertas en Railway para:
- Deployment failures
- High error rate
- Service crashes

---

## 🔄 Actualizaciones

### Deploy automático

Railway hace deploy automático cuando haces push a tu rama principal:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

Railway detectará el cambio y hará redeploy automáticamente.

### Rollback

Si algo sale mal:
1. Ve a Railway Dashboard
2. Click en "Deployments"
3. Selecciona un deployment anterior
4. Click en "Redeploy"

---

## 💰 Costos Estimados

Railway ofrece:
- **Hobby Plan**: $5/mes + uso
- **Pro Plan**: $20/mes + uso

Costos estimados para Nexus AI:
- **Compute**: ~$10-15/mes (512 MB RAM, 0.5 vCPU)
- **Bandwidth**: ~$2-5/mes
- **Total**: ~$17-25/mes

---

## 🎯 Checklist de Deployment

Antes de hacer deploy, verifica:

- [ ] Todas las variables de entorno configuradas
- [ ] `requirements.txt` actualizado
- [ ] `Dockerfile` optimizado
- [ ] `start_services.sh` tiene permisos de ejecución
- [ ] Supabase tiene todas las tablas creadas
- [ ] Índices de base de datos aplicados
- [ ] Pusher configurado y funcionando
- [ ] Binance API con permisos correctos

Después del deploy, verifica:

- [ ] Health check responde correctamente
- [ ] Worker genera señales (espera 5 minutos)
- [ ] Frontend recibe actualizaciones en tiempo real
- [ ] No hay errores críticos en los logs
- [ ] Circuit Breaker no está activado

---

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs en Railway Dashboard
2. Verifica la tabla `error_logs` en Supabase
3. Ejecuta el diagnóstico: `python check_ai_status.py`
4. Revisa esta guía de troubleshooting

---

**Última actualización**: 31 de enero, 2026
**Versión**: 5.0
