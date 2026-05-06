# Setup - ASCII Art Generator

## ✅ Instalación completada

Python dependencies:
✓ requests
✓ python-dotenv  
✓ flask
✓ flask-cors

Node dependencies:
✓ react
✓ react-dom
✓ vite
✓ @vitejs/plugin-react

---

## 🚀 Cómo correr (cada vez)

### Terminal 1: Backend Flask (PRIMERO)

```bash
cd /Users/adrianmedina/src/Cthulhu/ascii_generator
source venv/bin/activate
python server.py
```

**Espera hasta ver**:
```
🎨 ASCII Art Generator Server
📍 Port: 5001
🔗 http://localhost:5001
🔄 Debug: True
```

---

### Terminal 2: Frontend React (SEGUNDO)

```bash
cd /Users/adrianmedina/src/Cthulhu/ascii_generator/client
npm run dev
```

**Espera hasta ver**:
```
VITE v4.3.0  ready in XXX ms
➜  Local:   http://localhost:5173/
```

---

## 🌐 Abre en el navegador

```
http://localhost:5173
```

---

## 🎯 Prueba rápida

1. Escribe en la textarea: `"A dark lighthouse on a rocky coast with fog"`
2. Haz clic en `✨ Generar ASCII Art`
3. Espera 30-60 segundos
4. Verás la imagen + ASCII art

---

## 🔄 Hot Reload

Modifica `ascii_generator/client/src/App.jsx` o `App.css`:
→ El navegador se actualiza automáticamente sin refresh

---

## 📝 Notas

- El venv está en `ascii_generator/venv/`
- Siempre ejecuta `source venv/bin/activate` antes de correr server.py
- Los cambios en React son instantáneos (HMR)
- La generación de imagen toma tiempo (es gratis desde HF)

---

## ⚡ Alias corto (opcional)

Puedes crear alias en tu ~/.zshrc:

```bash
alias ascii-backend='cd ~/src/Cthulhu/ascii_generator && source venv/bin/activate && python server.py'
alias ascii-frontend='cd ~/src/Cthulhu/ascii_generator/client && npm run dev'
```

Luego simplemente:
```bash
ascii-backend   # Terminal 1
ascii-frontend  # Terminal 2
```

---

**¡Listo para usar! 🎨**
