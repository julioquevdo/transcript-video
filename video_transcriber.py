import os
import speech_recognition as sr
from moviepy.video.io.VideoFileClip import VideoFileClip
import argparse
import subprocess
import sys
import glob
from pydub import AudioSegment
import math
import time
import json
from datetime import datetime
import shutil


def create_video_folder(video_title, is_youtube=False, youtube_url=None):
    if not video_title or not isinstance(video_title, str):
        video_title = "video"
    
    youtube_id = None
    if is_youtube and youtube_url:
        try:
            if "v=" in youtube_url:
                youtube_id = youtube_url.split("v=")[1].split("&")[0]
                if not video_title or video_title == "youtube_video":
                    video_title = f"youtube_{youtube_id}"
        except:
            pass
    
    try:
        valid_name = "".join(c for c in video_title if c.isalnum() or c in " _-").strip()
        valid_name = valid_name.replace(" ", "_")
    except:
        valid_name = "video"
    
    if len(valid_name) > 50:
        valid_name = valid_name[:50]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{valid_name}_{timestamp}"
    
    if not os.path.exists("videos"):
        os.makedirs("videos")
    
    folder_path = os.path.join("videos", folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    try:
        info_file = os.path.join(folder_path, "info.txt")
        with open(info_file, "w", encoding="utf-8") as f:
            f.write(f"Título: {video_title}\n")
            f.write(f"Data de processamento: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            if is_youtube and youtube_url:
                f.write(f"URL do YouTube: {youtube_url}\n")
                if youtube_id:
                    f.write(f"ID do YouTube: {youtube_id}\n")
    except:
        pass
        
    return folder_path


def extract_audio_from_video(video_path, audio_path):
    try:
        print(f"Extracting audio from {video_path}...")
        
        if video_path.endswith('.m4a'):
            cmd = ['C:\\ffmpeg\\bin\\ffmpeg.exe', '-y', '-i', video_path, '-acodec', 'pcm_s16le', '-ar', '44100', audio_path]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Audio extracted successfully and saved to {audio_path}")
            return True
        
        video = VideoFileClip(video_path)
        
        if video.audio is None:
            print("Vídeo não tem áudio. Procurando arquivo de áudio correspondente...")
            
            base_name = os.path.splitext(video_path)[0]
            audio_files = glob.glob(f"{base_name}*.m4a") + glob.glob(f"{base_name}*.mp3") + glob.glob(f"{base_name}*.aac")
            
            if audio_files:
                print(f"Encontrado arquivo de áudio: {audio_files[0]}")
                cmd = ['C:\\ffmpeg\\bin\\ffmpeg.exe', '-y', '-i', audio_files[0], '-acodec', 'pcm_s16le', '-ar', '44100', audio_path]
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"Audio extracted successfully and saved to {audio_path}")
                return True
            else:
                print("Não foi encontrado nenhum arquivo de áudio correspondente.")
                return False
        
        video.audio.write_audiofile(audio_path, codec='pcm_s16le')
        print(f"Audio extracted successfully and saved to {audio_path}")
        return True
    except Exception as e:
        print(f"Error extracting audio: {e}")
        try:
            print("Tentando extração com FFmpeg...")
            cmd = ['C:\\ffmpeg\\bin\\ffmpeg.exe', '-y', '-i', video_path, '-acodec', 'pcm_s16le', '-ar', '44100', audio_path]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(audio_path):
                print(f"Audio extracted successfully with FFmpeg and saved to {audio_path}")
                return True
        except Exception as ffmpeg_error:
            print(f"FFmpeg extraction also failed: {ffmpeg_error}")
        
        return False


def split_audio_into_chunks(audio_path, chunk_length_ms=30000, output_dir="audio_chunks"):
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        print(f"Carregando o arquivo de áudio: {audio_path}")
        audio = AudioSegment.from_wav(audio_path)
        
        duration = len(audio)
        num_chunks = math.ceil(duration / chunk_length_ms)
        print(f"Dividindo o áudio em {num_chunks} segmentos de {chunk_length_ms/1000} segundos...")
        
        chunk_files = []
        for i in range(num_chunks):
            start_ms = i * chunk_length_ms
            end_ms = min((i + 1) * chunk_length_ms, duration)
            
            chunk = audio[start_ms:end_ms]
            chunk_file = os.path.join(output_dir, f"chunk_{i:03d}.wav")
            chunk.export(chunk_file, format="wav")
            chunk_files.append(chunk_file)
            
        print(f"Áudio dividido em {len(chunk_files)} segmentos")
        return chunk_files
    
    except Exception as e:
        print(f"Erro ao dividir o áudio: {e}")
        return []


def transcribe_audio_chunk(audio_path, language="en-US"):
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            
            text = recognizer.recognize_google(audio_data, language=language)
            return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"Erro na API do Google: {e}")
        return ""
    except Exception as e:
        print(f"Erro ao transcrever o chunk {audio_path}: {e}")
        return ""


