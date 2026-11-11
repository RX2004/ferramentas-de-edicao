# 🎬 Ferramentas de Edição em Python

Três scripts que tiram trabalho repetitivo do fluxo de edição de vídeo e de documentos.
Cada um resolve uma tarefa que eu fazia à mão, arquivo por arquivo.

| Ferramenta | Problema que resolve | Tempo economizado (estimativa) |
|---|---|---|
| [**Extrator de áudio em lote**](#-extrator-de-áudio-em-lote) | Tirar o áudio (MP3) de dezenas de vídeos para transcrever, legendar ou reaproveitar | ~2 min por vídeo → **1 hora vira poucos minutos** numa pasta com 30 vídeos |
| [**OCR de PDF**](#-ocr-de-pdf) | PDFs escaneados não deixam buscar nem copiar texto | Evita redigitar trechos; um PDF de 100 páginas fica pesquisável **em ~1 a 3 min** |
| [**Baixador do Telegram por hashtag**](#-baixador-do-telegram-por-hashtag) | Baixar vídeos específicos (ou todos) de um canal ou grupo, um por um, e organizar os nomes | ~1 min por vídeo (achar, baixar, renomear) → **dezenas de vídeos de uma vez**, já nomeados |

> As estimativas são do meu uso real; o ganho depende do tamanho dos arquivos e do computador.

---

## 🔊 Extrator de áudio em lote
`extrator-de-audio/video_para_audio.py`

**O que faz:** você aponta uma pasta (ou um arquivo) e ele gera um `.mp3` para cada vídeo.
- Aceita `.mp4`, `.mkv`, `.avi`, `.mov`, `.flv`, `.wmv`
- **Pula os que já foram convertidos** — dá para rodar de novo na mesma pasta sem refazer nada
- Avisa quando um vídeo não tem faixa de áudio, em vez de travar
- Libera a memória a cada vídeo (importante em pastas grandes)

```bash
pip install moviepy
python extrator-de-audio/video_para_audio.py
```
O script pergunta a pasta de origem e a de destino.

---

## 📄 OCR de PDF
`ocr-pdf/ocr_pdf.py`

**O que faz:** recebe um PDF escaneado (só imagem) e cria `nome_pesquisavel.pdf`, com uma camada de texto
invisível por cima — o visual não muda, mas agora dá para **buscar (Ctrl+F), selecionar e copiar** o texto.
- Só faz OCR nas páginas escaneadas: páginas que já têm texto digital ficam intactas (sem texto duplicado)
- Escolha o idioma: `por` (padrão), `eng`, ou os dois juntos com `por+eng`
- Mensagens de erro claras (PDF com senha, arquivo aberto em outro programa, idioma não instalado…)
  e código de saída 1 quando falha, para usar em lote ou em outros scripts

```bash
pip install ocrmypdf          # requer o Tesseract (com o idioma português) e o Ghostscript instalados
python ocr-pdf/ocr_pdf.py "documento.pdf"
python ocr-pdf/ocr_pdf.py "documento.pdf" por+eng
```

---

## 📥 Baixador do Telegram por hashtag
`telegram-baixador/baixador_por_hashtag.py`

**O que faz:** depois de escolher o canal ou grupo, você escolhe o modo:

**[1] Por hashtag.** Em canais que organizam os vídeos por hashtag (`#P01`, `#P02`…), ele busca e baixa
só os que você pedir, já com o nome da hashtag.

**[2] Todos os vídeos.** Baixa todos os vídeos do canal ou grupo, do mais antigo ao mais novo, numa pasta
com o nome do grupo.
- Pega também os vídeos enviados "como arquivo" (e ignora PDFs, fotos e outros arquivos)
- Antes de começar, mostra quantos vídeos são, quantos já foram baixados e o tamanho total, e pede confirmação
- Nomes na ordem de postagem: `000123_Aula 01.mp4` (número da mensagem + nome original ou legenda)
- Um vídeo com erro não para os outros; rode de novo para baixar só o que faltou

**Nos dois modos:**
- **Intervalos:** digite `#P01-P20` e ele entende `#P01, #P02 … #P20`
- **Tag exata:** `#P1` não baixa `#P10` por engano
- **Download seguro:** baixa primeiro para `.part` e só renomeia no fim — um download interrompido nunca
  é confundido com um arquivo completo
- **Retoma de onde parou:** pula o que já foi baixado
- **Respeita o limite do Telegram:** se o servidor pedir para esperar (FloodWait), ele espera e continua
- Lista seus canais recentes para escolher pelo número, ou aceita link/@username
- Resumo no fim: baixados, já existentes, não encontrados e com erro

### Configuração (uma vez)
1. Crie suas credenciais de API em <https://my.telegram.org> → *API development tools*.
2. Copie `telegram-baixador/.env.exemplo` para `telegram-baixador/.env` e preencha:
   ```env
   TELEGRAM_API_ID=123456
   TELEGRAM_API_HASH=sua_chave_aqui
   ```
3. Rode:
   ```bash
   pip install telethon
   python telegram-baixador/baixador_por_hashtag.py
   ```
   Na primeira vez o Telegram envia um código de login para o seu app.

### 🔒 Segurança
- **Nenhuma credencial fica no código.** Ela vem do `.env`, que está no `.gitignore`.
- O arquivo de **sessão** (que mantém você logado) é salvo em `~/.telegram_downloader`, **fora da pasta
  do projeto** — assim nunca vai parar no Git nem em pastas sincronizadas na nuvem.
- Use apenas em canais a que você tem acesso e com conteúdo que você tem direito de baixar.

---

## Tecnologias
Python 3 · [MoviePy](https://zulko.github.io/moviepy/) · [OCRmyPDF](https://ocrmypdf.readthedocs.io/) ·
[Telethon](https://docs.telethon.dev/) (API oficial do Telegram) · asyncio

## Licença
MIT — veja [LICENSE](LICENSE).
