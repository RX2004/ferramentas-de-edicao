# -*- coding: utf-8 -*-
"""
Baixador de vídeos do Telegram.

Dois modos, depois de escolher o canal ou grupo:
  [1] Por hashtag  - baixa só os vídeos das tags pedidas (#P01, #P02-P10...)
  [2] Todos        - baixa todos os vídeos do canal/grupo, do mais antigo ao mais novo

Os dois retomam de onde pararam: o que já foi baixado é pulado.
"""
import os
import re
import sys
import asyncio
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import Channel, Chat, InputMessagesFilterDocument, InputMessagesFilterVideo

for fluxo in (sys.stdout, sys.stderr):  # emojis em consoles que não usam UTF-8
    try:
        fluxo.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass


# --- CONFIGURAÇÕES ---
# As credenciais NUNCA ficam no código: vêm de variáveis de ambiente ou de um
# arquivo .env ao lado do script (veja .env.exemplo). Crie as suas em https://my.telegram.org
def carregar_env(arquivo=Path(__file__).with_name('.env')):
    """Lê um .env simples (CHAVE=valor) sem precisar de bibliotecas extras."""
    if arquivo.exists():
        for linha in arquivo.read_text(encoding='utf-8').splitlines():
            linha = linha.strip()
            if linha and not linha.startswith('#') and '=' in linha:
                chave, valor = linha.split('=', 1)
                os.environ.setdefault(chave.strip(), valor.strip().strip('"\''))


carregar_env()
try:
    API_ID = int(os.environ['TELEGRAM_API_ID'])
    API_HASH = os.environ['TELEGRAM_API_HASH']
except (KeyError, ValueError):
    raise SystemExit("❌ Defina TELEGRAM_API_ID e TELEGRAM_API_HASH (veja o arquivo .env.exemplo).")

SESSION_NAME = os.environ.get('TELEGRAM_SESSAO', 'baixador_por_hashtag')
# A sessão (seu login) fica fora da pasta do projeto, em ~/.telegram_downloader,
# para nunca ir parar no Git nem em pastas sincronizadas na nuvem.
PASTA_CONFIG = Path.home() / '.telegram_downloader'

PASTA_DOWNLOAD = Path(os.environ.get('TELEGRAM_PASTA_DOWNLOAD', Path.home() / 'Downloads' / 'telegram_midias'))
LIMITE_CANAIS = 50
# ---------------------

CARACTERES_INVALIDOS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def caminho_sessao():
    """Retorna o caminho do arquivo de sessão, fora da pasta do projeto."""
    PASTA_CONFIG.mkdir(parents=True, exist_ok=True)
    return str(PASTA_CONFIG / SESSION_NAME)


def nome_seguro(texto, limite=80):
    """
    Remove caracteres que o Windows não aceita em nomes de arquivo.
    """
    texto = CARACTERES_INVALIDOS.sub('_', texto).strip(' .')[:limite].strip(' .')
    return texto or 'sem_nome'


def expandir_tags(entrada):
    """
    Transforma a entrada do usuário em lista de tags.
    Aceita intervalos: '#P01-P05' vira #P01 #P02 #P03 #P04 #P05.
    """
    tags = []
    for item in entrada.replace(',', ' ').split():
        item = item.lstrip('#')
        intervalo = re.fullmatch(r'([^\d\s-]*)(\d+)-#?\1?(\d+)', item)
        if intervalo:
            prefixo, inicio, fim = intervalo.groups()
            largura = len(inicio)
            for n in range(int(inicio), int(fim) + 1):
                tags.append(f"#{prefixo}{n:0{largura}d}")
        elif item:
            tags.append(f"#{item}")
    return tags


def eh_video(mensagem):
    if mensagem.video:
        return True
    mime = (mensagem.document.mime_type or '') if mensagem.document else ''
    return mime.startswith('video')


def extensao_de(mensagem):
    return (mensagem.file.ext if mensagem.file else None) or '.mp4'


def ja_existe(pasta, nome_base):
    """Procura um arquivo completo (qualquer extensão, ignorando downloads incompletos)."""
    for existente in pasta.glob(f"{glob_seguro(nome_base)}.*"):
        if existente.suffix != '.part':
            return existente
    return None


def glob_seguro(texto):
    """Escapa [ e ] para o glob não tratá-los como padrão."""
    return re.sub(r'([\[\]])', r'[\1]', texto)


def exibir_progresso(recebido, total):
    """
    Função para exibir a barra de progresso do download.
    """
    if total > 0:
        percentual = 100 * recebido / total
        print(f"    Baixando... [{percentual:5.1f}%] {recebido / 1048576:.1f}/{total / 1048576:.1f} MB", end='\r')


async def baixar_midia(client, mensagem, caminho_final):
    """
    Baixa para .part e só renomeia no fim: um download interrompido nunca é
    confundido com um arquivo completo.
    """
    caminho_temp = caminho_final.with_name(caminho_final.name + '.part')
    await client.download_media(mensagem.media, file=str(caminho_temp), progress_callback=exibir_progresso)
    caminho_temp.replace(caminho_final)
    print(f"\n  📥 Download de '{caminho_final.name}' concluído.")


