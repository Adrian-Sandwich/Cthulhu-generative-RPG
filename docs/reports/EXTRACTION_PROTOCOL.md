# Protocolo de Extracción de Libros de Aventura Solitaria

## Objetivo
Extraer y validar entrada por entrada de libros PDF en formato de "aventura solitaria numerada" de manera genérica y reutilizable para cualquier libro con este formato.

## Formato de Libro Soportado

### Características del PDF
- Entradas numeradas secuencialmente (1, 2, 3, ... N)
- Cada entrada contiene:
  - **Número de entrada**: Línea con solo el número (ej: `1`)
  - **Nombre de personaje** (opcional): Línea con nombre propio
  - **Contenido narrativo**: El texto de la aventura
  - **Choices**: Líneas que comienzan con `•`, indicando opciones (ej: `• Go to 45.`)
  - **Trace numbers**: Números entre paréntesis al final (ej: `(34, 56, 78)`)

### Variantes Detectadas
El protocolo detecta dos formatos de entrada:
1. **Formato estándar**: Número en línea sola
   ```
   1
   
   The sun sinks low...
   • Go to 12.
   (Beginning)
   ```

2. **Formato con prefijo**: `B NÚMERO` (variante en algunos libros)
   ```
   B 93
   
   You feel that the information...
   • Go to 101.
   (7, 110)
   ```

## Protocolo de Extracción

### Paso 1: Localización de Entradas
```
Para cada línea del PDF:
  SI línea coincide con "^\\s*(\\d{1,3})\\s*$"
     O línea coincide con "^\\s*B\\s+(\\d{1,3})\\s*$"
    ENTONCES registrar ubicación de esa entrada
```

### Paso 2: Extracción de Contenido
Para cada entrada encontrada:
```
1. Inicio = línea del número + 1
2. Fin = línea de siguiente número o EOF
3. Para cada línea entre Inicio y Fin:
   - Ignorar líneas header ("ALONE AGAINST THE TIDE", etc.)
   - Ignorar líneas que son solo BOKRUG
   - Líneas con "•" → agregar a CHOICES
   - Líneas con "(dígitos)" → agregar a TRACE_NUMBERS
   - Línea corta sin puntuación → potencial NOMBRE_PERSONAJE
   - Resto → agregar a CONTENIDO
4. Unificar líneas de contenido
5. Normalizar espacios: múltiples espacios → un espacio
```

### Paso 3: Clasificación de Tipo
```
SI texto está vacío O < 5 caracteres:
  TIPO = "empty" (pseudo-entrada)
SINO SI tiene CHOICES o TRACE_NUMBERS válidos:
  TIPO = "adventure" (entrada de aventura real)
SINO SI contiene palabras clave de instrucción:
  TIPO = "instruction" (sección de instrucciones del juego)
SINO SI texto < 20 caracteres:
  TIPO = "empty" (pseudo-entrada)
SINO:
  TIPO = "adventure" (aventura sin choices explícitos)
```

### Paso 4: Validación
Para cada entrada extraída:
- ✓ Verificar que tenga contenido (> 10 caracteres)
- ✓ Verificar que tenga choices O trace numbers (si no es "instruction")
- ✓ Comparar contra PDF original línea por línea

## Resultados esperados

### Para "Alone Against the Tide" (243 entradas)
```
Total de entradas extraídas: 243
Entradas de aventura: 234
Pseudo-entradas: 9
  - 7 entradas vacías (portada, copyright, etc.)
  - 2 entradas de instrucciones del juego

Caracteres totales: ~567,000
Promedio por entrada: ~2,332 caracteres
Rango: 0 - 6,655 caracteres
```

## Estructura de Datos de Salida

```json
{
  "number": 1,
  "text": "The sun sinks low on the horizon...",
  "choices": [
    "• Go to 12."
  ],
  "trace_numbers": [],
  "character_name": null,
  "is_adventure_entry": true,
  "entry_type": "adventure"
}
```

## Validación Cruzada

El protocolo valida cada entrada:
1. **Extrae de PDF** → Obtiene entrada número N
2. **Extrae contenido** → Reúne todo entre N y N+1
3. **Limpia formato** → Normaliza espacios y saltos de línea
4. **Compara contra Original** → Verifica que coincida con PDF

Esto asegura que:
- No se pierdan líneas de texto
- Las choices estén completas
- Los trace numbers sean correctos

## Uso del Protocolo

### Instalación
```bash
# No requiere dependencias especiales, solo:
# - Python 3.6+
# - pdftotext (incluido en poppler-utils)

pip install poppler-utils  # Si no está instalado
```

### Ejecución
```bash
# Extracción y validación básica
python3 pdf_extraction_protocol.py libro.pdf 243 --validate

# Extracción con output personalizado
python3 pdf_extraction_protocol.py libro.pdf 250 --output my_entries.json

# Solo extracción sin validación
python3 pdf_extraction_protocol.py libro.pdf 243
```

### Para Otros Libros

El protocolo es genérico. Para usarlo en otro libro:

1. **Determinar número de entradas**: Buscar la última entrada en el PDF
2. **Ejecutar extractor**: 
   ```bash
   python3 pdf_extraction_protocol.py "nuevo_libro.pdf" NÚMERO_ENTRADAS --validate
   ```
3. **Revisar pseudo-entradas**: Las entradas de tipo "empty" o "instruction" pueden requerir revisión manual

## Problemas Comunes y Soluciones

### Problema: "Entradas faltantes"
**Causa**: El formato del PDF difiere (ej: "B NÚMERO" en lugar de solo número)
**Solución**: El protocolo detecta ambos patrones automáticamente

### Problema: "Choices incompletas"
**Causa**: Las choices están divididas en múltiples líneas
**Solución**: El protocolo cada línea con "•" y las agrupa como una sola choice

### Problema: "Trace numbers no extraídos"
**Causa**: Regex no coincide con formato específico
**Solución**: Actualizar regex en `_extract_entry_from_pdf()` según el formato

### Problema: "Pseudo-entradas incorrectas"
**Causa**: Palabras clave de instrucción demasiado agresivas
**Solución**: Ajustar palabras clave en `validate_entry()`

## Extensiones Futuras

El protocolo puede extenderse para:
- [ ] Extraer mapas de dependencias entre entradas
- [ ] Detectar bucles y ramas muertas
- [ ] Generar visualización de árbol de aventura
- [ ] Validar integridad de references (¿todos los "go to X" tienen entrada X?)
- [ ] Detectar entradas inalcanzables
- [ ] Estadísticas de flujo narrativo

## Archivos Generados

- `entries_protocol.json` - Todas las entradas extraídas y clasificadas
- Reporte de validación en stdout

## Licencia
Este protocolo es genérico y reutilizable para cualquier libro con este formato.
