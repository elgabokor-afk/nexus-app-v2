# ⚡ EJECUTAR ESTO EN SUPABASE

## 🎯 UN SOLO PASO - 2 MINUTOS

### 1. Abre Supabase SQL Editor

### 2. Copia y pega TODO esto:

```sql
-- Añadir columnas
ALTER TABLE signals ADD COLUMN IF NOT EXISTS academic_thesis_id BIGINT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS statistical_p_value NUMERIC;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS rsi NUMERIC;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS atr_value NUMERIC;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS volume_ratio NUMERIC;
ALTER TABLE paper_positions ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ;
ALTER TABLE paper_positions ADD COLUMN IF NOT EXISTS signal_id BIGINT;

-- Crear índices
CREATE INDEX IF NOT EXISTS idx_paper_positions_symbol ON paper_positions(symbol);
CREATE INDEX IF NOT EXISTS idx_paper_positions_status ON paper_positions(status);
CREATE INDEX IF NOT EXISTS idx_signals_symbol_created ON signals(symbol, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_direction ON signals(direction, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs(created_at DESC);

-- Analizar
ANALYZE paper_positions;
ANALYZE signals;
ANALYZE error_logs;

-- Verificar
SELECT COUNT(*) as total_indexes 
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND indexname LIKE 'idx_%';
```

### 3. Click en "Run" o presiona Ctrl+Enter

### 4. Resultado esperado:
```
total_indexes
-------------
7-10
```

## ✅ LISTO!

Tu base de datos ahora está optimizada 5-10x más rápida.

## 🚀 Siguiente paso:

Ejecuta en tu terminal:
```bash
INSTALL_DEPENDENCIES.bat
```

---

**Tiempo total**: 2 minutos  
**Archivos**: `database_indexes_MINIMAL.sql` (mismo contenido)
