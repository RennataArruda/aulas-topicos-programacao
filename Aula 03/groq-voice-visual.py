
import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from datetime import timedelta
from collections import Counter
from groq import Groq
import pygame
import threading

# Inicializar cliente Groq
client = Groq()
pygame.mixer.init()

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

segmentos_transcricao = []

audio_paused = False
audio_start_time = 0

audio_filepath = ""
highlight_thread = None
parar_highlight = False

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

def selecionar_arquivo_local():
    global audio_filepath
    filepath = filedialog.askopenfilename(
        title="Selecione um arquivo de áudio",
        filetypes=[("Arquivos de Áudio", "*.mp3 *.wav *.m4a *.flac *.aac")]
    )
    if filepath:
        try:
            audio_filepath = filepath
            resultado = transcrever_audio_groq(filepath)
            exibir_resultado(resultado)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao processar o arquivo local:\n{e}")

def exibir_resultado(transcricao):
    texto_tempo.delete(1.0, tk.END)
    texto_completa.delete(1.0, tk.END)
    texto_stats.delete(1.0, tk.END)
    segmentos_transcricao.clear()

    if hasattr(transcricao, "text"):
        texto_completa.insert(tk.END, transcricao.text.strip())

    if hasattr(transcricao, "segments"):
        linha_num = int(texto_tempo.index(tk.END).split('.')[0])
        for segmento in transcricao.segments:
            inicio = str(timedelta(seconds=segmento["start"]))
            fim = str(timedelta(seconds=segmento["end"]))
            linha = f"[{inicio} - {fim}] {segmento['text']}\n"
            texto_tempo.insert(tk.END, linha)
            segmentos_transcricao.append({
                "start": segmento["start"],
                "end": segmento["end"],
                "tk_index": linha_num
            })
            linha_num += 1

        mostrar_estatisticas(transcricao)

def salvar_em_txt():
    conteudo = texto_completa.get("1.0", tk.END).strip()
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

def mostrar_estatisticas(transcricao):
    texto_stats.delete(1.0, tk.END)
    if hasattr(transcricao, "text"):
        palavras = transcricao.text.split()
        total_palavras = len(palavras)
        contador = Counter([p.strip(".,!?;:").lower() for p in palavras if len(p) > 2])
        mais_comuns = contador.most_common(5)
        tempo_total = 0
        if hasattr(transcricao, "segments") and len(transcricao.segments) > 0:
            tempo_total = transcricao.segments[-1]["end"]
        stats = f"- Total de palavras: {total_palavras}\n"
        stats += f"- Duração total do áudio: {str(timedelta(seconds=int(tempo_total)))}\n"
        stats += "- Palavras mais repetidas:\n"
        for palavra, qtd in mais_comuns:
            stats += f"  • {palavra}: {qtd}x\n"
        texto_stats.insert(tk.END, stats)

def iniciar_highlight(inicio=0):
    global highlight_thread, parar_highlight
    parar_highlight = True
    if highlight_thread and highlight_thread.is_alive():
        highlight_thread.join()
    parar_highlight = False
    highlight_thread = threading.Thread(target=destacar_transcricao, args=(inicio,))
    highlight_thread.start()

def destacar_transcricao(inicio=0):
    global segmentos_transcricao, parar_highlight
    while pygame.mixer.music.get_busy() and not parar_highlight:
        tempo_atual = pygame.mixer.music.get_pos() / 1000 + inicio
        for segmento in segmentos_transcricao:
            if segmento["start"] <= tempo_atual <= segmento["end"]:
                texto_tempo.tag_remove("highlight", "1.0", tk.END)
                texto_tempo.tag_add("highlight", f"{segmento['tk_index']}.0", f"{segmento['tk_index']}.end")
                texto_tempo.tag_config("highlight", background="#d0f0c0")
                break



def reproduzir_audio_tempo():
    global audio_filepath
    global audio_paused
    global audio_start_time

    if not audio_filepath:
        messagebox.showwarning("Aviso", "Nenhum áudio carregado.")
        return
    if audio_paused:
        pygame.mixer.music.unpause()
        audio_paused = False
    else:
        pygame.mixer.music.load(audio_filepath)
        pygame.mixer.music.play(start=audio_start_time)
        atualizar_temporizador()
        iniciar_highlight(audio_start_time)


def pausar_audio():
    global audio_paused, audio_start_time
    audio_paused = True
    audio_start_time = pygame.mixer.music.get_pos() / 1000
    pygame.mixer.music.pause()

    pygame.mixer.music.pause()


