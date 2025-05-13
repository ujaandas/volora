from pocketsphinx import AudioFile

config = {
    'verbose': False,
    'audio_file': 'output2.wav',
    'buffer_size': 2048,
    'no_search': False,
    'full_utt': False,
}

audio = AudioFile(**config)
for phrase in audio:
    print(phrase)
