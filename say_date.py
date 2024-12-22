from datetime import datetime
from pathlib import Path

import wave

import pyaudio
import numpy as np


def load_sounds(samples_dir, *dirs):
    data = {k: [] for k in dirs}
    for _dir in dirs:
        dpath = Path(samples_dir) / _dir
        for path in dpath.iterdir():
            if not path.suffix == '.wav':
                continue

            try:
                with wave.open(str(path.absolute()), 'rb') as sound_file:
                    data[_dir].append({
                        "params": sound_file.getparams(),
                        "frames": sound_file.readframes(sound_file.getnframes())
                    })
            except wave.Error as e:
                print(f"Error loading file {path}: {e}")

    return data


def get_time_based_indexes(_time: datetime):
    day = _time.timetuple().tm_mday - 1
    hour = _time.hour - 1
    minute = _time.minute
    month = _time.month - 1

    if minute % 10 == 1:
        minutes_noun = 2
    elif minute % 10 in [2, 3, 4] and (minute / 10) % 10 != 1:
        minutes_noun = 1
    else:
        minutes_noun = 0

    return day, month, hour, minute - 1, minutes_noun


def play_sound(sound_data):
    p = pyaudio.PyAudio()

    frames = sound_data["frames"]
    params = sound_data["params"]

    stream = p.open(format=p.get_format_from_width(params.sampwidth),
                    channels=params.nchannels,
                    rate=params.framerate,
                    output=True)

    stream.write(frames)

    stream.stop_stream()
    stream.close()

    p.terminate()


def trim_silence(audio_data, threshold=75):
    non_silent_indices = np.where(np.abs(audio_data) > threshold)[0]
    if non_silent_indices.size == 0:
        return b""
    start, end = non_silent_indices[0], non_silent_indices[-1]

    return audio_data[start:end + 1]


def crossfade(audio1, audio2, sr=44100, fade_duration_ms=50):
    if audio1 is None:
        return audio2

    if audio2 is None:
        return audio1

    fade_samples = int((fade_duration_ms / 1000) * sr)

    if fade_samples > len(audio1) or fade_samples > len(audio2):
        fade_samples = min(len(audio1), len(audio2))

    crossfaded = (
            audio1[-fade_samples:] + audio2[:fade_samples] / 2
    ).astype(np.int16)

    return np.concatenate([audio1[:-fade_samples], crossfaded, audio2[fade_samples:]])


def concatenate_samples(sample1, sample2, threshold=75):
    s1 = np.frombuffer(sample1['frames'], np.int16)
    s2 = np.frombuffer(sample2['frames'], np.int16)

    s1 = trim_silence(s1, threshold=threshold)
    s2 = trim_silence(s2, threshold=threshold)
    faded = crossfade(s1, s2, sr=sample1['params'].framerate)

    return {
        "params": sample1["params"],
        "frames": faded.tobytes()
    }


def add_tail(sample, tail_duration=0.2):
    data = np.frombuffer(sample['frames'], np.int16)
    tail = np.linspace(1, 0, int(tail_duration * sample['params'].framerate)).astype(np.int16)
    return {
        "params": sample["params"],
        "frames": np.concat([data, tail]).tobytes()
    }


root = Path('.').parent / 'samples'
data = load_sounds(root, 'days', 'hours', 'minutes', 'months', 'minute_nouns')

day, month, hour, minute, m_noun = get_time_based_indexes(datetime(2024, 2, 24, 13, 41).now())
phrase = concatenate_samples(data["days"][day], data["months"][month])
phrase = concatenate_samples(phrase, data["hours"][hour])
phrase = concatenate_samples(phrase, data["minutes"][minute])
phrase = concatenate_samples(phrase, data["minute_nouns"][m_noun])

phrase = add_tail(phrase, 0.2)

play_sound(phrase)