async def com_espera_do_telegram(acao):
    """Executa a ação; se o Telegram pedir para esperar (FloodWait), espera e tenta de novo."""
    while True:
        try:
            return await acao()
        except FloodWaitError as e:
            print(f"\n  ⏳ Limite do Telegram atingido. Aguardando {e.seconds}s...")
            await asyncio.sleep(e.seconds + 1)


# ----------------------------------------------------------- modo 1: por hashtag

async def baixar_tag(client, entidade, tag):
    """
    Procura e baixa o vídeo de uma tag. Retorna 'baixado', 'existe' ou 'nao_encontrado'.
    """
    nome_base = nome_seguro(tag[1:])

    existente = ja_existe(PASTA_DOWNLOAD, nome_base)
    if existente:
        print(f"  ✅ Arquivo '{existente.name}' já existe. Pulando.")
        return 'existe'

    # Tag exata: '#P1' não pode casar com '#P10'
    padrao_tag = re.compile(re.escape(tag) + r'(?![\w])', re.IGNORECASE)

    async for mensagem in client.iter_messages(entidade, search=tag, limit=10):
        if not (mensagem.text and padrao_tag.search(mensagem.text) and eh_video(mensagem)):
            continue

        caminho_final = PASTA_DOWNLOAD / f"{nome_base}{extensao_de(mensagem)}"
        print(f"  -> Vídeo encontrado! Baixando '{caminho_final.name}'...")
        await baixar_midia(client, mensagem, caminho_final)
        return 'baixado'

    print(f"  ❌ Nenhum vídeo encontrado para a tag {tag} (ou sem arquivo de vídeo na mensagem).")
    return 'nao_encontrado'


async def modo_hashtag(client, entidade):
    while True:
        print("\n" + "="*40)
        print("👉 Digite as hashtags separadas por espaço (aceita intervalo: #P01-P10).")
        entrada_usuario = input("Exemplo: #P01 #P02 #P05 (ou 'sair'): ").strip()

        if not entrada_usuario:
            continue
        if entrada_usuario.lower() == 'sair':
            return

        tags = expandir_tags(entrada_usuario)
        print(f"\n📋 Processando {len(tags)} itens...")

        resultados = {'baixado': [], 'existe': [], 'nao_encontrado': [], 'erro': []}

        for tag in tags:
            print(f"\n🔎 [Tag: {tag}] Procurando...")
            # Um erro em uma tag não interrompe as demais
            try:
                resultado = await com_espera_do_telegram(lambda: baixar_tag(client, entidade, tag))
                resultados[resultado].append(tag)
            except Exception as e:
                print(f"\n  ❌ Erro ao processar {tag}: {e}")
                resultados['erro'].append(tag)

        print("\n" + "-" * 40)
        print("📊 Resumo:")
        print(f"  📥 Baixados:        {len(resultados['baixado'])} {' '.join(resultados['baixado'])}")
        print(f"  ✅ Já existiam:     {len(resultados['existe'])} {' '.join(resultados['existe'])}")
        print(f"  ❌ Não encontrados: {len(resultados['nao_encontrado'])} {' '.join(resultados['nao_encontrado'])}")
        print(f"  ⚠️  Com erro:        {len(resultados['erro'])} {' '.join(resultados['erro'])}")


# ------------------------------------------------------------ modo 2: todos

def nome_do_video(mensagem):
    """
    Nome do arquivo no modo 'todos': o número da mensagem vem na frente, então os
    vídeos ficam na ordem em que foram postados e dois vídeos nunca têm o mesmo nome.
    Depois vem o nome original do arquivo ou, se não houver, a primeira linha da legenda.
    """
    original = Path(mensagem.file.name).stem if (mensagem.file and mensagem.file.name) else ''
    legenda = (mensagem.text or '').strip().splitlines()[0] if (mensagem.text or '').strip() else ''
    descricao = nome_seguro(original or legenda or 'video', limite=60)
    return f"{mensagem.id:06d}_{descricao}"


async def listar_videos(client, entidade):
    """
    Junta os vídeos normais e os enviados 'como arquivo', do mais antigo ao mais novo.
    """
    videos = {}
    async for mensagem in client.iter_messages(entidade, filter=InputMessagesFilterVideo, reverse=True):
        videos[mensagem.id] = mensagem
    async for mensagem in client.iter_messages(entidade, filter=InputMessagesFilterDocument, reverse=True):
        if eh_video(mensagem):
            videos[mensagem.id] = mensagem
    return [videos[i] for i in sorted(videos)]


def tamanho_legivel(total_bytes):
    for unidade in ('B', 'KB', 'MB', 'GB'):
        if total_bytes < 1024 or unidade == 'GB':
            return f"{total_bytes:.1f} {unidade}" if unidade != 'B' else f"{total_bytes} B"
        total_bytes /= 1024


