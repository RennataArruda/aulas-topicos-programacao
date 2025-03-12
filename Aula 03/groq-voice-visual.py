import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from datetime import timedelta
from collections import Counter
from groq import Groq

# Inicializar cliente Groq
client = Groq()

# Pasta temporária
TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

# Função para transcrever o áudio usando a API Groq
def transcrever_audio_groq(caminho_arquivo):
    with open(caminho_arquivo, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(caminho_arquivo), file.read()),
            model="whisper-large-v3-turbo",
            prompt="Entrevista",
            response_format="verbose_json",
            language="pt",
            temperature=0.0
        )
        return transcription

# Função para selecionar arquivo local
def selecionar_arquivo_local():
    filepath = filedialog.askopenfilename(
        title="Selecione um arquivo de áudio",
        filetypes=[("Arquivos de Áudio", "*.mp3 *.wav *.m4a *.flac *.aac")]
    )
    if filepath:
        try:
            resultado = transcrever_audio_groq(filepath)
            exibir_resultado(resultado)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao processar o arquivo local:\n{e}")

# Função para exibir o resultado da transcrição
def exibir_resultado(transcricao):
    texto_resultado.delete(1.0, tk.END)

    if hasattr(transcricao, "text"):
        texto_resultado.insert(tk.END, "📝 Transcrição Completa:\n\n")
        texto_resultado.insert(tk.END, transcricao.text + "\n\n")

    if hasattr(transcricao, "segments"):
        texto_resultado.insert(tk.END, "🕐 Transcrição com Marcação de Tempo:\n\n")
        for segmento in transcricao.segments:
            inicio = str(timedelta(seconds=segmento["start"]))
            fim = str(timedelta(seconds=segmento["end"]))
            linha = f"[{inicio} - {fim}] {segmento['text']}\n"
            texto_resultado.insert(tk.END, linha)

        mostrar_estatisticas(transcricao)

# Função para salvar transcrição em .txt
def salvar_em_txt():
    conteudo = texto_resultado.get("1.0", tk.END).strip()
    if not conteudo:
        messagebox.showwarning("Aviso", "Nenhuma transcrição disponível para salvar.")
        return

    filepath = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de Texto", "*.txt")],
        title="Salvar transcrição como"
    )
    if filepath:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(conteudo)
            messagebox.showinfo("Sucesso", "Transcrição salva com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo:\n{e}")

# Função para exibir estatísticas da transcrição
def mostrar_estatisticas(transcricao):
    if hasattr(transcricao, "text"):
        palavras = transcricao.text.split()
        total_palavras = len(palavras)
        contador = Counter([p.strip(".,!?;:").lower() for p in palavras if len(p) > 2])
        mais_comuns = contador.most_common(5)

        tempo_total = 0
        if hasattr(transcricao, "segments") and len(transcricao.segments) > 0:
            tempo_total = transcricao.segments[-1]["end"]

        stats = f"\n📊 Estatísticas da Transcrição:\n"
        stats += f"- Total de palavras: {total_palavras}\n"
        stats += f"- Duração total do áudio: {str(timedelta(seconds=int(tempo_total)))}\n"
        stats += f"- Palavras mais repetidas:\n"
        for palavra, qtd in mais_comuns:
            stats += f"  • {palavra}: {qtd}x\n"

        texto_resultado.insert(tk.END, stats + "\n")

# Criar interface gráfica
janela = tk.Tk()
janela.title("Transcrição de Áudio com Estatísticas - Groq Whisper")
janela.geometry("900x700")
janela.configure(bg="#f0f4f8")

# Título
titulo = tk.Label(
    janela,
    text="🎧 Transcrição de Áudio com Marcação de Tempo",
    font=("Helvetica", 16, "bold"),
    bg="#f0f4f8",
    fg="#2c3e50"
)
titulo.pack(pady=10)

# Botão Selecionar
btn_local = tk.Button(
    janela,
    text="📂 Selecionar Arquivo de Áudio",
    font=("Helvetica", 12),
    command=selecionar_arquivo_local,
    bg="#3498db",
    fg="white",
    padx=10,
    pady=5
)
btn_local.pack(pady=10)

# Botão Salvar
btn_salvar = tk.Button(
    janela,
    text="💾 Salvar Transcrição em TXT",
    font=("Helvetica", 12),
    command=salvar_em_txt,
    bg="#2ecc71",
    fg="white",
    padx=10,
    pady=5
)
btn_salvar.pack(pady=5)

# Área de texto
texto_resultado = scrolledtext.ScrolledText(
    janela,
    wrap=tk.WORD,
    width=110,
    height=30,
    font=("Consolas", 10),
    bg="#ffffff"
)
texto_resultado.pack(padx=10, pady=15)

# Iniciar interface
janela.mainloop()