def parar_audio():
    global parar_highlight, audio_paused, audio_start_time

    pygame.mixer.music.stop()
    parar_highlight = True
    audio_paused = False
    audio_start_time = 0

    texto_tempo.tag_remove("highlight", "1.0", tk.END)
    label_timer.config(text="00:00")
    progresso_var.set(0)


def atualizar_temporizador():
    if pygame.mixer.music.get_busy():
        tempo = pygame.mixer.music.get_pos() // 1000
        label_timer.config(text=f"{tempo//60:02d}:{tempo%60:02d}")
        progresso_var.set(tempo)
    janela.after(500, atualizar_temporizador)

def clicar_transcricao(event):
    linha = int(texto_tempo.index(f"@{event.x},{event.y}").split('.')[0])
    for segmento in segmentos_transcricao:
        if segmento["tk_index"] == linha:
            reproduzir_audio_tempo()
            break

def obter_transcricao_atual():
    texto = texto_completa.get("1.0", tk.END).strip()
    if not texto:
        messagebox.showwarning("Aviso", "Nenhuma transcrição disponível.")
    return texto

def mostrar_modal_resumo(texto_resumo):
    modal = tk.Toplevel(janela)
    modal.title("📌 Resumo em Tópicos gerado pela IA")
    modal.geometry("800x500")
    modal.configure(bg="#f7f7f7")

    label = tk.Label(modal, text="📌 Resumo em Tópicos", font=("Segoe UI", 14, "bold"), bg="#f7f7f7")
    label.pack(pady=(10, 5))

    text_box = scrolledtext.ScrolledText(modal, wrap=tk.WORD, width=100, height=20,
                                         font=("Consolas", 10), bg="#ffffff", relief=tk.FLAT)
    text_box.pack(padx=10, pady=10, fill="both", expand=True)
    text_box.insert(tk.END, texto_resumo)
    text_box.config(state=tk.DISABLED)

    def salvar_resumo_txt():
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt")],
            title="Salvar resumo como"
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(texto_resumo)
                messagebox.showinfo("Sucesso", "Resumo salvo com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar o resumo:\n{e}")

    btn_salvar = tk.Button(modal, text="💾 Salvar como TXT", command=salvar_resumo_txt,
                           font=("Segoe UI", 10), bg="#27ae60", fg="white", padx=10, pady=5,
                           relief=tk.FLAT, cursor="hand2", activebackground="#2ecc71")
    btn_salvar.pack(pady=(0, 15))


def gerar_resumo_topicos():
    texto = obter_transcricao_atual()
    if texto:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um assistente que gera resumos em tópicos a partir de transcrições de áudio. Organize as principais ideias da transcrição em formato de tópicos claros e objetivos."
                    },
                    {
                        "role": "user",
                        "content": f"Este é o conteúdo da transcrição. Gere um resumo em tópicos em português:\n\n{texto}"
                    }
                ],
                model="deepseek-r1-distill-qwen-32b",
                temperature=0.5,
                max_completion_tokens=1024,
                top_p=1,
                stop=None,
                stream=False,
            )

            resposta_ia = chat_completion.choices[0].message.content.strip()
            mostrar_modal_resumo(resposta_ia)

        except Exception as e:
            messagebox.showerror("Erro ao gerar resumo com IA", str(e))

def mostrar_modal_ideias_chave(texto_ideias):
    modal = tk.Toplevel(janela)
    modal.title("💡 Ideias-Chave extraídas pela IA")
    modal.geometry("800x500")
    modal.configure(bg="#f7f7f7")

    label = tk.Label(modal, text="💡 Ideias-Chave", font=("Segoe UI", 14, "bold"), bg="#f7f7f7")
    label.pack(pady=(10, 5))

    text_box = scrolledtext.ScrolledText(modal, wrap=tk.WORD, width=100, height=20,
                                         font=("Consolas", 10), bg="#ffffff", relief=tk.FLAT)
    text_box.pack(padx=10, pady=10, fill="both", expand=True)
    text_box.insert(tk.END, texto_ideias)
    text_box.config(state=tk.DISABLED)

    def salvar_ideias_txt():
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt")],
            title="Salvar ideias-chave como"
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(texto_ideias)
                messagebox.showinfo("Sucesso", "Ideias-chave salvas com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar as ideias:\n{e}")

    btn_salvar = tk.Button(modal, text="💾 Salvar como TXT", command=salvar_ideias_txt,
                           font=("Segoe UI", 10), bg="#27ae60", fg="white", padx=10, pady=5,
                           relief=tk.FLAT, cursor="hand2", activebackground="#2ecc71")
    btn_salvar.pack(pady=(0, 15))


