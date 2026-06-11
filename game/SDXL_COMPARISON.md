# SDXL vs SD v1.5: ¿Vale la pena?

## Problema Actual

**Lighthouse Exterior (SD v1.5):**
- ✓ Buena composición
- ✓ Claro horror atmosphere
- ✗ **Demasiado realista (no es pixel art)**
- ✗ Fotográfico, no retro

**Esperado:**
- Pixel art retro style
- 8-bit/16-bit aesthetic
- Colorful palette
- Game-like appearance

---

## Comparación Técnica

| Aspecto | SD v1.5 | SDXL |
|---------|---------|------|
| **Tamaño modelo** | 4 GB | 6-7 GB |
| **VRAM necesario** | 4-6 GB | 8-12 GB |
| **Tiempo generación** | 30-35s | 60-90s |
| **Calidad** | 7/10 | 9/10 |
| **Style compliance** | Media | Excelente |
| **Prompt following** | 70% | 95% |
| **Pixel art skills** | Débil | Buena |

---

## Prueba: Mismo Prompt en Ambos Modelos

### Prompt:
```
Pixel art retro horror. Lighthouse on rocky coast. First-person view.
```

### SD v1.5 Resultado:
- Realista (no pixel art)
- Fotográfico
- Entiende "horror" pero no "pixel art"

### SDXL Resultado (esperado):
- Pixel art recognizable
- Retro aesthetic
- Entiende AMBOS: horror Y pixel art
- Mejor color palette control

---

## Cuándo Cambiar a SDXL

### ✓ Vale la pena SI:
- Necesitas pixel art puro (sí, tu caso)
- Tienes 10+ GB VRAM disponible
- Puedes esperar 2-3x más lento
- Quieres mejorar calidad permanentemente

### ✗ NO vale la pena SI:
- El realismo te da igual
- Quieres generar rápido
- VRAM limitada en M1
- Timeline muy corto

---

## Riesgo SDXL en M1

**Potencial problema:** M1 con float32 + SDXL = 10-12 GB VRAM  
**M1 RAM típica:** 8-16 GB  

**Si tienes 16 GB:** ✓ Probablemente funcione  
**Si tienes 8 GB:** ⚠ Risky, puede out-of-memory  

Workaround: `enable_attention_slicing()` + `enable_sequential_cpu_offload()`

---

## Mi Recomendación

### Opción 1: Stick with SD v1.5 + Accept Reality
- Lighthouse_exterior es realista pero still usable
- Rápido (30s)
- Integra YA

### Opción 2: Try SDXL First, Decide Later
- Test si cabe en tu M1
- Si funciona → mejor results
- Si no → volvemos a SD v1.5

### Opción 3: Hybrid
- SD v1.5 para lugares "realistas" (lighthouse, ruins)
- SDXL solo para lugares "artísticos" (caverns, void)

---

## Tiempo Estimado

- **SD v1.5 → Ship:** 4-6 horas
- **Try SDXL test:** 5-10 minutos
- **SDXL → Ship:** 6-8 horas (si funciona)
- **SDXL → Fallback a SD v1.5:** +2 horas

---

## Mi Voto

**Test SDXL ahora (5 min), decide después.**

Si funciona y te gusta: Use SDXL  
Si no funciona: Volvemos a SD v1.5 sin pérdida

No es decisión binaria - es investigación rápida.