def transcribe_audio_with_chunks(audio_path, language="en-US", chunk_length_sec=30, progress_callback=None):
    chunk_length_ms = chunk_length_sec * 1000
    
    chunk_files = split_audio_into_chunks(audio_path, chunk_length_ms, 
                                         os.path.join(os.path.dirname(audio_path), "audio_chunks"))
    
    if not chunk_files:
        return "Falha ao dividir o áudio em segmentos"
    
    print(f"Transcrevendo {len(chunk_files)} segmentos de áudio...")
    full_text = []
    
    for i, chunk_file in enumerate(chunk_files):
        print(f"Processando segmento {i+1} de {len(chunk_files)}...")
        chunk_text = transcribe_audio_chunk(chunk_file, language)
        
        if chunk_text:
            full_text.append(chunk_text)
        
        if progress_callback:
            progress = int((i + 1) / len(chunk_files) * 100)
            progress_callback(progress)
        
        try:
            os.remove(chunk_file)
        except:
            pass
    
    try:
        chunks_dir = os.path.join(os.path.dirname(audio_path), "audio_chunks")
        if os.path.exists(chunks_dir) and not os.listdir(chunks_dir):
            os.rmdir(chunks_dir)
    except:
        pass
    
    return " ".join(full_text)


def extract_speech_from_video(video_path, output_text_path=None, language="en-US", chunk_length_sec=30, progress_callback=None):
    video_dir = os.path.dirname(video_path)
    if not output_text_path:
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_text_path = os.path.join(video_dir, f"{base_name}_transcricao.txt")
    
    temp_audio_path = os.path.join(video_dir, "temp_audio.wav")
    
    if not extract_audio_from_video(video_path, temp_audio_path):
        base_name = os.path.splitext(video_path)[0]
        audio_files = glob.glob(f"{base_name}*.m4a") + glob.glob(f"{base_name}*.mp3") + glob.glob(f"{base_name}*.aac")
        
        if audio_files:
            print(f"Trying to use separate audio file: {audio_files[0]}")
            if not extract_audio_from_video(audio_files[0], temp_audio_path):
                return "Failed to extract audio from video and audio files"
        else:
            return "Failed to extract audio from video and no audio files found"
    
    if progress_callback:
        progress_callback(25)
    
    transcribed_text = transcribe_audio_with_chunks(
        temp_audio_path, 
        language, 
        chunk_length_sec,
        lambda progress: progress_callback(25 + progress * 0.75) if progress_callback else None
    )
    
    if os.path.exists(temp_audio_path):
        os.remove(temp_audio_path)
        print("Temporary audio file removed")
    
    if output_text_path and transcribed_text:
        try:
            with open(output_text_path, 'w', encoding='utf-8') as file:
                file.write(transcribed_text)
            print(f"Transcribed text saved to {output_text_path}")
        except Exception as e:
            print(f"Error saving transcribed text: {e}")
    
    if progress_callback:
        progress_callback(100)
    
    return transcribed_text


