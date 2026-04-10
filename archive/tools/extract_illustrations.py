#!/usr/bin/env python3
"""
EXTRACTOR DE ILUSTRACIONES Y MAPAS
Organiza los archivos PNG por tipo de contenido
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

# Mapeo de páginas a tipos de contenido (basado en análisis del PDF)
PAGE_CLASSIFICATION = {
    # HANDOUTS / CHARACTER SHEETS (pages 91-100)
    (91, 100): 'handouts',

    # MAPS (identified by keyword searches)
    # Entry 43 map (page around entry content)
    (35, 37): 'maps',  # City of Old Ones map area
    (45, 50): 'maps',  # Egyptian pyramid maps
    (84, 86): 'maps',  # Eight-way intersection map

    # FRONT MATTER
    (1, 10): 'frontmatter',

    # REGULAR ADVENTURE ENTRIES (rest)
    (11, 90): 'adventure'
}

class IllustrationExtractor:
    """Extrae y organiza ilustraciones del PDF"""

    def __init__(self, pdf_pages_dir: str = 'pdf_pages'):
        self.pdf_pages_dir = Path(pdf_pages_dir)
        self.output_dirs = {
            'adventure': Path('illustrations/adventure'),
            'maps': Path('illustrations/maps'),
            'handouts': Path('illustrations/handouts'),
            'frontmatter': Path('illustrations/frontmatter')
        }

        # Crear directorios de salida
        for dir_path in self.output_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

    def classify_page(self, page_num: int) -> str:
        """Clasifica una página según su contenido"""
        for (start, end), category in PAGE_CLASSIFICATION.items():
            if start <= page_num <= end:
                return category
        return 'adventure'

    def get_all_pages(self) -> List[int]:
        """Obtiene todas las páginas disponibles"""
        pages = []
        for page_file in sorted(self.pdf_pages_dir.glob('page-*.png')):
            # Extraer número de página: page-001.png -> 1
            page_num = int(page_file.stem.split('-')[1])
            pages.append(page_num)
        return sorted(pages)

    def copy_pages(self, verbose: bool = True):
        """Copia las páginas a sus directorios correspondientes"""
        all_pages = self.get_all_pages()

        if verbose:
            print(f"\n{'='*80}")
            print("EXTRACCIÓN Y ORGANIZACIÓN DE ILUSTRACIONES")
            print(f"{'='*80}\n")
            print(f"Total de páginas: {len(all_pages)}\n")

        category_counts = {
            'adventure': 0,
            'maps': 0,
            'handouts': 0,
            'frontmatter': 0
        }

        for page_num in all_pages:
            category = self.classify_page(page_num)
            category_counts[category] += 1

            # Archivo fuente
            src_file = self.pdf_pages_dir / f'page-{page_num:03d}.png'

            # Archivo destino
            dest_dir = self.output_dirs[category]
            dest_file = dest_dir / f'{category}-page-{page_num:03d}.png'

            # Copiar
            if src_file.exists():
                shutil.copy2(src_file, dest_file)

                if verbose and page_num <= 5:  # Show first few for verification
                    print(f"✓ Page {page_num:3d} → {category}/{dest_file.name}")

        if verbose:
            print("\n" + "="*80)
            print("RESUMEN")
            print("="*80 + "\n")

            for category, count in category_counts.items():
                print(f"  {category:12s}: {count:3d} páginas → {self.output_dirs[category]}")

            print(f"\n  Total: {sum(category_counts.values())} páginas organizadas")

    def create_index(self, verbose: bool = True):
        """Crea un índice JSON de las ilustraciones"""
        index = {
            'created': str(Path.cwd()),
            'total_pages': len(self.get_all_pages()),
            'categories': {}
        }

        for category, dir_path in self.output_dirs.items():
            files = sorted(dir_path.glob('*.png'))
            index['categories'][category] = {
                'count': len(files),
                'files': [f.name for f in files],
                'path': str(dir_path)
            }

        # Guardar índice
        index_file = Path('illustrations/index.json')
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)

        if verbose:
            print(f"\n✓ Índice creado: {index_file}\n")

        return index

    def generate_report(self):
        """Genera un reporte HTML de las ilustraciones"""
        index_file = Path('illustrations/index.json')

        if not index_file.exists():
            self.create_index(verbose=False)

        with open(index_file, 'r') as f:
            index = json.load(f)

        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Alone Against the Dark - Illustrations</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; border-bottom: 2px solid #666; padding-bottom: 10px; }}
        .category {{ margin: 20px 0; padding: 15px; background: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .category h2 {{ color: #555; margin-top: 0; }}
        .category-info {{ color: #666; margin: 10px 0; }}
        .file-list {{ columns: 3; gap: 20px; }}
        .file-item {{ break-inside: avoid; color: #333; font-size: 12px; }}
        .stats {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
        .stat-item {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <h1>Alone Against the Dark - Illustrations & Maps</h1>
    <div class="stats">
        <div class="stat-item"><strong>Total Pages:</strong> {total}</div>
        <div class="stat-item"><strong>Generated:</strong> {timestamp}</div>
    </div>
""".format(
            total=index['total_pages'],
            timestamp=__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        for category, info in index['categories'].items():
            html += f"""
    <div class="category">
        <h2>{category.upper()}</h2>
        <div class="category-info">
            <strong>Pages:</strong> {info['count']} |
            <strong>Location:</strong> {info['path']}
        </div>
        <div class="file-list">
"""

            for filename in info['files']:
                html += f'            <div class="file-item">→ {filename}</div>\n'

            html += """        </div>
    </div>
"""

        html += "\n</body>\n</html>"

        # Guardar HTML
        report_file = Path('illustrations/index.html')
        with open(report_file, 'w') as f:
            f.write(html)

        return report_file


def main():
    extractor = IllustrationExtractor()

    # Extraer y organizar
    extractor.copy_pages(verbose=True)

    # Crear índice
    index = extractor.create_index(verbose=True)

    # Generar reporte HTML
    report_file = extractor.generate_report()
    print(f"✓ Reporte HTML creado: {report_file}\n")

    print("✅ PROCESO COMPLETADO")
    print(f"\nArchivos organizados en: ./illustrations/")
    print(f"  - adventure/   : Páginas con entradas de aventura")
    print(f"  - maps/        : Mapas y diagramas")
    print(f"  - handouts/    : Hojas de investigadores y referencias")
    print(f"  - frontmatter/ : Portada e introducción")
    print(f"\nÍndice: ./illustrations/index.json")
    print(f"Reporte: ./illustrations/index.html\n")


if __name__ == '__main__':
    main()
