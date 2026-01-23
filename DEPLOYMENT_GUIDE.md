# Guía de Despliegue: TrendsAI Fullstack

¡Cuidado! No puedes subir "todo a Netlify" tal cual, porque tienes dos tecnologías diferentes que funcionan de distinta manera.

Tu sistema ahora tiene dos partes:
1.  **Frontend (La Web)**: Next.js + React.
2.  **Backend (El Robot)**: Python script (`scanner.py`).

Aquí tienes cómo desplegar cada una correctamente:

---

## 🏗️ Parte 1: El Frontend (La Web)
**Destino ideal**: Vercel (Recomendado) o Netlify.

Esta es la parte que ven tus usuarios (el Dashboard).
1.  Sube tu carpeta `nexus-app-v2` a GitHub.
2.  Ve a [Vercel.com](https://vercel.com) (creadores de Next.js) o Netlify.
3.  Importa el repositorio.
4.  **Configuración de Entorno**:
    *   En Vercel/Netlify, ve a "Environment Variables".
    *   Añade las mismas claves que tienes en `.env.local`:
        *   `NEXT_PUBLIC_SUPABASE_URL`
        *   `NEXT_PUBLIC_SUPABASE_ANON_KEY`
5.  Dale a "Deploy". ¡Listo! Tu web estará en `https://nexus-app.vercel.app`.

---

## 🤖 Parte 2: El Backend (El Robot Python)
**Destino ideal**: Railway.app o Render.com.
**¿Por qué NO Netlify?**: Netlify solo sirve webs. Si subes el script de Python allí, se apagará a los 10 segundos. Tu robot necesita estar encendido 24/7.

### Opción A: Railway (Más fácil)
1.  Sube tu carpeta `nexus-app-v2` a GitHub (ya lo hiciste en el paso 1).
2.  Ve a [Railway.app](https://railway.app).
3.  "New Project" -> "Deploy from GitHub repo".
4.  **Importante**: Railway intentará detectar el proyecto. Debes decirle que ejecute el Python.
5.  Configura el comando de inicio (Start Command):
    ```bash
    cd data-engine && python scanner.py
    ```
6.  Añade las Variables de Entorno (las mismas de Supabase + Service Role Key):
    *   `NEXT_PUBLIC_SUPABASE_URL`
    *   `SUPABASE_SERVICE_ROLE_KEY`
7.  ¡Listo! Railway mantendrá tu script corriendo 24/7 escaneando Binance.

---

##  RESUMEN
| Carpeta | Qué es | Dónde se sube |
| :--- | :--- | :--- |
| `nexus-app-v2/` | Página Web (Next.js) | **Vercel** o **Netlify** |
| `nexus-app-v2/data-engine/` | Robot de Trading (Python) | **Railway** o **Render** |

**Nota**: Si solo subes la web a Netlify y no subes el robot a Railway, la web funcionará pero **no mostrará señales nuevas**, porque nadie estará alimentando la base de datos en la nube.
