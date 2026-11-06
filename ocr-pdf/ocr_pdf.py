import ocrmypdf
import sys
import os
from pathlib import Path

def processar_ocr(caminho_input):
    # 1. Validar se o arquivo existe
    path_original = Path(caminho_input).resolve()
    
    if not path_original.exists():
        print(f"❌ Erro: O arquivo '{caminho_input}' não foi encontrado.")
        return

    # 2. Criar o nome do arquivo de saída
    diretorio = path_original.parent
    nome_saida = f"{path_original.stem}_pesquisavel{path_original.suffix}"
    caminho_saida = diretorio / nome_saida

    print(f"🚀 Iniciando OCR: {path_original.name}")
    print(f"📂 Destino: {caminho_saida}")

    try:
        # Executa o motor de OCR
        # language="por" -> idioma do texto (português); use "por+eng" para os dois
        # deskew=True -> Corrige inclinação de fotos/scans
        ocrmypdf.ocr(
            path_original, 
            caminho_saida, 
            language="por", 
            optimize=1,
            redo_ocr=True  # Substitui a camada de texto existente pela nova
            # Removemos o deskew=True para evitar o erro de validação
        )
        print(f"✅ Concluído com sucesso!")
        
    except Exception as e:
        print(f"⚠️ Ocorreu um erro: {e}")

if __name__ == "__main__":
    # Verifica se você enviou o caminho pelo terminal
    # Exemplo: python ocr_pdf.py "meu_documento.pdf"
    if len(sys.argv) > 1:
        arquivo_alvo = sys.argv[1]
    else:
        # Se não enviou, pergunta no terminal
        arquivo_alvo = input("Digite ou cole o caminho completo do PDF: ").strip('"')

    processar_ocr(arquivo_alvo)