def download_youtube_video(youtube_url, output_folder=None, progress_callback=None):
    try:
        print(f"Downloading video from {youtube_url}...")
        
        try:
            subprocess.run(['C:\\ffmpeg\\bin\\ffmpeg.exe', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            print("FFmpeg não está instalado ou não está no PATH. Por favor, instale o FFmpeg.")
            print("Você pode baixá-lo em: https://ffmpeg.org/download.html")
            return None
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"], 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL)
            print("yt-dlp installed successfully")
        except:
            pass
        
        if not output_folder:
            output_folder = "."
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        progress_file = os.path.join(output_folder, "download_progress.json")
        
        def hook(d):
            if d['status'] == 'downloading':
                with open(progress_file, 'w') as f:
                    json.dump(d, f)
                
                if progress_callback and '_percent_str' in d:
                    try:
                        percent = float(d['_percent_str'].replace('%', ''))
                        progress_callback(percent)
                    except:
                        pass
            
            elif d['status'] == 'finished':
                if progress_callback:
                    progress_callback(100)
        
        yt_dlp_path = os.path.join(os.path.dirname(sys.executable), "Scripts", "yt-dlp")
        if not os.path.exists(yt_dlp_path):
            yt_dlp_path = "yt-dlp"
        
        output_template = os.path.join(output_folder, "%(title)s.%(ext)s")
        
        command = [
            yt_dlp_path, 
            youtube_url,
            "-o", output_template,
            "--force-overwrites",
            "--newline",
            "--progress",
            "--print", "after_move:filepath"
        ]
        
        title_command = [
            yt_dlp_path,
            youtube_url,
            "--print", "title",
            "--skip-download",
            "--no-warnings"
        ]
        
        try:
            title_process = subprocess.Popen(
                title_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            video_title, _ = title_process.communicate()
            video_title = video_title.strip()
            print(f"Título do vídeo: {video_title}")
        except:
            video_title = "youtube_video"
        
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        output_path = None
        
        for line in process.stdout:
            print(line.strip())
            if os.path.exists(line.strip()):
                output_path = line.strip()
        
        process.wait()
        
        if os.path.exists(progress_file):
            os.remove(progress_file)
        
        if process.returncode != 0:
            error = process.stderr.read()
            print(f"Error running yt-dlp: {error}")
            return None, None
        
        if not output_path:
            video_files = glob.glob(os.path.join(output_folder, "*"))
            video_files = [f for f in video_files if os.path.isfile(f) and not f.endswith('.json') and not f.endswith('.txt')]
            
            video_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            if video_files:
                output_path = video_files[0]
        
        if output_path:
            print(f"Video downloaded successfully to {output_path}")
            if video_title:
                return output_path, video_title
            else:
                return output_path
            
        print("Download appears to have failed, file not found")
        if video_title:
            return None, None
        else:
            return None
        
    except Exception as e:
        print(f"Error downloading YouTube video: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract speech text from video")
    
    video_source = parser.add_mutually_exclusive_group(required=True)
    video_source.add_argument("-f", "--file", help="Path to the input video file")
    video_source.add_argument("-y", "--youtube", help="YouTube video URL")
    
    parser.add_argument("-o", "--output", help="Path to save the transcribed text")
    parser.add_argument("-l", "--language", default="en-US", help="Language code for speech recognition (default: en-US)")
    parser.add_argument("-c", "--chunk", type=int, default=30, help="Length of audio chunks in seconds (default: 30)")
    
    args = parser.parse_args()
    
    try:
        import pydub
    except ImportError:
        print("Instalando dependência: pydub")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pydub"])
        import pydub
    
    try:
        subprocess.run(['C:\\ffmpeg\\bin\\ffmpeg.exe', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        print("AVISO: FFmpeg não está acessível no caminho C:\\ffmpeg\\bin\\ffmpeg.exe")
        print("Verifique se o FFmpeg está instalado neste local ou ajuste o caminho no código.")
    
    video_path = None
    output_folder = None
    
    if not os.path.exists("videos"):
        os.makedirs("videos")
    
    if args.youtube:
        temp_folder = os.path.join("videos", "temp_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)
        
        def print_progress(percent):
            print(f"\rDownload progress: {percent:.1f}%", end="", flush=True)
        
        video_path, video_title = download_youtube_video(args.youtube, temp_folder, print_progress)
        print()
        
        if not video_path:
            print("Failed to download YouTube video")
            exit(1)
            
        output_folder = create_video_folder(video_title or "youtube_video", True, args.youtube)
        print(f"Criada pasta para o vídeo: {output_folder}")
        
        new_video_path = os.path.join(output_folder, os.path.basename(video_path))
        shutil.move(video_path, new_video_path)
        video_path = new_video_path
        
        try:
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder)
        except:
            pass
    else:
        video_path = args.file
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_folder = create_video_folder(video_name)
        
        new_video_path = os.path.join(output_folder, os.path.basename(video_path))
        shutil.copy2(video_path, new_video_path)
        video_path = new_video_path
    
    output_path = args.output
    if not output_path:
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(output_folder, f"{video_name}_transcricao.txt")
    
    result = extract_speech_from_video(video_path, output_path, args.language, args.chunk)
    
    print("\nTranscribed Text:")
    print(result[:500] + "..." if len(result) > 500 else result)
    print(f"\nComprimento total do texto: {len(result)} caracteres")
    
    if output_path:
        print(f"\nTexto completo salvo em: {output_path}")