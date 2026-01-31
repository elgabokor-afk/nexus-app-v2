# 🔧 Railway: No Logs - Solución

## 🚨 Problema: No aparecen logs en Railway

Si no ves logs en Railway, significa que el contenedor está fallando antes de iniciar.

---

## ✅ Solución Rápida

### Paso 1: Usar el script minimalista

He creado 3 versiones del script de inicio:

1. **start_services.sh** - Completo (todos los servicios)
2. **start_services_simple.sh** - Simplificado (worker + API)
3. **start_minimal.sh** - Mínimo (solo API)

### Paso 2: Cambiar el Procfile

Edita el `Procfile` para usar la versión mínima:

```bash
web: bash start_minimal.sh
```

Commit y push:
```bash
git add Procfile
git commit -m "Use minimal startup script"
git push
```

### Paso 3: Verificar en Railway

Espera 2-3 minutos y revisa los logs. Deberías ver:

```
=== NEXUS AI STARTING ===
Python version: 3.11.x
Working directory: /app
PORT: 8080
==========================
Starting API only (minimal mode)...
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

---

## 🔍 Diagnóstico Avanzado

### Opción 1: Ejecutar diagnóstico en Railway

Cambia temporalmente el `Procfile` a:

```bash
web: python railway_debug.py && bash start_minimal.sh
```

Esto ejecutará el diagnóstico antes de iniciar el servicio.

### Opción 2: Verificar variables de entorno

En Railway Dashboard:
1. Ve a tu servicio
2. Settings → Variables
3. Verifica que estén todas las variables críticas:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `BINANCE_API_KEY`
   - `PUSHER_APP_ID`
   - `OPENAI_API_KEY`

### Opción 3: Revisar el build log

En Railway:
1. Ve a Deployments
2. Click en el deployment activo
3. Ve a la pestaña "Build Logs"
4. Busca errores en el build

---

## 🐛 Problemas Comunes

### 1. "No such file or directory: start_services.sh"

**Causa**: El script no tiene permisos de ejecución o no existe

**Solución**:
```bash
chmod +x start_services.sh start_services_simple.sh start_minimal.sh
git add .
git commit -m "Fix script permissions"
git push
```

### 2. "ModuleNotFoundError: No module named 'xxx'"

**Causa**: Dependencia faltante en requirements.txt

**Solución**:
```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

### 3. "Connection refused" o "Supabase error"

**Causa**: Variables de entorno no configuradas

**Solución**: Verifica en Railway Settings → Variables

### 4. "Port already in use"

**Causa**: Railway no está pasando la variable PORT correctamente

**Solución**: Asegúrate de que el script use `${PORT:-8080}`

---

## 🔄 Estrategia de Escalado

### Fase 1: Solo API (Mínimo)

```bash
# Procfile
web: bash start_minimal.sh
```

Esto inicia solo el API. Verifica que funcione:
- `https://tu-url.railway.app/health`

### Fase 2: API + Worker (Simple)

Una vez que el API funcione, agrega el worker:

```bash
# Procfile
web: bash start_services_simple.sh
```

### Fase 3: Todos los servicios (Completo)

Finalmente, usa el script completo:

```bash
# Procfile
web: bash start_services.sh
```

---

## 📝 Checklist de Verificación

Antes de hacer deploy, verifica:

- [ ] `Procfile` apunta al script correcto
- [ ] Scripts tienen permisos de ejecución (`chmod +x`)
- [ ] `requirements.txt` tiene todas las dependencias
- [ ] Variables de entorno configuradas en Railway
- [ ] `Dockerfile` copia todos los archivos necesarios
- [ ] `data-engine/` existe y tiene todos los archivos Python

---

## 🚀 Comandos Rápidos

### Usar versión mínima (solo API):
```bash
echo "web: bash start_minimal.sh" > Procfile
git add Procfile
git commit -m "Use minimal startup"
git push
```

### Usar versión simple (API + Worker):
```bash
echo "web: bash start_services_simple.sh" > Procfile
git add Procfile
git commit -m "Use simple startup"
git push
```

### Ejecutar diagnóstico:
```bash
echo "web: python railway_debug.py && bash start_minimal.sh" > Procfile
git add Procfile
git commit -m "Add diagnostic"
git push
```

---

## 📊 Verificar que Funciona

### 1. Health Check
```bash
curl https://tu-url.railway.app/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "version": "v5.0",
  "services": {
    "supabase": "connected",
    "redis": "connected",
    "pusher": "configured"
  }
}
```

### 2. Root Endpoint
```bash
curl https://tu-url.railway.app/
```

Respuesta esperada:
```json
{
  "status": "ok",
  "version": "v5.0"
}
```

### 3. Logs en Railway

Deberías ver:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

---

## 🆘 Si Nada Funciona

### Plan B: Deploy solo el API

Crea un `Procfile` ultra-simple:

```bash
web: cd data-engine && python -m uvicorn nexus_api:app --host 0.0.0.0 --port $PORT
```

Esto inicia SOLO el API, sin workers ni servicios adicionales.

Una vez que funcione, puedes agregar los workers gradualmente.

---

## 📞 Siguiente Paso

1. **Cambia el Procfile** a la versión mínima
2. **Commit y push**
3. **Espera 2-3 minutos**
4. **Revisa los logs en Railway**
5. **Verifica el health endpoint**

Si ves logs, el problema está resuelto. Si no, ejecuta el diagnóstico.

---

**Última actualización**: 31 de enero, 2026
