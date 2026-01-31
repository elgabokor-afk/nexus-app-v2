# 🚀 INSTRUCCIONES DE DEPLOY - FASE 1

## ✅ Pre-Deploy Checklist

Antes de hacer deploy, verifica:

```bash
# 1. Validar todos los fixes
python validate_fixes.py

# 2. Probar circuit breaker
python data-engine/circuit_breaker.py

# 3. Verificar que no hay errores de sintaxis
python -m py_compile data-engine/cosmos_worker.py
python -m py_compile data-engine/cosmos_engine.py
python -m py_compile data-engine/paper_trader.py
python -m py_compile data-engine/circuit_breaker.py
```

Si todos los comandos pasan sin errores, estás listo para deploy.

---

## 📦 Deploy a Railway

### Opción 1: Deploy Automático (Recomendado)

```bash
# 1. Commit de cambios
git add .
git commit -m "feat: FASE 1 - Implementar fixes críticos (whale_monitor, validación académica, circuit breaker)"

# 2. Push a repositorio
git push origin main

# Railway detectará los cambios automáticamente y hará deploy
```

### Opción 2: Deploy Manual

```bash
# Si usas Railway CLI
railway up
```

---

## 🔧 Configuración Post-Deploy

### 1. Verificar Variables de Entorno en Railway

Asegúrate de que estas variables estén configuradas en Railway:

**Backend (nexus-api)**:
```
SUPABASE_URL=https://uxjjqrctxfajzicruvxc.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
PUSHER_APP_ID=2107673
PUSHER_KEY=dda05a0dc630ab53ec2e
PUSHER_SECRET=e4747199473f7ff11690
PUSHER_CLUSTER=mt1
REDIS_URL=redis://default:LHqSPGcErrkuHuvrbElmnmqkMKHXgnEQ@redis.railway.internal:6379
TRADING_MODE=PAPER
```

**Frontend (nexus-frontend)**:
```
NEXT_PUBLIC_SUPABASE_URL=https://uxjjqrctxfajzicruvxc.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_PUSHER_KEY=dda05a0dc630ab53ec2e
NEXT_PUBLIC_PUSHER_CLUSTER=mt1
```

### 2. Ajustar Circuit Breaker Config

Edita `circuit_breaker_config.json` según tu capital:

```json
{
    "initial_capital": 10000,
    "max_daily_loss_pct": 5.0,
    "max_consecutive_losses": 5,
    "max_drawdown_pct": 10.0,
    "cooldown_minutes": 60,
    "auto_reset_daily": true
}
```

**IMPORTANTE**: Asegúrate de que este archivo esté en el repositorio antes de hacer deploy.

---

## 📊 Monitoreo Post-Deploy

### 1. Verificar Logs en Railway

```bash
# Ver logs del backend
railway logs --service=nexus-api

# Buscar estas líneas en los logs:
# ✅ "[CIRCUIT BREAKER] Protection system loaded"
# ✅ "[CIRCUIT BREAKER] Initialized with capital: $10000"
# ✅ "COSMOS AI WORKER STARTED [RAILWAY MODE]"
```

### 2. Verificar Frontend

Abre tu aplicación en el navegador:
- URL: https://www.nexuscryptosignals.com (o tu dominio)
- Verifica que NO hay error 404 de favicon en la consola
- Verifica que el título de la pestaña dice "Nexus Crypto Signals"

### 3. Verificar Base de Datos

En Supabase SQL Editor:

```sql
-- Verificar que las señales se están guardando
SELECT COUNT(*) FROM signals WHERE created_at > NOW() - INTERVAL '1 hour';

-- Verificar que el paper trader está funcionando
SELECT COUNT(*) FROM paper_positions WHERE status = 'OPEN';

-- Verificar logs de errores
SELECT * FROM error_logs WHERE created_at > NOW() - INTERVAL '1 hour' ORDER BY created_at DESC LIMIT 10;
```

---

## 🚨 Troubleshooting

### Problema: Circuit Breaker no se carga

**Síntoma**: No ves logs de "[CIRCUIT BREAKER]" en Railway

**Solución**:
1. Verifica que `circuit_breaker_config.json` está en el repositorio
2. Verifica que el archivo está en la raíz del proyecto (no en data-engine/)
3. Redeploy:
   ```bash
   git add circuit_breaker_config.json
   git commit -m "fix: Añadir circuit breaker config"
   git push origin main
   ```

### Problema: Worker crashea con NameError

**Síntoma**: Logs muestran "NameError: name 'whale_monitor' is not defined"

**Solución**:
1. Verifica que el fix está aplicado:
   ```bash
   grep "whale_monitor = None" data-engine/cosmos_worker.py
   ```
2. Si no aparece, aplica el fix manualmente y redeploy

### Problema: Favicon 404 persiste

**Síntoma**: Consola del navegador muestra error 404 para favicon.ico

**Solución**:
1. Verifica que `src/app/layout.tsx` tiene la configuración de icons
2. Limpia caché del navegador (Ctrl+Shift+R)
3. Verifica que `public/nexus-logo.png` existe

### Problema: Señales no llegan al frontend

**Síntoma**: Dashboard no muestra señales nuevas

**Solución**:
1. Verifica variables de entorno de Pusher en Railway
2. Verifica que SUPABASE_URL está configurado en el backend
3. Revisa logs del backend para errores de Pusher
4. Verifica que el worker está corriendo:
   ```bash
   railway logs --service=nexus-api | grep "COSMOS WORKER"
   ```

---

## ✅ Validación Final

Después de 1 hora de operación en producción, verifica:

- [ ] No hay crashes en los logs de Railway
- [ ] Circuit breaker aparece en los logs
- [ ] Señales se están generando (revisa tabla `signals` en Supabase)
- [ ] Frontend muestra señales correctamente
- [ ] No hay errores 404 de favicon
- [ ] Paper trader está abriendo/cerrando posiciones

Si todos los checks pasan, ¡el deploy fue exitoso! 🎉

---

## 📈 Próximos 7 Días

Monitorea estas métricas:

1. **Uptime**: Debe ser >99%
2. **Señales generadas**: Al menos 5-10 por día
3. **Circuit breaker activaciones**: Idealmente 0, máximo 1-2
4. **Win rate**: Objetivo >55% después de 50 trades
5. **Drawdown máximo**: Debe mantenerse <10%

---

## 🔄 Rollback (Si algo sale mal)

Si necesitas revertir los cambios:

```bash
# 1. Revertir último commit
git revert HEAD

# 2. Push
git push origin main

# 3. Railway hará deploy automático de la versión anterior
```

O manualmente en Railway:
1. Ve a Deployments
2. Encuentra el deployment anterior que funcionaba
3. Click en "Redeploy"

---

## 📞 Contacto de Emergencia

Si encuentras problemas críticos:

1. Revisa `RESUMEN_IMPLEMENTACION.md` para detalles
2. Ejecuta `python validate_fixes.py` localmente
3. Revisa logs en Railway dashboard
4. Consulta `FIXES_COMPLETADOS.md` para implementación

---

**Última Actualización**: 31 de Enero, 2026  
**Versión**: 1.0  
**Estado**: Listo para Deploy ✅
