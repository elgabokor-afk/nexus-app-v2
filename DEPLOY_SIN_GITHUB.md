# 🚀 Deploy a Railway SIN GitHub

## 🚨 Problema: GitHub Bloqueando por API Keys

GitHub detectó API keys en el historial de commits y está bloqueando todos los pushes.

## ✅ Solución: Railway CLI (Deploy Directo)

Railway puede deployar directamente desde tu máquina sin usar GitHub.

---

## 📋 Paso 1: Instalar Railway CLI

```powershell
npm install -g @railway/cli
```

Si no tienes npm, descarga Node.js primero:
- https://nodejs.org/

---

## 📋 Paso 2: Login a Railway

```powershell
railway login
```

Esto abrirá tu navegador para autenticarte.

---

## 📋 Paso 3: Link al Proyecto

```powershell
railway link
```

Selecciona tu proyecto existente de la lista.

---

## 📋 Paso 4: Deploy

```powershell
railway up
```

Esto deployará directamente desde tu máquina local.

---

## 🎯 Comando Todo-en-Uno

```powershell
# Instalar CLI
npm install -g @railway/cli

# Login
railway login

# Link proyecto
railway link

# Deploy
railway up
```

---

## ✅ Ventajas de Railway CLI

1. **No usa GitHub** - Bypasea completamente el problema de las API keys
2. **Más rápido** - Deploy directo desde tu máquina
3. **Más control** - Puedes deployar sin commit
4. **Debugging fácil** - Ves los logs en tiempo real

---

## 📊 Verificar el Deploy

Después del deploy, Railway te dará una URL. Verifica:

```powershell
# Reemplaza con tu URL
curl https://tu-url.railway.app/health
```

O abre en el navegador:
```
https://tu-url.railway.app/health
```

---

## 🔄 Deployar Actualizaciones

Cada vez que hagas cambios:

```powershell
railway up
```

No necesitas commit ni push.

---

## 📝 Alternativa: Limpiar Historial de Git

Si prefieres seguir usando GitHub, necesitas limpiar el historial:

```powershell
# CUIDADO: Esto borra el historial
git checkout --orphan temp-branch
git add .
git commit -m "Fresh start - no secrets"
git branch -D railway-deploy
git branch -m railway-deploy
git push origin railway-deploy --force
```

**⚠️ ADVERTENCIA**: Esto borra todo el historial de Git.

---

## 🎯 Recomendación

**Usa Railway CLI** - Es más simple y evita problemas con GitHub.

```powershell
npm install -g @railway/cli
railway login
railway link
railway up
```

---

**Última actualización**: 31 de enero, 2026
