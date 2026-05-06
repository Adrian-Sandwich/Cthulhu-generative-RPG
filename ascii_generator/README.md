# ASCII Art Generator - Lovecraftian Edition

Generador de ASCII art realista basado en texto usando Stable Diffusion XL + React.

```
Texto (prompt) → Imagen (HuggingFace SDXL) → ASCII Art
```

## Arquitectura

- **Backend**: Flask (puerto 5001) + HuggingFace Inference API
- **Frontend**: React 18 + Vite (puerto 5173) con hot reload
- **Pipeline**: Stable Diffusion XL → Pillow → ASCII conversion

## Instalación

### 1. Instalar dependencias Python

```bash
# En la raíz del proyecto
pip install requests python-dotenv flask flask-cors
```

### 2. Configurar variables de entorno

El archivo `.env` ya está creado en `ascii_generator/.env` con tu HF_TOKEN.

```bash
cat ascii_generator/.env
# HF_TOKEN=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
# FLASK_PORT=5001
# DEBUG=True
```

### 3. Instalar dependencias de React

```bash
cd ascii_generator/client
npm install
```

## Correr la aplicación

### Terminal 1: Backend Flask

```bash
cd /Users/adrianmedina/src/Cthulhu
python ascii_generator/server.py

# Output:
# 🎨 ASCII Art Generator Server
# 📍 Port: 5001
# 🔗 http://localhost:5001
# 🔄 Debug: True
```

### Terminal 2: Frontend React (con hot reload)

```bash
cd ascii_generator/client
npm run dev

# Output:
#   VITE v4.3.0  ready in 234 ms
#   ➜  Local:   http://localhost:5173/
#   ➜  press h to show help
```

### Abrir en el navegador

```
http://localhost:5173
```

## Uso

1. **Escribe una descripción** de la escena (en la textarea izquierda)
   - Ej: "A dark lighthouse on a rocky coast with fog"

2. **Ajusta parámetros**:
   - Ancho ASCII (40-120 caracteres)
   - Charset (dark, detailed, blocks, standard, artistic)
   - Estilo (lovecraftian, standard)
   - Mejorar con bordes (checkbox)

3. **Haz clic en "Generar ASCII Art"**
   - Espera 30-60 segundos mientras se genera la imagen

4. **Verás**:
   - Imagen original generada por Stable Diffusion XL
   - ASCII art de esa imagen
   - Botón para descargar como .txt

## Flujo de datos

```
Usuario escribe prompt
  ↓
POST /api/generate {prompt, width, charset, style}
  ↓
Backend: Flask recibe solicitud
  ↓
image_gen.py: Llama HuggingFace API
  ↓
Stable Diffusion XL genera imagen PNG
  ↓
ascii_render.py: Convierte PNG → string ASCII
  ↓
Backend retorna: {ascii_art, image_base64, metadata}
  ↓
React muestra imagen + ASCII art
  ↓
Cambios en App.jsx se actualizan en tiempo real (HMR)
```

## Endpoints disponibles

### `POST /api/generate`

Genera ASCII art a partir de texto.

**Request**:
```json
{
  "prompt": "lighthouse in fog",
  "width": 80,
  "charset": "dark",
  "style": "lovecraftian",
  "enhance": false
}
```

**Response**:
```json
{
  "success": true,
  "ascii_art": "@%#*+=-:. \n...",
  "image_base64": "data:image/png;base64,...",
  "metadata": {
    "width": 80,
    "height": 45,
    "charset": "dark",
    "style": "lovecraftian"
  }
}
```

### `GET /api/charsets`

Lista los charsets disponibles.

```json
{
  "charsets": ["dark", "detailed", "blocks", "standard", "artistic"],
  "samples": {...}
}
```

### `GET /api/styles`

Lista los estilos disponibles.

```json
{
  "styles": ["lovecraftian", "standard"]
}
```

### `GET /api/health`

Health check.

```json
{
  "status": "ok",
  "service": "ascii-art-generator"
}
```

## Estructura de archivos

```
ascii_generator/
├── .env                     ← Configuración (HF_TOKEN, puerto)
├── .gitignore               ← .env no versionado
├── README.md                ← Este archivo
├── server.py                ← Flask backend (puerto 5001)
├── image_gen.py             ← Cliente HuggingFace Inference API
├── ascii_render.py          ← Conversión imagen → ASCII
├── templates/
│   └── index.html           ← Sirve React app
└── client/                  ← React app (puerto 5173)
    ├── package.json
    ├── vite.config.js       ← Proxy a Flask 5001
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx          ← Componente principal
        ├── App.css
        └── index.css
```

## Desarrollo

### Hot reload (HMR)

Cambios en `App.jsx` o `App.css` se actualizan automáticamente en el navegador sin reconstruir.

```bash
# Modifica App.jsx
# → El navegador actualiza automáticamente
```

### Build para producción

```bash
cd ascii_generator/client
npm run build
# → Genera archivos optimizados en ../dist/
```

## Troubleshooting

### Error: "HF_TOKEN environment variable not set"

Asegúrate de que `.env` está en `ascii_generator/.env` y tiene un token válido.

### Error: "Model loading" (503)

HuggingFace está cargando el modelo. Espera y reintentar.

### Error: "CORS" en navegador

Verifica que el proxy en `vite.config.js` está configurado:
```js
proxy: {
  '/api': {
    target: 'http://localhost:5001',
    changeOrigin: true,
  }
}
```

### Lentitud en generación

La generación de imagen toma 30-60 segundos en HuggingFace (es una API gratuita).

Para acelerar, considera:
- Usar Replicate.com (pago pero más rápido)
- Ejecutar Stable Diffusion localmente (requiere GPU)

## Notas

- El token de HF no está commitido (`.env` en `.gitignore`)
- Los charsets se pueden extender fácilmente en `ascii_render.py`
- El frontend está completamente desacoplado del backend (CORS activo)
- React hot reload funciona sin necesidad de refresh manual

## Próximos pasos

- Integrar en `app.py` (servidor principal del juego)
- Mostrar ASCII art en momentos clave del juego
- Cachear imágenes generadas para reutilizar
- Agregar más estilos y charsets
