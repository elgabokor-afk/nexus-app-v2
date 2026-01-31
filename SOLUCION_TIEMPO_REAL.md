# 🔴 PROBLEMA: Sistema No Genera Señales en Tiempo Real

## Diagnóstico Completo

### ✅ Lo que SÍ funciona:
1. **Base de datos**: Conectada y operativa
2. **Pusher (Realtime)**: Configurado correctamente
3. **Binance API**: Conectada en modo LIVE
4. **Frontend**: Configurado para recibir señales en tiempo real
5. **Circuit Breaker**: Desactivado (no está bloqueando)
6. **Parámetros del bot**: Configurados correctamente (55% confianza mínima)

### ❌ El PROBLEMA PRINCIPAL:
**El worker de Cosmos AI NO está corriendo**

- Última señal generada: Hace 8.6 horas (30 de enero, 16:28)
- El worker se reinicia pero no completa ciclos de escaneo
- Sin worker activo = Sin señales nuevas = Sin actualizaciones en tiempo real

---

## 🔧 SOLUCIÓN

### Paso 1: Iniciar el Worker

Ejecuta uno de estos comandos:

```bash
# Opción 1: Script automatizado (RECOMENDADO)
START_AI_WORKER.bat

# Opción 2: Manual
cd data-engine
python cosmos_worker.py
```

### Paso 2: Verificar que está funcionando

El worker debe mostrar logs como:
```
[COSMOS WORKER] - INFO - Scanning markets...
[COSMOS WORKER] - INFO - Scanning 15 Assets: ['BTC/USDT', 'ETH/USDT', ...]
[COSMOS WORKER] - INFO - >>> SIGNAL FOUND: BTC/USDT BUY (Conf: 87%)
[COSMOS WORKER] - INFO - Published Signal: BTC/USDT
```

### Paso 3: Verificar señales en tiempo real

Ejecuta el diagnóstico:
```bash
python check_ai_status.py
```

Deberías ver señales recientes (menos de 5 minutos).

---

## 📊 Configuración del Worker

El worker escanea el mercado cada **60 segundos** y:

1. **Analiza 15+ pares** (BTC, ETH, SOL, etc.)
2. **Aplica filtros de confianza** (mínimo 55%)
3. **Valida con múltiples timeframes** (5m, 15m, 4h)
4. **Verifica confluencia técnica** (RSI, MACD, EMA)
5. **Aplica validación académica** (PhD layer)
6. **Transmite vía Pusher** al frontend en tiempo real

---

## 🚨 Problemas Comunes

### 1. Worker se detiene solo
**Causa**: Error en alguna dependencia o API
**Solución**: Revisar logs en `error_logs` table

### 2. Worker corre pero no genera señales
**Causa**: Mercado sin oportunidades o filtros muy estrictos
**Solución**: 
- Verificar que `min_confidence` no sea > 85%
- Revisar que no haya activos en blacklist

### 3. Señales no llegan al frontend
**Causa**: Pusher no configurado o canales incorrectos
**Solución**: Verificar variables PUSHER_* en .env.local

---

## 🔍 Monitoreo Continuo

### Verificar estado del sistema:
```bash
python check_ai_status.py
```

### Ver actividad reciente:
```bash
python data-engine/check_recent_activity.py
```

### Ver estadísticas de la base de datos:
```bash
python data-engine/check_db_stats.py
```

---

## 📝 Notas Importantes

1. **El worker DEBE mantenerse corriendo** para generar señales
2. En producción (Railway/Heroku), usa el `Procfile` para mantenerlo activo
3. El worker consume ~50-100 MB RAM y es CPU-light
4. Genera 1-5 señales por hora en promedio (depende del mercado)

---

## 🎯 Próximos Pasos

1. ✅ Iniciar el worker con `START_AI_WORKER.bat`
2. ✅ Verificar que genera señales cada 1-2 minutos
3. ✅ Confirmar que el frontend las recibe en tiempo real
4. ✅ Monitorear por 30 minutos para asegurar estabilidad

---

## 🆘 Si el problema persiste

1. Revisar logs del worker en consola
2. Verificar tabla `error_logs` en Supabase
3. Confirmar que Binance API tiene permisos de lectura
4. Verificar que no hay rate limits activos

---

**Última actualización**: 31 de enero, 2026
**Estado**: Worker detenido - Requiere reinicio manual
