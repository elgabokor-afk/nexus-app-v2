# 🔓 Quitar Protecciones de GitHub

## 📋 Guía Paso a Paso

### Paso 1: Ir a Configuración del Repositorio

1. Ve a tu repositorio en GitHub:
   ```
   https://github.com/elgabokor-afk/nexus-app-v2
   ```

2. Click en **Settings** (arriba a la derecha)

---

### Paso 2: Desactivar Push Protection (Secret Scanning)

1. En el menú izquierdo, busca **Code security and analysis**

2. Busca la sección **"Push protection"**

3. Click en **Disable** para desactivarla

   **Esto permitirá hacer push aunque haya API keys en el historial**

---

### Paso 3: Desactivar Branch Protection Rules (Opcional)

Si también tienes reglas de protección en la rama `main`:

1. En el menú izquierdo, click en **Branches**

2. Busca **"Branch protection rules"**

3. Si ves una regla para `main`, click en **Edit** o **Delete**

4. Opciones a desactivar:
   - ❌ "Require a pull request before merging"
   - ❌ "Require status checks to pass before merging"
   - ❌ "Require conversation resolution before merging"
   - ❌ "Require signed commits"
   - ❌ "Require linear history"

5. Click en **Save changes** o **Delete** (si quieres eliminar la regla completamente)

---

### Paso 4: Verificar que Funciona

Ahora intenta hacer push a `main`:

```powershell
# Cambiar a main
git checkout main

# Merge los cambios de railway-deploy
git merge railway-deploy

# Push a main
git push origin main
```

---

## ⚠️ Consideraciones de Seguridad

### Desactivar Push Protection:

**Pros:**
- ✅ Puedes hacer push sin problemas
- ✅ No necesitas usar ramas alternativas
- ✅ Workflow más simple

**Contras:**
- ⚠️ GitHub no te avisará si subes API keys accidentalmente
- ⚠️ Menos seguridad

### Recomendación:

**Opción 1: Desactivar temporalmente**
- Desactiva Push Protection
- Haz tus cambios
- Reactiva Push Protection después

**Opción 2: Usar .gitignore correctamente**
- Mantén Push Protection activa
- Asegúrate de que `.env.local` esté en `.gitignore`
- Nunca subas archivos con API keys reales

**Opción 3: Usar railway-deploy (actual)**
- Mantén todas las protecciones
- Usa la rama `railway-deploy` para deployment
- `main` solo para código sin secrets

---

## 🎯 Pasos Rápidos (Resumen)

### Para Desactivar Push Protection:

1. GitHub → Tu Repo → **Settings**
2. **Code security and analysis**
3. **Push protection** → **Disable**
4. Confirmar

### Para Desactivar Branch Protection:

1. GitHub → Tu Repo → **Settings**
2. **Branches**
3. **Branch protection rules** → Edit/Delete regla de `main`
4. Desactivar todas las opciones
5. **Save changes**

---

## 📝 Alternativa: Permitir el Secret Específico

Si solo quieres permitir tu OpenAI API key específica:

1. Ve al link que GitHub te dio en el error:
   ```
   https://github.com/elgabokor-afk/nexus-app-v2/security/secret-scanning/unblock-secret/...
   ```

2. Click en **"Allow this secret"**

3. Confirma

Esto permitirá ese secret específico sin desactivar toda la protección.

---

## ✅ Después de Quitar las Protecciones

Podrás hacer push a `main` normalmente:

```powershell
git checkout main
git add .
git commit -m "Tu cambio"
git push origin main
```

Y Railway puede usar la rama `main` directamente.

---

## 🔄 Migrar de railway-deploy a main

Si quieres volver a usar `main`:

```powershell
# 1. Cambiar a main
git checkout main

# 2. Traer cambios de railway-deploy
git merge railway-deploy

# 3. Push a main (ahora sin protecciones)
git push origin main

# 4. Configurar Railway para usar main
# Railway Dashboard → Settings → Source → Branch: main
```

---

**Última actualización**: 31 de enero, 2026
