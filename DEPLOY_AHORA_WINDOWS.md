# 🚀 Deploy a Railway - Windows

## ⚡ Opción Rápida (Recomendada)

Ejecuta uno de estos archivos .bat:

### 1. Deploy Mínimo (Solo API) - Para Testing
```
deploy_minimal.bat
```
- Inicia solo el API
- Más rápido y simple
- Ideal para verificar que funciona

### 2. Deploy Simple (API + Worker) - Recomendado
```
deploy_simple.bat
```
- Inicia API + Worker de señales
- Balance entre funcionalidad y simplicidad
- **RECOMENDADO PARA EMPEZAR**

### 3. Deploy Completo (Todos los Servicios)
```
deploy_full.bat
```
- Inicia todos los servicios
- Más completo pero más complejo
- Usar después de verificar que funciona el simple

---

## 📋 Paso a Paso Manual

Si prefieres hacerlo manualmente:

### Paso 1: Editar Procfile

Abre `Procfile` y cambia el contenido a:

```
web: bash start_minimal.sh
```

### Paso 2: Commit y Push

```powershell
git add Procfile
git commit -m "Deploy minimal version"
git push
```

### Paso 3: Esperar

Railway hará el deploy automáticamente. Espera 2-3 minutos.

### Paso 4: Verificar Logs

Ve a Railway Dashboard → Tu Servicio → Logs

Deberías ver:
```
=== NEXUS AI STARTING ===
Python version: 3.11.x
Starting API only (minimal mode)...
INFO: Uvicorn running on http://0.0.0.0:8080
```

---

## ✅ Verificar que Funciona

### Opción 1: Desde PowerShell

```powershell
# Reemplaza TU-URL con tu URL de Railway
Invoke-WebRequest -Uri "https://TU-URL.railway.app/health"
```

### Opción 2: Desde el Navegador

Abre en tu navegador:
```
https://TU-URL.railway.app/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "version": "v5.0",
  "services": {
    "supabase": "connected"
  }
}
```

---

## 🔄 Cambiar de Versión

### De Mínimo a Simple:
```
deploy_simple.bat
```

### De Simple a Completo:
```
deploy_full.bat
```

### Volver a Mínimo:
```
deploy_minimal.bat
```

---

## 🐛 Si Hay Problemas

### 1. No hay logs en Railway

**Solución**: Usa la versión mínima primero
```
deploy_minimal.bat
```

### 2. Error "git not found"

**Solución**: Instala Git para Windows
- https://git-scm.com/download/win

### 3. Error "permission denied"

**Solución**: Ejecuta como Administrador
- Click derecho en el .bat → "Ejecutar como administrador"

### 4. Railway no hace redeploy

**Solución**: Verifica que el push se haya completado
```powershell
git status
git log -1
```

---

## 📊 Estrategia Recomendada

### Día 1: Deploy Mínimo
```
deploy_minimal.bat
```
- Verifica que el API funcione
- Prueba el endpoint /health
- Revisa los logs

### Día 2: Deploy Simple
```
deploy_simple.bat
```
- Agrega el worker de señales
- Verifica que genere señales
- Monitorea por 1 hora

### Día 3: Deploy Completo
```
deploy_full.bat
```
- Activa todos los servicios
- Monitoreo completo
- Sistema en producción

---

## 🎯 Comando Único (Todo en Uno)

Si quieres hacer todo de una vez:

```powershell
# Commit todos los cambios
git add .
git commit -m "Optimized for Railway deployment"
git push

# Railway hará redeploy automáticamente
```

---

## 📞 Siguiente Paso

1. **Ejecuta**: `deploy_minimal.bat`
2. **Espera**: 2-3 minutos
3. **Verifica**: Logs en Railway
4. **Prueba**: https://tu-url.railway.app/health

Si funciona, pasa a `deploy_simple.bat`

---

**Última actualización**: 31 de enero, 2026
