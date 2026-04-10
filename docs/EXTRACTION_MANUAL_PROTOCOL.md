# Protocolo de Extracción Manual - Entradas Faltantes

## Status Actual
- **Entradas extraídas**: 527/594
- **Entradas faltantes**: 67
- **Problema**: Formato multi-columna del PDF hace que pdftotext falle

## Entradas Faltantes (67 total)

```
[111, 112, 126, 127, 137, 138, 154, 155, 170, 171, 181, 182, 201, 202, 203, 
213, 214, 215, 232, 233, 234, 248, 249, 264, 265, 284, 285, 286, 302, 303, 
321, 322, 339, 356, 357, 358, 374, 375, 388, 389, 390, 406, 407, 408, 425, 
444, 445, 446, 459, 460, 480, 489, 490, 507, 509, 510, 525, 549, 550, 551, 
565, 571, 572, 586, 587, 588, 589]
```

## Soluciones Disponibles

### Opción 1: Extracción Manual por el Usuario (5-10 minutos)
El usuario abre el PDF y copia el contenido de cada entrada faltante.

```json
{
  "number": 111,
  "text": "[copiar texto aquí]",
  "choices": [],
  "trace_numbers": [],
  "entry_type": "adventure"
}
```

### Opción 2: OCR Automatizado (30-60 minutos)
Ejecutar:
```bash
python3 extract_missing_smart.py
```

**Requisitos**:
- tesseract (OCR) - ✓ Disponible
- pdftoppm (PDF → PNG) - ✓ Disponible

**Proceso**:
1. Para cada entrada faltante N:
   - Determinar páginas entre Entry N-1 y N+1
   - Extraer página como imagen PNG
   - OCR con tesseract
   - Parsear contenido
   - Insertar en JSON

### Opción 3: Usar Herramienta Online
Copiar-pegar PDF en herramienta OCR online (menos recomendado por privacidad)

## Recomendación
**Opción 1 + Motor Universal**:
1. Las 527 entradas extraídas SON jugables
2. Motor universal funciona sin las 67 faltantes (genera placeholders)
3. Extraer manualmente solo si se necesitan para campaña completa

**O**: Ejecutar Opción 2 (automatizado) si queremos las 594

## Próximos Pasos
1. ¿Deseas ejecutar el OCR automático? (30-60 min)
2. ¿Extraes manualmente las 67? (2-5 min por entrada)
3. ¿Continuamos con 527 y agregamos después?

