# -*- coding: utf-8 -*-
"""
Transforma um PDF escaneado (só imagem) em PDF pesquisável.

Uso:
    python ocr_pdf.py "documento.pdf"            # português
    python ocr_pdf.py "documento.pdf" por+eng    # português e inglês

Gera "documento_pesquisavel.pdf" na mesma pasta.
"""
import subprocess
import sys
from pathlib import Path

# Evita erro com emojis em consoles que não usam UTF-8 (cmd antigo, saída redirecionada)
for fluxo in (sys.stdout, sys.stderr):
    try:
        fluxo.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

IDIOMA_PADRAO = 'por'

# Códigos de saída do OCRmyPDF que valem uma explicação amigável
ERROS_CONHECIDOS = {
    1: 'argumentos inválidos.',
    2: 'o arquivo de entrada não é um PDF válido.',
    3: 'falta um programa necessário (Tesseract ou Ghostscript) ou o idioma não está instalado.',
    4: 'o PDF de saída ficou inválido.',
    5: 'sem permissão para gravar o arquivo de saída (ele está aberto em outro programa?).',
    8: 'o PDF está protegido por senha.',
    10: 'o PDF é assinado digitalmente ou tem formulário, e o OCR invalidaria isso.',
    15: 'erro interno do OCRmyPDF.',
}


def processar_ocr(caminho_input, idioma=IDIOMA_PADRAO):
    """Roda o OCR e devolve True se deu certo."""
    path_original = Path(caminho_input).expanduser().resolve()

    if not path_original.is_file():
        print(f"❌ Erro: o arquivo '{caminho_input}' não foi encontrado.")
        return False
    if path_original.suffix.lower() != '.pdf':
        print(f"❌ Erro: '{path_original.name}' não é um PDF.")
        return False

    caminho_saida = path_original.with_name(f"{path_original.stem}_pesquisavel.pdf")

    print(f"🚀 Iniciando OCR: {path_original.name} (idioma: {idioma})")
    print(f"📂 Destino: {caminho_saida}")

    # O OCRmyPDF roda pela linha de comando (python -m ocrmypdf) de propósito:
    # na versão 17, a chamada ocrmypdf.ocr() perde as opções e gera o PDF
    # sem a camada de texto, mesmo dizendo que deu certo.
    comando = [
        sys.executable, '-m', 'ocrmypdf',
        '--language', idioma,
        '--skip-text',     # só faz OCR nas páginas sem texto (não duplica texto digital)
        '--optimize', '1',  # compressão sem perda de qualidade
        str(path_original),
        str(caminho_saida),
    ]

    try:
        resultado = subprocess.run(comando)
    except OSError as e:
        print(f"⚠️ Não foi possível iniciar o OCRmyPDF: {e}")
        return False

    if resultado.returncode == 0:
        print("✅ Concluído com sucesso!")
        return True

    motivo = ERROS_CONHECIDOS.get(resultado.returncode, 'veja a mensagem acima.')
    print(f"⚠️ O OCR falhou (código {resultado.returncode}): {motivo}")
    return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arquivo_alvo = sys.argv[1]
    else:
        arquivo_alvo = input("Digite ou cole o caminho completo do PDF: ").strip().strip('"\'')

    idioma = sys.argv[2] if len(sys.argv) > 2 else IDIOMA_PADRAO
    sys.exit(0 if processar_ocr(arquivo_alvo, idioma) else 1)
