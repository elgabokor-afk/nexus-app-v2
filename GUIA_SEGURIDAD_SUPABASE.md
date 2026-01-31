# 🔒 GUÍA: Resolver Problemas de Seguridad en Supabase

## 📋 Problemas Detectados

El Security Advisor de Supabase detectó **3 errores de seguridad**:

1. ❌ **Security Definer View** en `public.paper_stats`
2. ❌ **RLS Disabled** en `public.paper_players`
3. ❌ **RLS Disabled** en `public.paper_attempts`

---

## ⚠️ ¿Por qué es importante?

### RLS Disabled (Row Level Security)
- **Riesgo**: Cualquier usuario puede ver TODOS los datos de la tabla
- **Impacto**: Violación de privacidad, usuarios pueden ver datos de otros usuarios
- **Severidad**: ALTA

### Security Definer View
- **Riesgo**: Escalación de privilegios, bypass de RLS
- **Impacto**: Usuarios pueden acceder a datos que no deberían ver
- **Severidad**: MEDIA

---

## 🛠️ Solución Rápida (5 minutos)

### Paso 1: Abrir Supabase SQL Editor
1. Ve a https://supabase.com
2. Abre tu proyecto
3. Click en "SQL Editor" en el menú lateral

### Paso 2: Ejecutar el Script de Seguridad
1. Click en "New Query"
2. Abre el archivo `fix_security_issues.sql` en tu editor local
3. Copia TODO el contenido
4. Pega en el SQL Editor de Supabase
5. Click en "Run" (o Ctrl+Enter)

### Paso 3: Verificar que se Resolvió
1. Ve a "Security Advisor" en Supabase
2. Click en "Refresh"
3. Los 3 errores deberían desaparecer ✅

---

## 📝 ¿Qué hace el script?

### Fix 1: Habilitar RLS en paper_players
```sql
ALTER TABLE public.paper_players ENABLE ROW LEVEL SECURITY;
```
- Habilita Row Level Security
- Crea políticas para que usuarios solo vean sus propios datos
- Usa `auth.uid()` para filtrar por usuario

### Fix 2: Habilitar RLS en paper_attempts
```sql
ALTER TABLE public.paper_attempts ENABLE ROW LEVEL SECURITY;
```
- Similar al anterior
- Protege los intentos de cada usuario

### Fix 3: Arreglar paper_stats View
```sql
CREATE OR REPLACE VIEW public.paper_stats
WITH (security_invoker = true)
AS ...
```
- Cambia de SECURITY DEFINER a SECURITY INVOKER
- Ahora la vista respeta los permisos del usuario que la consulta

---

## ⚠️ IMPORTANTE: Verificar Antes de Ejecutar

### Verificar si las tablas existen:
```sql
-- Ejecuta esto primero para ver qué tablas tienes
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('paper_players', 'paper_attempts', 'paper_stats');
```

### Si las tablas NO existen:
- **No te preocupes**, estos errores pueden ser de tablas antiguas o de prueba
- Puedes ignorarlos o eliminar las tablas si no las usas:
  ```sql
  DROP TABLE IF EXISTS public.paper_players CASCADE;
  DROP TABLE IF EXISTS public.paper_attempts CASCADE;
  DROP VIEW IF EXISTS public.paper_stats CASCADE;
  ```

### Si las tablas SÍ existen:
- Ejecuta el script `fix_security_issues.sql`
- Verifica que tienes columna `user_id` en las tablas
- Si no tienes `user_id`, ajusta las políticas según tu estructura

---

## 🔍 Verificación Post-Fix

### 1. Verificar RLS Habilitado
```sql
SELECT 
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('paper_players', 'paper_attempts');
```
**Resultado esperado**: `rowsecurity = true` para ambas tablas

### 2. Verificar Políticas Creadas
```sql
SELECT 
    tablename,
    policyname,
    cmd
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('paper_players', 'paper_attempts');
```
**Resultado esperado**: 3 políticas por tabla (SELECT, INSERT, UPDATE)

### 3. Verificar Security Advisor
- Ve a Security Advisor en Supabase
- Click en "Refresh"
- **Resultado esperado**: 0 errores ✅

---

## 🎯 Alternativa: Eliminar Tablas No Usadas

Si estas tablas son de prueba o no las usas:

```sql
-- CUIDADO: Esto eliminará las tablas y todos sus datos
DROP TABLE IF EXISTS public.paper_players CASCADE;
DROP TABLE IF EXISTS public.paper_attempts CASCADE;
DROP VIEW IF EXISTS public.paper_stats CASCADE;
```

Después, refresca el Security Advisor y los errores desaparecerán.

---

## 📊 Tablas Principales del Sistema

Las tablas críticas de tu sistema son:
- `signals` - Señales de trading
- `paper_positions` - Posiciones del paper trader
- `paper_trades` - Trades ejecutados
- `bot_wallet` - Wallet del bot
- `error_logs` - Logs de errores

**Estas tablas ya tienen RLS configurado correctamente** ✅

---

## ⚠️ Si Algo Sale Mal

### Rollback:
```sql
-- Deshabilitar RLS (solo si es necesario)
ALTER TABLE public.paper_players DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.paper_attempts DISABLE ROW LEVEL SECURITY;

-- Eliminar políticas
DROP POLICY IF EXISTS "Users can view their own paper_players" ON public.paper_players;
DROP POLICY IF EXISTS "Users can insert their own paper_players" ON public.paper_players;
DROP POLICY IF EXISTS "Users can update their own paper_players" ON public.paper_players;

DROP POLICY IF EXISTS "Users can view their own paper_attempts" ON public.paper_attempts;
DROP POLICY IF EXISTS "Users can insert their own paper_attempts" ON public.paper_attempts;
```

---

## 🎯 Checklist

- [ ] Verificar si las tablas existen
- [ ] Decidir: ¿Arreglar o eliminar?
- [ ] Ejecutar script correspondiente
- [ ] Verificar en Security Advisor
- [ ] Confirmar 0 errores

---

## 📞 Notas Adicionales

1. **Si no usas estas tablas**: Elimínalas con DROP TABLE
2. **Si las usas**: Ejecuta el script de seguridad
3. **Si no estás seguro**: Pregunta antes de ejecutar

**Tiempo estimado**: 5 minutos  
**Impacto**: Mejora la seguridad de tu base de datos  
**Riesgo**: Bajo (solo afecta tablas específicas)

---

**Próximo Paso**: Ejecutar el script y verificar en Security Advisor ✅
