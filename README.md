# 🎙️ Extrator de Texto de Vídeos

Um aplicativo para extrair texto falado de vídeos usando reconhecimento de fala. Transforme áudio em texto facilmente a partir de vídeos locais ou do YouTube.

![Versão](https://img.shields.io/badge/versão-1.0-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen)
![Conda](https://img.shields.io/badge/Conda-compatível-orange)

## 📋 Características

- **Processamento de Vídeos Locais**: Extraia texto de arquivos MP4, AVI, MKV, WEBM, MOV.
- **Suporte ao YouTube**: Cole uma URL do YouTube e extraia o texto automaticamente.
- **Multilíngue**: Suporte a vários idiomas incluindo Português do Brasil, Inglês, Espanhol entre outros.
- **Interface Gráfica Amigável**: Interface simples e intuitiva.
- **Ajuste de Segmentos**: Configure o tamanho dos segmentos de áudio para melhorar a precisão.
- **Organização Automática**: Cria automaticamente pastas para cada vídeo processado.


## 🔧 Requisitos

- Windows 10/11
- FFmpeg (instalado automaticamente pelo instalador)
- Conexão com internet (para vídeos do YouTube e uso da API Google Speech Recognition)

## 💾 Instalação

### Método 1: Instalador (Recomendado para usuários finais)

1. Baixe o instalador da [página de Releases](https://github.com/seu-usuario/extrator-texto-videos/releases)
2. Execute o arquivo `Instalador_Extrator_de_Texto.exe`
3. Siga as instruções do assistente de instalação

### Método 2: Usando Conda (Para desenvolvedores)

Este projeto foi desenvolvido usando Conda, que é recomendado para gerenciar as dependências:

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/extrator-texto-videos.git

# Entre no diretório
cd extrator-texto-videos

# Crie um ambiente Conda com as dependências necessárias
conda env create -f environment.yml

# Ative o ambiente
conda activate extrator-video

# Execute o aplicativo
python transcriber_gui.py
```

### Método 3: Instalação manual com Conda

Se o arquivo `environment.yml` não estiver disponível:

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/extrator-texto-videos.git

# Entre no diretório
cd extrator-texto-videos

# Crie um novo ambiente Conda
conda create -n extrator-video python=3.9

# Ative o ambiente
conda activate extrator-video

# Instale as dependências principais
conda install -c conda-forge tk
conda install -c conda-forge moviepy
conda install -c conda-forge pydub
conda install -c conda-forge speechrecognition

# Instale ferramentas adicionais
pip install yt-dlp

# Execute o aplicativo
python transcriber_gui.py
```

## 🔨 Criando um executável

Para criar um executável com PyInstaller em um ambiente Conda:

```bash
# Ative o ambiente Conda
conda activate extrator-video

# Instale o PyInstaller
conda install -c conda-forge pyinstaller

# Crie o executável
pyinstaller --onefile --windowed --name="Extrator de Texto de Vídeos" transcriber_gui.py

# O executável estará na pasta 'dist'
```

## 🚀 Como Usar

### Extraindo texto de um vídeo do YouTube:

1. Inicie o aplicativo
2. Selecione a aba "YouTube"
3. Cole a URL do vídeo do YouTube
4. Selecione o idioma do vídeo
5. Ajuste o tamanho do segmento conforme necessário (padrão: 30 segundos)
6. Clique em "INICIAR EXTRAÇÃO"
7. Aguarde o processo ser concluído
8. O texto extraído será salvo automaticamente em uma pasta com o nome do vídeo

### Extraindo texto de um vídeo local:

1. Inicie o aplicativo
2. Selecione a aba "Arquivo Local"
3. Clique em "Procurar..." e selecione seu arquivo de vídeo
4. Selecione o idioma do vídeo
5. Ajuste o tamanho do segmento conforme necessário
6. Clique em "INICIAR EXTRAÇÃO"
7. Aguarde o processo ser concluído
8. O texto extraído será salvo automaticamente em uma pasta com o nome do vídeo

## 📁 Estrutura de Arquivos
- `Instalador_Extrator_de_Texto.exe`: Instalador do Software
- `transcriber_gui.py`: Código principal da interface gráfica
- `video_transcriber.py`: Funções para extração de áudio e transcrição
- `environment.yml`: Definição do ambiente Conda (dependências)
- `icon.ico`: Ícone do aplicativo

## 🛠️ Tecnologias Utilizadas

- **Python**: Linguagem de programação base
- **Conda**: Gerenciador de pacotes e ambientes
- **Tkinter**: Framework para interface gráfica
- **SpeechRecognition**: API para reconhecimento de fala
- **MoviePy**: Biblioteca para processamento de vídeos
- **PyDub**: Manipulação de áudio
- **yt-dlp**: Biblioteca para download de vídeos do YouTube
- **FFmpeg**: Ferramenta para processamento de áudio/vídeo
- **PyInstaller**: Para criar o executável standalone

## ⚠️ Resolução de Problemas

### Erro "Acesso negado: 'videos'"

Se encontrar este erro ao iniciar o aplicativo:

1. Feche o aplicativo
2. Clique com o botão direito no ícone e selecione "Executar como administrador"

### O FFmpeg não é encontrado

O aplicativo procura o FFmpeg em:
- C:\ffmpeg\bin\ffmpeg.exe
- Na mesma pasta do executável
- No PATH do sistema

Para instalar o FFmpeg no ambiente Conda:
```bash
conda install -c conda-forge ffmpeg
```

Ou instale manualmente de [ffmpeg.org](https://ffmpeg.org/download.html) e adicione ao PATH.

### Problemas com PyInstaller e Conda

Se encontrar problemas ao criar o executável:

```bash
# Tente especificar dependências ocultas
pyinstaller --onefile --windowed --name="Extrator de Texto de Vídeos" --hidden-import=moviepy.video.io.ffmpeg_reader --hidden-import=speech_recognition transcriber_gui.py
```

### Erros na transcrição

Para melhorar a qualidade da transcrição:
- Reduza o tamanho do segmento para 15-20 segundos
- Certifique-se de selecionar o idioma correto
- Vídeos com melhor qualidade de áudio produzem melhores resultados

## 📄 Exportando o ambiente Conda

Para criar ou atualizar o arquivo `environment.yml`:

```bash
conda env export > environment.yml
```

Para criar uma versão mais portátil (somente com pacotes explicitamente instalados):

```bash
conda env export --from-history > environment.yml
```

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

## 👏 Créditos

Desenvolvido por [Julio Quevedo](https://www.linkedin.com/in/julioquevdo/)

### Bibliotecas e recursos utilizados:
- [Google Speech Recognition API](https://cloud.google.com/speech-to-text)
- [FFmpeg](https://ffmpeg.org/)
- [Conda](https://docs.conda.io/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/)
- [MoviePy](https://zulko.github.io/moviepy/)
- [PyDub](https://github.com/jiaaro/pydub)

---

🌟 Se este projeto foi útil para você, considere deixar uma estrela no GitHub! 🌟