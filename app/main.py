from AudioHelper import AudioHelper


def main():
    audio = AudioHelper()
    sound = audio.record(3)
    audio.play(sound)


if __name__ == "__main__":
    main()