async def modo_todos(client, entidade):
    titulo = getattr(entidade, 'title', None) or 'canal'
    pasta = PASTA_DOWNLOAD / nome_seguro(titulo)

    print("🔎 Procurando todos os vídeos... (pode levar um tempo em grupos grandes)")
    videos = await com_espera_do_telegram(lambda: listar_videos(client, entidade))
    if not videos:
        print("🟡 Nenhum vídeo encontrado neste canal/grupo.")
        return

    pendentes = [m for m in videos if not ja_existe(pasta, nome_do_video(m))]
    tamanho = sum((m.file.size or 0) for m in pendentes if m.file)

    print(f"\n🎬 {len(videos)} vídeo(s) encontrado(s) em '{titulo}'.")
    if len(pendentes) < len(videos):
        print(f"   ✅ {len(videos) - len(pendentes)} já baixado(s) antes, serão pulados.")
    if not pendentes:
        print("   Nada novo para baixar.")
        return
    print(f"   📥 Faltam {len(pendentes)}, cerca de {tamanho_legivel(tamanho)}.")
    print(f"   📂 Destino: {pasta}")

    if input("\nConfirmar o download? (s/n): ").strip().lower() not in ('s', 'sim'):
        print("Cancelado.")
        return
    pasta.mkdir(parents=True, exist_ok=True)

    baixados, erros = 0, []
    for n, mensagem in enumerate(pendentes, 1):
        caminho_final = pasta / f"{nome_do_video(mensagem)}{extensao_de(mensagem)}"
        print(f"\n[{n}/{len(pendentes)}] {caminho_final.name}")
        try:
            await com_espera_do_telegram(lambda: baixar_midia(client, mensagem, caminho_final))
            baixados += 1
        except Exception as e:  # um vídeo com erro não interrompe os demais
            print(f"\n  ❌ Erro: {e}")
            erros.append(caminho_final.name)

    print("\n" + "-" * 40)
    print("📊 Resumo:")
    print(f"  📥 Baixados:    {baixados}")
    print(f"  ✅ Já existiam: {len(videos) - len(pendentes)}")
    print(f"  ⚠️  Com erro:    {len(erros)}")
    for nome in erros:
        print(f"     - {nome}")
    if erros:
        print("  Rode de novo para tentar só os que falharam.")


# ------------------------------------------------------------------- início

async def escolher_canal(client):
    """
    Lista os canais e grupos recentes e retorna a entidade escolhida (ou None).
    """
    print("Buscando seus canais e grupos... (Aguarde)")

    canais = []
    async for dialog in client.iter_dialogs(limit=LIMITE_CANAIS):
        if isinstance(dialog.entity, (Channel, Chat)):
            tipo = 'canal' if dialog.is_channel and not dialog.is_group else 'grupo'
            canais.append((dialog.title, tipo, dialog.entity))

    if not canais:
        print(f"🟡 Nenhum canal ou grupo encontrado nos seus {LIMITE_CANAIS} chats recentes.")
    else:
        print("--- 🔎 Escolha um canal ou grupo da lista ---")
        for i, (titulo, tipo, _) in enumerate(canais):
            print(f"  [{i+1}] {titulo} ({tipo})")

    print("-" * 30)
    print("👉 Ou cole o link/username (ex: @canal_xyz ou https://t.me/...)")

    canal_input = input("\nDigite o NÚMERO ou o LINK/USERNAME: ").strip()

    if not canal_input:
        print("❌ Nenhuma opção inserida. Encerrando.")
        return None

    if canal_input.isdigit():
        indice = int(canal_input) - 1
        if not 0 <= indice < len(canais):
            print("❌ Número inválido. Fora da lista.")
            return None
        print(f"🔎 Acessando: '{canais[indice][0]}'")
        return canais[indice][2]

    print("🔎 Tentando acessar por link/username...")
    try:
        entidade = await client.get_entity(canal_input)
    except (ValueError, TypeError) as e:
        print(f"❌ Não foi possível acessar o canal: {e}")
        return None
    print(f"🔎 Acessando: '{getattr(entidade, 'title', 'Nome não disponível')}'")
    return entidade


def escolher_modo():
    print("\nO que você quer baixar?")
    print("  [1] Vídeos por hashtag (#P01, #P02-P10...)")
    print("  [2] TODOS os vídeos deste canal/grupo")
    while True:
        opcao = input("Digite 1 ou 2: ").strip()
        if opcao in ('1', '2'):
            return opcao


async def main():
    try:
        PASTA_DOWNLOAD.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"❌ Erro ao criar o diretório: {e}")
        return

    async with TelegramClient(caminho_sessao(), API_ID, API_HASH) as client:
        print("✅ Conectado com sucesso ao Telegram.")
        print("-" * 30)

        entidade = await escolher_canal(client)
        if entidade is None:
            return
        print("-" * 30)

        if escolher_modo() == '1':
            await modo_hashtag(client, entidade)
        else:
            await modo_todos(client, entidade)

    print("\n\n🎉 Processo finalizado!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Script interrompido pelo usuário.")
