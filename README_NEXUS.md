# Nexus TrendsAI Platform (v2.0)

Esta es la nueva plataforma Fullstack para TrendsAI, construida con la arquitectura "Fintech Standard": **Next.js + Python + Supabase**.

## 1. Estructura del Proyecto

*   **Frontend (`/`)**: Aplicación Next.js 14 (React) moderna.
    *   `src/app/dashboard`: Página principal del scanner.
    *   `src/components`: Componentes UI (Gráficos, Señales).
    *   `src/lib`: Cliente de conexión a Supabase.
*   **Backend / Data Engine (`/data-engine`)**:
    *   `scanner.py`: Script de Python que conecta a Binance y detecta señales.
    *   `db.py`: Módulo de conexión para guardar señales en la base de datos.
    *   `requirements.txt`: Librerías necesarias (ccxt, pandas, requests).

## 2. Cómo Iniciar el Sistema

### Paso A: Iniciar el Frontend (Web)
1.  Abre una terminal en esta carpeta (`nexus-app-v2`).
2.  Ejecuta:
    ```bash
    npm run dev
    ```
3.  La web estará disponible en `http://localhost:3000/dashboard`.

### Paso B: Iniciar el Motor de Datos (Python)
1.  Abre **otra** terminal y entra a la carpeta del motor:
    ```bash
    cd data-engine
    ```
2.  Ejecuta el escáner:
    ```bash
    python scanner.py
    ```
3.  Verás cómo analiza el mercado. Si encuentra una señal (RSI < 30), la enviará automáticamente a la web.

## 3. Despliegue (Producción)

*   **Web**: Se recomienda desplegar esta carpeta en **Vercel** (automático con Next.js).
*   **Python Worker**: Se puede desplegar en un VPS (DigitalOcean, AWS) o como un "Background Worker" en plataformas como Railway o Render.