def extrair_ideias_chave():
    texto = obter_transcricao_atual()
    if texto:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um assistente de linguagem. Sua tarefa é analisar transcrições de áudio e extrair as ideias-chave mais relevantes, de forma clara e concisa em português."
                    },
                    {
                        "role": "user",
                        "content": f"A seguir está uma transcrição de áudio. Extraia as ideias-chave principais da transcrição:\n\n{texto}"
                    }
                ],
                model="deepseek-r1-distill-qwen-32b",
                temperature=0.5,
                max_completion_tokens=1024,
                top_p=1,
                stop=None,
                stream=False,
            )

            resposta_ia = chat_completion.choices[0].message.content.strip()
            mostrar_modal_ideias_chave(resposta_ia)

        except Exception as e:
            messagebox.showerror("Erro ao extrair ideias-chave com IA", str(e))

def mostrar_modal_coesao_textual(texto_reescrito):
    modal = tk.Toplevel(janela)
    modal.title("📝 Transcrição com Melhor Coesão Textual")
    modal.geometry("800x500")
    modal.configure(bg="#f7f7f7")

    label = tk.Label(modal, text="📝 Transcrição Reescrita com Melhor Coesão Textual", font=("Segoe UI", 14, "bold"), bg="#f7f7f7")
    label.pack(pady=(10, 5))

    text_box = scrolledtext.ScrolledText(modal, wrap=tk.WORD, width=100, height=20,
                                         font=("Consolas", 10), bg="#ffffff", relief=tk.FLAT)
    text_box.pack(padx=10, pady=10, fill="both", expand=True)
    text_box.insert(tk.END, texto_reescrito)
    text_box.config(state=tk.DISABLED)

    def salvar_coesao_txt():
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt")],
            title="Salvar texto reescrito como"
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(texto_reescrito)
                messagebox.showinfo("Sucesso", "Texto reescrito salvo com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar o texto reescrito:\n{e}")

    btn_salvar = tk.Button(modal, text="💾 Salvar como TXT", command=salvar_coesao_txt,
                           font=("Segoe UI", 10), bg="#27ae60", fg="white", padx=10, pady=5,
                           relief=tk.FLAT, cursor="hand2", activebackground="#2ecc71")
    btn_salvar.pack(pady=(0, 15))


def melhorar_coesao_textual():
    texto = obter_transcricao_atual()
    if texto:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um assistente de linguagem especializado em melhorar a coesão textual de textos. Reescreva a transcrição mantendo o mesmo significado, mas com maior fluidez, clareza e organização textual, em português."
                    },
                    {
                        "role": "user",
                        "content": f"A seguir está uma transcrição de áudio. Reescreva com melhor coesão textual:\n\n{texto}"
                    }
                ],
                model="deepseek-r1-distill-qwen-32b",
                temperature=0.5,
                max_completion_tokens=1024,
                top_p=1,
                stop=None,
                stream=False,
            )

            resposta_ia = chat_completion.choices[0].message.content.strip()
            mostrar_modal_coesao_textual(resposta_ia)

        except Exception as e:
            messagebox.showerror("Erro ao melhorar coesão textual com IA", str(e))


# Interface gráfica
janela = tk.Tk()
janela.title("✨ Transcrição Inteligente com Groq Whisper")
janela.geometry("1000x850")
janela.configure(bg="#ecf0f1")

menu_bar = tk.Menu(janela)
menu_ia = tk.Menu(menu_bar, tearoff=0)
menu_ia.add_command(label="📌 Geração de resumo em tópicos", command=gerar_resumo_topicos)
menu_ia.add_command(label="💡 Extrair Ideias Chave", command=extrair_ideias_chave)
menu_ia.add_command(label="📝 Melhorar coesão textual da transcrição", command=melhorar_coesao_textual)
menu_bar.add_cascade(label="🤖 Melhore com IA", menu=menu_ia)
janela.config(menu=menu_bar)

titulo = tk.Label(janela, text="🎧 Transcrição de Áudio com Marcação Inteligente",
                  font=("Segoe UI", 18, "bold"), bg="#ecf0f1", fg="#2c3e50")
titulo.pack(pady=10)

