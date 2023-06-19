
from typing import Dict, Tuple, Optional, IO
import sys
import subprocess as sp
import select
from pathlib import Path
import io
from threading import Thread
import demucs
from tkinter.filedialog import askopenfile
import tkinter.ttk as ttk
import tkinter as tk
from tkinter.ttk import *
from tkinter import *
import pygame
import os
from basic_pitch.inference import predict


pygame.mixer.init()
model = "htdemucs"
extensions = ["wav", "mp3", "flac", "aif", "aiff"]
two_stems = None
mp3 = True
mp3_rate = 320
float32 = False  # output as float 32 wavs, unsused if 'mp3' is True.
int24 = False
file = ''


def copy_process_streams(process: sp.Popen):
    def raw(stream: Optional[IO[bytes]]) -> IO[bytes]:
        assert stream is not None
        if isinstance(stream, io.BufferedIOBase):
            stream = stream.raw
        return stream

    p_stdout, p_stderr = raw(process.stdout), raw(process.stderr)
    stream_by_fd: Dict[int, Tuple[IO[bytes], io.StringIO, IO[str]]] = {
        p_stdout.fileno(): (p_stdout, sys.stdout),
        p_stderr.fileno(): (p_stderr, sys.stderr),
    }
    fds = list(stream_by_fd.keys())

    while fds:
        # `select` syscall will wait until one of the file descriptors has content.
        ready, _, _ = select.select(fds, [], [])
        for fd in ready:
            p_stream, std = stream_by_fd[fd]
            raw_buf = p_stream.read(2 ** 16)
            if not raw_buf:
                fds.remove(fd)
                continue
            buf = raw_buf.decode()
            std.write(buf)
            std.flush()


def separate(inp=None, outp=None):
    cmd = ["python3", "-m", "demucs.separate", "-o", str(outp), "-n", model]
    if mp3:
        cmd += ["--mp3", f"--mp3-bitrate={mp3_rate}"]
    if float32:
        cmd += ["--float32"]
    if int24:
        cmd += ["--int24"]
    if two_stems is not None:
        cmd += [f"--two-stems={two_stems}"]
    files = [inp, ]
    print(files)
    if not files:
        print("File not found!")
        return
    print("Going to separate the files:")
    print('\n'.join(files))
    print("With command: ", " ".join(cmd))
    p = sp.Popen(cmd + files, stdout=sp.PIPE, stderr=sp.PIPE)
    copy_process_streams(p)
    p.wait()
    if p.returncode != 0:
        print("Command failed, something went wrong.")


def audio_button():
    listenButtonVox.grid_remove()
    listenButtonBass.grid_remove()
    listenButtonDrum.grid_remove()
    listenButtonOth.grid_remove()
    midiButtonVox.grid_remove()
    midiButtonBass.grid_remove()
    midiButtonDrum.grid_remove()
    midiButtonOth.grid_remove()

    file_path = askopenfile(mode='r', filetypes=[
                            ("Audio Files", "*.wav"), ("Audio Files", "*.mp3")])
    global file
    if file_path is not None:
        file = file_path.name
        print("Chosen File:", file)
        listenButton.state(["!disabled"])
    if file_path is None:
        listenButton.state(["disabled"])
        print("No file chosen")


def listen_button():
    print("The listen button was clicked!")
    pygame.mixer.music.load(file)
    pygame.mixer.music.play(loops=0)
    listenButton.grid_remove()
    pauseButton.grid(row=0, column=1, padx=5, pady=5)


def midi_button(button_pressed):

    if button_pressed == "vox":
        model_output, midi_data, note_activations = predict(Path.home(
        )/"Downloads"/"htdemucs"/os.path.basename(file).split(".")[0]/"vocals.mp3")
        midi_data.write(str(Path.home()/"Downloads"/"htdemucs" /
                        os.path.basename(file).split(".")[0]/"Vocals_Midi_file.mid"))

    if button_pressed == "bass":
        model_output, midi_data, note_activations = predict(
            Path.home()/"Downloads"/"htdemucs"/os.path.basename(file).split(".")[0]/"bass.mp3")
        midi_data.write(str(Path.home()/"Downloads"/"htdemucs" /
                        os.path.basename(file).split(".")[0]/"Bass_Midi_file.mid"))

    if button_pressed == "drum":
        model_output, midi_data, note_activations = predict(Path.home(
        )/"Downloads"/"htdemucs"/os.path.basename(file).split(".")[0]/"drums.mp3")
        midi_data.write(str(Path.home()/"Downloads"/"htdemucs" /
                        os.path.basename(file).split(".")[0]/"Drums_Midi_file.mid"))

    if button_pressed == "other":
        model_output, midi_data, note_activations = predict(Path.home(
        )/"Downloads"/"htdemucs"/os.path.basename(file).split(".")[0]/"other.mp3")
        midi_data.write(str(Path.home()/"Downloads"/"htdemucs" /
                        os.path.basename(file).split(".")[0]/"Other_Midi_file.mid"))


