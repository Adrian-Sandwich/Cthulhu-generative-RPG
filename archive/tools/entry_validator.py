#!/usr/bin/env python3
"""
VALIDADOR DE ENTRIES CON LLM

Usa Claude para validar que cada entrada extraída del JSON
coincide correctamente con el contenido del PDF.

Procesa 243 entradas, identifica discrepancias y proporciona
correcciones automáticas.
"""

import json
import subprocess
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import anthropic

# Inicializar cliente de Claude
client = anthropic.Anthropic()


@dataclass
class ValidationResult:
    """Resultado de validación de una entrada"""
    entry_num: int
    status: str  # "VALID", "MISMATCH", "MISSING", "EXTRA"
    json_content: str
    pdf_content: str
    confidence: float
    message: str
    suggested_fix: Optional[str] = None


class EntryValidator:
    """Validador de entries usando LLM"""

    def __init__(self, json_file: str, pdf_file: str):
        """Inicializa el validador con JSON y PDF"""
        # Cargar JSON
        with open(json_file, 'r') as f:
            self.json_entries = json.load(f)

        # Extraer PDF
        result = subprocess.run(
            ['pdftotext', pdf_file, '-'],
            capture_output=True,
            text=True
        )
        self.pdf_lines = result.stdout.split('\n')
        self.pdf_text = result.stdout

        # Crear mapa de entries en JSON
        self.json_map = {e['number']: e for e in self.json_entries}

        # Extraer entries del PDF
        self.pdf_entries = self._extract_pdf_entries()

        print(f"✓ Validador inicializado")
        print(f"  JSON entries: {len(self.json_entries)}")
        print(f"  PDF entries extraídas: {len(self.pdf_entries)}")

    def _extract_pdf_entries(self) -> Dict[int, str]:
        """Extrae todas las entries del PDF"""
        entries = {}

        for i, line in enumerate(self.pdf_lines):
            stripped = line.strip()

            # Patrón 1: Número solo
            if re.match(r'^\d{1,3}$', stripped):
                num = int(stripped)
                if 1 <= num <= 243:
                    # Validar que es entrada real (no trace number)
                    prev = self.pdf_lines[i - 1].strip() if i > 0 else ""
                    if not prev or prev.endswith(')'):
                        # Extraer contenido siguiente
                        content = self._extract_content_from_pdf(i)
                        if content:
                            entries[num] = content

            # Patrón 2: "B NÚMERO"
            elif re.match(r'^\s*B\s+(\d{1,3})\s*$', stripped):
                match = re.match(r'B\s+(\d{1,3})', stripped)
                if match:
                    num = int(match.group(1))
                    if 1 <= num <= 243:
                        content = self._extract_content_from_pdf(i)
                        if content:
                            entries[num] = content

        return entries

    def _extract_content_from_pdf(self, start_line: int) -> Optional[str]:
        """Extrae contenido de una entrada a partir de una línea"""
        content_lines = []
        i = start_line + 1

        while i < len(self.pdf_lines):
            line = self.pdf_lines[i].rstrip()
            stripped = line.strip()

            # Detectar siguiente entrada
            if re.match(r'^\d{1,3}$', stripped) or re.match(r'B\s+\d{1,3}', stripped):
                break

            # Ignorar headers
            if 'ALONE AGAINST' in line or (stripped and all(c in 'BOKRUG ' for c in stripped)):
                i += 1
                continue

            if stripped:
                content_lines.append(stripped)

            i += 1

        # Unir y normalizar
        content = ' '.join(content_lines)
        content = re.sub(r'\s+', ' ', content).strip()

        return content if len(content) > 20 else None

    def validate_entry(self, entry_num: int) -> ValidationResult:
        """Valida una entrada específica usando LLM"""
        json_entry = self.json_map.get(entry_num)
        pdf_content = self.pdf_entries.get(entry_num)

        # Caso 1: No está en PDF pero sí en JSON
        if not pdf_content and json_entry:
            return ValidationResult(
                entry_num=entry_num,
                status="EXTRA",
                json_content=json_entry['text'][:100],
                pdf_content="[NOT FOUND IN PDF]",
                confidence=1.0,
                message="Entrada en JSON pero no en PDF"
            )

        # Caso 2: Está en PDF pero no en JSON
        if pdf_content and not json_entry:
            return ValidationResult(
                entry_num=entry_num,
                status="MISSING",
                json_content="[NOT IN JSON]",
                pdf_content=pdf_content[:100],
                confidence=1.0,
                message="Entrada en PDF pero no en JSON",
                suggested_fix=pdf_content
            )

        # Caso 3: Ambos existen - validar con LLM
        if json_entry and pdf_content:
            return self._validate_with_llm(entry_num, json_entry['text'], pdf_content)

        # Caso 4: Ninguno existe
        return ValidationResult(
            entry_num=entry_num,
            status="VALID",
            json_content="[EMPTY]",
            pdf_content="[EMPTY]",
            confidence=1.0,
            message="Entrada vacía (esperado)"
        )

    def _validate_with_llm(self, entry_num: int, json_content: str, pdf_content: str) -> ValidationResult:
        """Usa Claude para validar si los contenidos coinciden"""

        prompt = f"""Analiza si estos dos textos son el MISMO contenido de la Entrada {entry_num}:

CONTENIDO EN JSON (lo que extrajimos):
"{json_content[:300]}"

CONTENIDO EN PDF (lo que DEBERÍA estar):
"{pdf_content[:300]}"

Responde EXACTAMENTE en este formato (sin nada más):

[DECISION]: MATCH o MISMATCH
[CONFIDENCE]: número 0-100
[REASON]: explicación breve

Si es MISMATCH, también incluye:
[CORRECT_CONTENT]: el contenido correcto (breve)
"""

        try:
            message = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=200,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text

            # Parsear respuesta
            lines = response_text.strip().split('\n')
            decision = "MATCH"
            confidence = 50
            reason = "Error parsing LLM response"
            correct_content = None

            for line in lines:
                if '[DECISION]' in line:
                    decision = "MISMATCH" if "MISMATCH" in line else "MATCH"
                elif '[CONFIDENCE]' in line:
                    try:
                        confidence = int(re.search(r'\d+', line).group())
                    except:
                        pass
                elif '[REASON]' in line:
                    reason = line.split(':', 1)[1].strip() if ':' in line else line
                elif '[CORRECT_CONTENT]' in line:
                    correct_content = line.split(':', 1)[1].strip() if ':' in line else None

            status = "VALID" if decision == "MATCH" else "MISMATCH"

            return ValidationResult(
                entry_num=entry_num,
                status=status,
                json_content=json_content[:100],
                pdf_content=pdf_content[:100],
                confidence=confidence / 100.0,
                message=reason,
                suggested_fix=correct_content if status == "MISMATCH" else None
            )

        except Exception as e:
            return ValidationResult(
                entry_num=entry_num,
                status="ERROR",
                json_content=json_content[:100],
                pdf_content=pdf_content[:100],
                confidence=0.0,
                message=f"Error en LLM: {str(e)}"
            )

    def validate_all(self) -> Tuple[List[ValidationResult], Dict]:
        """Valida todas las entradas"""
        results = []
        stats = {
            'total': 243,
            'valid': 0,
            'mismatch': 0,
            'missing': 0,
            'extra': 0,
            'error': 0,
            'high_confidence': 0,
        }

        print("\n🔍 VALIDANDO TODAS LAS ENTRIES...")
        print("="*80)

        for entry_num in range(1, 244):
            if entry_num % 50 == 0:
                print(f"Progress: {entry_num}/243...")

            result = self.validate_entry(entry_num)
            results.append(result)

            # Actualizar stats
            if result.status == "VALID":
                stats['valid'] += 1
            elif result.status == "MISMATCH":
                stats['mismatch'] += 1
            elif result.status == "MISSING":
                stats['missing'] += 1
            elif result.status == "EXTRA":
                stats['extra'] += 1
            else:
                stats['error'] += 1

            if result.confidence >= 0.8:
                stats['high_confidence'] += 1

        return results, stats

    def print_report(self, results: List[ValidationResult], stats: Dict):
        """Genera reporte de validación"""
        print("\n" + "="*80)
        print("REPORTE DE VALIDACIÓN")
        print("="*80)

        print(f"\n📊 ESTADÍSTICAS:")
        print(f"  Total de entradas: {stats['total']}")
        print(f"  Válidas: {stats['valid']}")
        print(f"  Discrepancias: {stats['mismatch']}")
        print(f"  Faltantes en JSON: {stats['missing']}")
        print(f"  Extras en JSON: {stats['extra']}")
        print(f"  Errores de validación: {stats['error']}")
        print(f"  Alta confianza (>80%): {stats['high_confidence']}")

        # Mostrar problemas
        problems = [r for r in results if r.status != "VALID"]

        if problems:
            print(f"\n⚠️ PROBLEMAS ENCONTRADOS ({len(problems)}):")
            print("-"*80)

            for result in problems[:20]:  # Mostrar primeros 20
                print(f"\nEntry {result.entry_num}: {result.status}")
                print(f"  Mensaje: {result.message}")
                if result.suggested_fix:
                    print(f"  Sugerencia: {result.suggested_fix[:80]}...")

            if len(problems) > 20:
                print(f"\n... y {len(problems) - 20} problemas más")
        else:
            print("\n✅ NO HAY PROBLEMAS DETECTADOS")

    def generate_corrections_file(self, results: List[ValidationResult]):
        """Genera archivo con correcciones sugeridas"""
        corrections = []

        for result in results:
            if result.status == "MISMATCH" and result.suggested_fix:
                corrections.append({
                    'entry': result.entry_num,
                    'current': result.json_content,
                    'suggested': result.suggested_fix,
                    'confidence': result.confidence,
                    'reason': result.message
                })
            elif result.status == "MISSING":
                corrections.append({
                    'entry': result.entry_num,
                    'action': 'ADD_FROM_PDF',
                    'content': result.pdf_content,
                    'reason': result.message
                })

        with open('corrections.json', 'w') as f:
            json.dump(corrections, f, indent=2)

        print(f"\n✓ Correcciones guardadas en corrections.json ({len(corrections)} items)")


if __name__ == '__main__':
    print("🔐 VALIDADOR DE ENTRIES CON LLM")
    print("="*80)

    # Crear validador
    validator = EntryValidator(
        'entries_with_rolls.json',
        '/Users/adrianmedina/src/Cthulhu/toaz.info-alone-against-the-tide-pr_33b3d17a9830aef5793eb045adc40271.pdf'
    )

    # Validar todas las entradas
    results, stats = validator.validate_all()

    # Generar reporte
    validator.print_report(results, stats)

    # Guardar correcciones
    validator.generate_corrections_file(results)

    print("\n✅ Validación completada")
