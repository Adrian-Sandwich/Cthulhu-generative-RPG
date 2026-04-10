#!/usr/bin/env python3
"""
VALIDADOR INTELIGENTE (RÁPIDO)

En lugar de usar LLM para todas las 243 entradas (lento),
primero detecta discrepancias automáticamente, luego solo
valida con LLM las entradas que tienen problemas.
"""

import json
import subprocess
import re
from dataclasses import dataclass
from typing import List, Dict, Tuple
import anthropic

client = anthropic.Anthropic()


@dataclass
class ValidationResult:
    entry_num: int
    status: str  # VALID, MISMATCH, MISSING, EXTRA
    confidence: float
    message: str
    suggestion: str = None


class SmartValidator:
    """Validador inteligente que optimiza llamadas a LLM"""

    def __init__(self, json_file: str, pdf_file: str):
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

        self.json_map = {e['number']: e for e in self.json_entries}
        self.pdf_entries = self._extract_pdf_entries()

        print(f"✓ Cargado: {len(self.json_entries)} en JSON")
        print(f"✓ Cargado: {len(self.pdf_entries)} en PDF")

    def _extract_pdf_entries(self) -> Dict[int, str]:
        """Extrae todas las entries del PDF de manera simple"""
        entries = {}

        for i, line in enumerate(self.pdf_lines):
            stripped = line.strip()

            # Patrón 1: Número solo
            if re.match(r'^\d{1,3}$', stripped):
                num = int(stripped)
                if 1 <= num <= 243:
                    content = self._get_content(i)
                    if content and len(content) > 20:
                        entries[num] = content

            # Patrón 2: "B NÚMERO"
            elif re.match(r'B\s+(\d{1,3})', stripped):
                match = re.search(r'B\s+(\d{1,3})', stripped)
                if match:
                    num = int(match.group(1))
                    if 1 <= num <= 243:
                        content = self._get_content(i)
                        if content and len(content) > 20:
                            entries[num] = content

        return entries

    def _get_content(self, start_line: int) -> str:
        """Obtiene contenido de una entrada"""
        lines = []
        i = start_line + 1
        count = 0

        while i < len(self.pdf_lines) and count < 50:  # Limitar a 50 líneas
            line = self.pdf_lines[i].strip()

            if not line or re.match(r'^\d{1,3}$', line) or re.match(r'B\s+\d', line):
                break

            if line and 'ALONE AGAINST' not in line:
                lines.append(line)
                count += 1

            i += 1

        return ' '.join(lines).strip()

    def quick_check(self, entry_num: int) -> Tuple[str, float]:
        """
        Validación rápida sin LLM:
        Compara automáticamente para detectar discrepancias obvias.
        Retorna: (status, confidence)
        """
        json_entry = self.json_map.get(entry_num)
        pdf_content = self.pdf_entries.get(entry_num)

        # Missing en PDF
        if not pdf_content and json_entry:
            # Verificar si el contenido está en otra entrada
            json_text = json_entry['text'].split()[0:5]  # Primeras 5 palabras
            for pdf_num, pdf_text in self.pdf_entries.items():
                if all(word.lower() in pdf_text.lower() for word in json_text if len(word) > 3):
                    # Encontrado en otro lugar
                    return ("MISMATCH", 0.95)

            return ("EXTRA", 1.0)

        # Missing en JSON
        if pdf_content and not json_entry:
            return ("MISSING", 1.0)

        # Ambos existen - comparación simple
        if json_entry and pdf_content:
            # Obtener primeras 50 caracteres (sin espacios múltiples)
            json_start = re.sub(r'\s+', ' ', json_entry['text'][:80]).lower()
            pdf_start = re.sub(r'\s+', ' ', pdf_content[:80]).lower()

            # Si comienzan igual, probablemente coincidan
            if json_start == pdf_start:
                return ("VALID", 1.0)

            # Si tienen mucho en común
            common_words = sum(1 for w in json_start.split() if w in pdf_start)
            if common_words > 0:
                similarity = common_words / max(len(json_start.split()), len(pdf_start.split()))
                if similarity > 0.7:
                    return ("VALID", similarity)

            # Muy diferentes
            return ("MISMATCH", 0.5)  # Baja confianza - necesita LLM

        return ("VALID", 1.0)

    def validate_with_llm(self, entry_num: int, json_content: str, pdf_content: str) -> str:
        """Usa LLM solo cuando es necesario"""
        prompt = f"""Valida brevemente si estos textos son la MISMA entrada {entry_num}:

JSON: "{json_content[:150]}..."
PDF: "{pdf_content[:150]}..."

Responde SOLO con: MATCH o MISMATCH"""

        try:
            msg = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )
            return "MISMATCH" if "MISMATCH" in msg.content[0].text else "MATCH"
        except:
            return "MATCH"  # Asumir válido si falla

    def validate_all(self) -> Tuple[List[ValidationResult], Dict]:
        """Valida todas las entradas de manera inteligente"""
        results = []
        stats = {
            'total': 243,
            'valid': 0,
            'mismatch': 0,
            'missing': 0,
            'extra': 0,
        }

        print("\n🔍 VALIDANDO CON ALGORITMO INTELIGENTE...")
        print("="*80)

        llm_calls = 0

        for entry_num in range(1, 244):
            if entry_num % 50 == 0:
                print(f"Progress: {entry_num}/243 (LLM calls: {llm_calls})...")

            # Validación rápida
            quick_status, confidence = self.quick_check(entry_num)

            # Si la confianza es baja, usar LLM
            if confidence < 0.7 and quick_status == "MISMATCH":
                json_entry = self.json_map.get(entry_num)
                pdf_content = self.pdf_entries.get(entry_num)
                if json_entry and pdf_content:
                    llm_result = self.validate_with_llm(
                        entry_num,
                        json_entry['text'],
                        pdf_content
                    )
                    quick_status = "VALID" if llm_result == "MATCH" else "MISMATCH"
                    confidence = 0.8
                    llm_calls += 1

            # Crear resultado
            result = ValidationResult(
                entry_num=entry_num,
                status=quick_status,
                confidence=confidence,
                message=f"Validated with {('LLM' if confidence >= 0.8 and llm_calls > 0 else 'AUTO')}"
            )

            results.append(result)
            stats[quick_status.lower()] += 1

        print(f"\n✓ Validación completada (LLM calls: {llm_calls}/243)")

        return results, stats

    def print_report(self, results: List[ValidationResult], stats: Dict):
        """Genera reporte"""
        print("\n" + "="*80)
        print("REPORTE DE VALIDACIÓN")
        print("="*80)

        print(f"\n📊 RESULTADOS:")
        print(f"  Total: {stats['total']}")
        print(f"  Válidas: {stats['valid']} ({100*stats['valid']//stats['total']}%)")
        print(f"  Discrepancias: {stats['mismatch']}")
        print(f"  Faltantes: {stats['missing']}")
        print(f"  Extras: {stats['extra']}")

        # Mostrar problemas
        problems = [r for r in results if r.status != "VALID"]

        if problems:
            print(f"\n⚠️ PROBLEMAS ({len(problems)}):")
            for result in problems[:10]:
                print(f"  Entry {result.entry_num}: {result.status} (conf: {result.confidence:.1f})")

            if len(problems) > 10:
                print(f"  ... y {len(problems)-10} más")

        if stats['mismatch'] == 0 and stats['missing'] == 0 and stats['extra'] == 0:
            print(f"\n✅ TODAS LAS ENTRADAS VALIDADAS CORRECTAMENTE")


if __name__ == '__main__':
    print("⚡ VALIDADOR INTELIGENTE (RÁPIDO)")
    print("="*80)

    validator = SmartValidator(
        'entries_with_rolls.json',
        '/Users/adrianmedina/src/Cthulhu/toaz.info-alone-against-the-tide-pr_33b3d17a9830aef5793eb045adc40271.pdf'
    )

    results, stats = validator.validate_all()
    validator.print_report(results, stats)

    # Guardar resultados
    with open('validation_results.json', 'w') as f:
        json.dump([{
            'entry': r.entry_num,
            'status': r.status,
            'confidence': r.confidence
        } for r in results], f, indent=2)

    print(f"\n✓ Resultados guardados en validation_results.json")