def stop_audio():
    pauseButton.grid_remove()
    listenButton.grid(row=0, column=1, padx=5, pady=5)
    pygame.mixer.music.stop()


def run_button():

    runButton.grid_remove()
    progress.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
    progress.start()
    createThread().start()


def start_separator():

    addAudioButton.state(["disabled"])
    listenButton.state(["disabled"])
    global file
    separate(file, str(Path.home() / "Downloads"))
    progress.stop()
    progress.grid_remove()
    addAudioButton.state(["!disabled"])
    listenButton.state(["!disabled"])
    runButton.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
    listenButtonVox.grid(row=3, column=0, padx=5, pady=5)
    listenButtonBass.grid(row=4, column=0, padx=5, pady=5)
    listenButtonDrum.grid(row=5, column=0, padx=5, pady=5)
    listenButtonOth.grid(row=6, column=0, padx=5, pady=5)

    midiButtonVox.grid(row=3, column=1, padx=5, pady=5)
    midiButtonBass.grid(row=4, column=1, padx=5, pady=5)
    midiButtonDrum.grid(row=5, column=1, padx=5, pady=5)
    midiButtonOth.grid(row=6, column=1, padx=5, pady=5)
    window.update()


def listen_extracted(button_pressed):
    if button_pressed == "vox":
        pygame.mixer.music.load(str(Path.home(
        )/"Downloads"/"htdemucs"/os.path.basename(file).split(".")[0]/"vocals.mp3"))
        pygame.mixer.music.play(loops=0)
        listenButtonVox.grid_remove()
        listenButtonBass.grid(row=4, column=0, padx=5, pady=5)
        listenButtonDrum.grid(row=5, column=0, padx=5, pady=5)
        listenButtonOth.grid(row=6, column=0, padx=5, pady=5)
        pauseVoxButton.grid(row=3, column=0, padx=5, pady=5)
        pauseBassButton.grid_remove()
        pauseDrumButton.grid_remove()
        pauseOthButton.grid_remove()

    if button_pressed == "bass":
        pygame.mixer.music.load(str(Path.home(
        )/"Downloads"/"htdemucs"/os.path.basename(file).split(".")[0]/"bass.mp3"))
        pygame.mixer.music.play(loops=0)
        listenButtonBass.grid_remove()
        listenButtonDrum.grid(row=5, column=0, padx=5, pady=5)
        listenButtonOth.grid(row=6, column=0, padx=5, pady=5)
        pauseBassButton.grid(row=4, column=0, padx=5, pady=5)
        listenButtonVox.grid(row=3, column=0, padx=5, pady=5)
        pauseVoxButton.grid_remove()
        pauseDrumButton.grid_remove()
        pauseOthButton.grid_remove()

    if button_pressed == "drum":
        pygame.mixer.music.load(str(Path.home(
        )/"Downloads"/"htdemucs"/os.path.basename(file).split(".")[0]/"drums.mp3"))
        pygame.mixer.music.play(loops=0)
        listenButtonDrum.grid_remove()
        pauseDrumButton.grid(row=5, column=0, padx=5, pady=5)
        listenButtonVox.grid(row=3, column=0, padx=5, pady=5)
        listenButtonBass.grid(row=4, column=0, padx=5, pady=5)
        listenButtonOth.grid(row=6, column=0, padx=5, pady=5)
        pauseVoxButton.grid_remove()
        pauseBassButton.grid_remove()
        pauseOthButton.grid_remove()

    if button_pressed == "other":
        pygame.mixer.music.load(str(Path.home(
        )/"Downloads"/"htdemucs"/os.path.basename(file).split(".")[0]/"other.mp3"))
        pygame.mixer.music.play(loops=0)
        listenButtonOth.grid_remove()
        pauseOthButton.grid(row=6, column=0, padx=5, pady=5)
        listenButtonVox.grid(row=3, column=0, padx=5, pady=5)
        listenButtonBass.grid(row=4, column=0, padx=5, pady=5)
        listenButtonDrum.grid(row=5, column=0, padx=5, pady=5)
        pauseVoxButton.grid_remove()
        pauseBassButton.grid_remove()
        pauseDrumButton.grid_remove()