frame_botoes = tk.Frame(janela, bg="#ecf0f1")
frame_botoes.pack(pady=5)

def criar_botao(texto, cor_bg, comando):
    return tk.Button(frame_botoes, text=texto, command=comando,
                     font=("Segoe UI", 11), bg=cor_bg, fg="white",
                     padx=12, pady=6, relief=tk.FLAT, cursor="hand2", activebackground="#95a5a6")

btn_local = criar_botao("📂 Selecionar Áudio", "#2980b9", selecionar_arquivo_local)
btn_salvar = criar_botao("💾 Salvar em TXT", "#27ae60", salvar_em_txt)

btn_local.grid(row=0, column=0, padx=10, pady=5)
btn_salvar.grid(row=0, column=1, padx=10, pady=5)


frame_audio = tk.Frame(janela, bg="#ecf0f1")
frame_audio.pack(pady=5)

label_audio = tk.Label(frame_audio, text="🎵 Controle de Áudio",
                       font=("Segoe UI", 12, "bold"), bg="#ecf0f1", anchor="w")
label_audio.grid(row=0, column=0, columnspan=4, sticky="w", padx=5, pady=(5, 2))

def criar_audio_botao(texto, cor, comando):
    return tk.Button(frame_audio, text=texto, command=comando,
                     font=("Segoe UI", 10), bg=cor, fg="white",
                     padx=8, pady=4, relief=tk.FLAT, cursor="hand2", activebackground="#bdc3c7")

btn_play = criar_audio_botao("▶ Play", "#1abc9c", reproduzir_audio_tempo)
btn_pause = criar_audio_botao("⏸ Pause", "#f39c12", pausar_audio)
btn_stop = criar_audio_botao("⏹ Stop", "#e74c3c", parar_audio)

btn_play.grid(row=1, column=0, padx=5, pady=5)
btn_pause.grid(row=1, column=1, padx=5, pady=5)
btn_stop.grid(row=1, column=2, padx=5, pady=5)

label_timer = tk.Label(frame_audio, text="00:00", font=("Consolas", 11, "bold"),
                       bg="#ffffff", fg="#2c3e50", relief=tk.SOLID, borderwidth=1, padx=10, pady=2)
label_timer.grid(row=1, column=3, padx=15)

progresso_var = tk.DoubleVar()
slider_audio = tk.Scale(frame_audio, from_=0, to=100, orient=tk.HORIZONTAL,
                        variable=progresso_var, showvalue=0, length=300,
                        sliderlength=10, troughcolor="#dfe6e9", bg="#ecf0f1")
slider_audio.grid(row=2, column=0, columnspan=4, pady=(5, 10))

frame_exibicao = tk.Frame(janela, bg="#ecf0f1")
frame_exibicao.pack(fill="both", expand=True, padx=15, pady=10)

label_tempo = tk.Label(frame_exibicao, text="🕐 Transcrição com Marcação de Tempo",
                       font=("Segoe UI", 12, "bold"), bg="#ecf0f1", anchor="w")
label_tempo.pack(fill="x", padx=5)
texto_tempo = scrolledtext.ScrolledText(frame_exibicao, wrap=tk.WORD, width=120, height=10,
                                        font=("Consolas", 10), bg="#ffffff", relief=tk.FLAT, borderwidth=10)
texto_tempo.pack(pady=(0, 10), fill="x")
texto_tempo.bind("<Button-1>", clicar_transcricao)

label_completa = tk.Label(frame_exibicao, text="📝 Transcrição Completa",
                          font=("Segoe UI", 12, "bold"), bg="#ecf0f1", anchor="w")
label_completa.pack(fill="x", padx=5)
texto_completa = scrolledtext.ScrolledText(frame_exibicao, wrap=tk.WORD, width=120, height=10,
                                           font=("Consolas", 10), bg="#ffffff", relief=tk.FLAT, borderwidth=10)
texto_completa.pack(pady=(0, 10), fill="x")

label_stats = tk.Label(frame_exibicao, text="📊 Estatísticas da Transcrição",
                       font=("Segoe UI", 12, "bold"), bg="#ecf0f1", anchor="w")
label_stats.pack(fill="x", padx=5)
texto_stats = scrolledtext.ScrolledText(frame_exibicao, wrap=tk.WORD, width=120, height=6,
                                        font=("Consolas", 10), bg="#ffffff", relief=tk.FLAT, borderwidth=10)
texto_stats.pack(pady=(0, 10), fill="x")

janela.mainloop()
