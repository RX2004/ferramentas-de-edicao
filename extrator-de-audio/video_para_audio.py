# -*- coding: utf-8 -*-
from moviepy import VideoFileClip
import os

def extrair_audio(video_path, output_folder):
    """
    Extrai o áudio de um arquivo de vídeo e o salva como MP3.
    """
    try:
        # Garante que a pasta de saída existe
        os.makedirs(output_folder, exist_ok=True)
        
        # Gera o nome do arquivo de saída baseado no nome do vídeo
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_filename = f"{base_name}.mp3"
        output_audio_path = os.path.join(output_folder, output_filename)

        # Verifica se o arquivo já existe para evitar reprocessamento desnecessário
        if os.path.exists(output_audio_path):
            print(f"⚠️  Áudio já existe, pulando: {output_filename}")
            return

        print(f"🎬 Carregando vídeo: {os.path.basename(video_path)}")
        
        # Carrega o vídeo e extrai o áudio
        # Usamos o bloco 'with' ou fechamos manualmente para liberar memória
        video = VideoFileClip(video_path)
        
        if video.audio is None:
            print(f"❌ O vídeo '{os.path.basename(video_path)}' não possui faixa de áudio.")
            video.close()
            return

        print(f"🔊 Extraindo e salvando em: {output_filename}...")
        video.audio.write_audiofile(output_audio_path, logger=None) # logger=None deixa o terminal mais limpo
        
        # Fecha os arquivos para liberar memória (Crucial em loops)
        video.close()
        
        print(f"✅ Sucesso: {output_filename}")

    except Exception as e:
        print(f"❌ Erro ao processar '{os.path.basename(video_path)}': {e}")


# --- Início do script principal ---

print("--- EXTRATOR DE ÁUDIO EM LOTE (BATCH) ---")

# 1. Solicita a origem (pode ser uma pasta ou um arquivo)
origem = input("Digite o caminho da PASTA com os vídeos (ou um arquivo único): ").strip()
origem = origem.replace('"', '') # Remove aspas se o usuário copiar "Caminho"

lista_videos = []

# Verifica o que o usuário digitou
if os.path.isdir(origem):
    # É uma pasta: varrer arquivos
    extensoes_validas = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv')
    print(f"\n🔎 Buscando vídeos na pasta: {origem}")
    
    for arquivo in os.listdir(origem):
        if arquivo.lower().endswith(extensoes_validas):
            caminho_completo = os.path.join(origem, arquivo)
            lista_videos.append(caminho_completo)
            
elif os.path.isfile(origem):
    # É um arquivo único
    lista_videos.append(origem)
else:
    print("❌ Caminho inválido. Certifique-se de que a pasta ou arquivo existe.")
    exit()

if not lista_videos:
    print("❌ Nenhum vídeo encontrado na pasta informada.")
    exit()

print(f"📋 Total de vídeos encontrados: {len(lista_videos)}")


# 2. Define as opções de pasta de saída (DESTINO)
pastas_predefinidas = {
    "1": "audios",
    "2": "audios_podcast",
    "3": "audios_para_edicao"
}

print("\nEscolha a pasta de DESTINO para os áudios:")
for numero, nome_pasta in pastas_predefinidas.items():
    print(f"{numero} - {nome_pasta}")
print("4 - Digitar outro caminho de pasta")

output_folder = ""
escolha_valida = False

while not escolha_valida:
    escolha_pasta = input("Digite o número ou o caminho: ").strip()
    
    # Remove aspas caso o usuário tenha colado caminho com aspas
    escolha_pasta = escolha_pasta.replace('"', '')

    if escolha_pasta in pastas_predefinidas:
        output_folder = pastas_predefinidas[escolha_pasta]
        escolha_valida = True
    elif escolha_pasta == "4":
        output_folder = input("Digite o caminho completo da pasta de destino: ").strip().replace('"', '')
        if output_folder:
            escolha_valida = True
    else:
        # Assume que é um caminho direto
        if len(escolha_pasta) > 3: # Verificação simples
             output_folder = escolha_pasta
             escolha_valida = True
        else:
             print("Opção inválida.")


print("\n" + "="*40)
print(f"🚀 Iniciando processamento de {len(lista_videos)} vídeos...")
print(f"📂 Salvando em: {output_folder}")
print("="*40 + "\n")

# 3. Loop de processamento
for i, video_path in enumerate(lista_videos):
    print(f"[{i+1}/{len(lista_videos)}] Processando...", end=" ")
    extrair_audio(video_path, output_folder)

print("\n\n🎉 Todos os vídeos foram processados!")
print(f"Verifique a pasta: {output_folder}")