def pause_audio():
    pygame.mixer.music.pause()
    listenButtonVox.grid(row=3, column=0, padx=5, pady=5)
    listenButtonBass.grid(row=4, column=0, padx=5, pady=5)
    listenButtonDrum.grid(row=5, column=0, padx=5, pady=5)
    listenButtonOth.grid(row=6, column=0, padx=5, pady=5)

    pauseVoxButton.grid_remove()
    pauseBassButton.grid_remove()
    pauseDrumButton.grid_remove()
    pauseOthButton.grid_remove()


def createThread():
    return Thread(target=start_separator)


window = tk.Tk()
window.update()
window.columnconfigure(0, weight=1, minsize=75)
window.columnconfigure(1, weight=3, minsize=75)
window.title("SourceAudio")
window.configure(background='grey')
window.resizable(False, False)
style = ttk.Style()
style.theme_use('alt')

# Upload Audio Button
addAudioButton = ttk.Button(
    window, text="Upload Audio", command=audio_button, width=25)
addAudioButton.grid(row=0, column=0, padx=5, pady=5)

listenButton = ttk.Button(
    window, text="Listen to  Audio", command=listen_button, width=25)
listenButton.grid(row=0, column=1, padx=5, pady=5)
listenButton.state(['disabled'])

# pause audio button
pauseButton = ttk.Button(window, text="Pause Audio",
                         command=stop_audio, width=25)
pauseVoxButton = ttk.Button(
    window, text="Stop", command=pause_audio, width=25)
pauseBassButton = ttk.Button(
    window, text="Stop", command=pause_audio, width=25)
pauseDrumButton = ttk.Button(
    window, text="Stop", command=pause_audio, width=25)
pauseOthButton = ttk.Button(
    window, text="Stop", command=pause_audio, width=25)


# progress bar
progress = ttk.Progressbar(window, orient=HORIZONTAL,
                           length=475, mode='determinate')

# Run audio separator button
runButton = ttk.Button(window, text="Run Audio Separator",
                       command=run_button, width=50)
runButton.grid(row=2, column=0, columnspan=2, padx=5, pady=5)


#  Listen to audio buttons
listenButtonVox = ttk.Button(
    window, text="Listen to Extracted Vocals", command=lambda m="vox": listen_extracted(m), width=25)
listenButtonBass = ttk.Button(
    window, text="Listen to Extracted Bass", command=lambda m="bass": listen_extracted(m), width=25)
listenButtonDrum = ttk.Button(
    window, text="Listen to Extracted Drums", command=lambda m="drum": listen_extracted(m), width=25)
listenButtonOth = ttk.Button(
    window, text="Listen to Extracted Other", command=lambda m="other": listen_extracted(m), width=25)


# Extract midi button
midiButtonVox = ttk.Button(window, text="Extract Vocal Midi",
                           command=lambda m="vox": midi_button(m), width=25)
midiButtonBass = ttk.Button(window, text="Extract Bass Midi",
                            command=lambda m="bass": midi_button(m), width=25)
midiButtonDrum = ttk.Button(window, text="Extract Drum Midi",
                            command=lambda m="drum": midi_button(m), width=25)
midiButtonOth = ttk.Button(window, text="Extract Other Midi",
                           command=lambda m="other": midi_button(m), width=25)


window.mainloop()

"""
@inproceedings{defossez2021hybrid,
               title = {Hybrid Spectrogram and Waveform Source Separation},
               author = {D{\'e}fossez, Alexandre},
               booktitle = {Proceedings of the ISMIR 2021 Workshop on Music Source Separation},
               year = {2021}
               }
@inproceedings{2022_BittnerBRME_LightweightNoteTranscription_ICASSP,
               author = {Bittner, Rachel M. and Bosch, Juan Jos\'e and Rubinstein, David and Meseguer-Brocal, Gabriel and Ewert, Sebastian},
               title = {A Lightweight Instrument-Agnostic Model for Polyphonic Note Transcription and Multipitch Estimation},
               booktitle = {Proceedings of the IEEE International Conference on Acoustics, Speech, and Signal Processing(ICASSP)},
               address = {Singapore},
               year = 2022,
               }
"""
