# Synthetic creation of positive files
# Add gong sound to negative files in different positions - shift by 100ms
# Save file

# Research:
# https://stackoverflow.com/questions/60918209/pydub-overlay-delay
# https://snyk.io/advisor/python/pydub/functions/pydub.AudioSegment
# https://stackoverflow.com/questions/4039158/mixing-two-audio-files-together-with-python

import os
from pydub import AudioSegment


def create_pos_dataset(path):
    directory_neg = os.fsencode(path)
    filename_gong = AudioSegment.from_wav(path + '/gong_ber/1-EW8678-n-Heraklion_Boarding-beginnt_de,en_2022_goodquality.wav')
    pos = 0
    for file in os.listdir(directory_neg):
        # the position parameter means where on the original sound do you wish to start.
        filename_neg = os.fsdecode(file)
        if filename_neg.endswith(".wav") and pos < 4000:
            print("Filename negative: " + filename_neg)
            print("Filename Gong: 1-EW8678-n-Heraklion_Boarding-beginnt_de,en_2022_goodquality.wav")
            print("Position of gong start: ", pos)
            file_neg = AudioSegment.from_wav(path + filename_neg)
            filename_pos_with_ambient = file_neg.overlay(filename_gong, position=pos)
            mono_pos = filename_pos_with_ambient.split_to_mono()
            #os.mkdir(path + "overlays/")
            mono_pos[1].export(path + "overlays_mono/" + "gong_mono_" + str(pos) + "_" + filename_neg, format="wav")

            pos += 500

        elif filename_neg.endswith(".wav") and pos == 4000:
            pos = 0

        if len(os.listdir("/Users/annikaschilk/Documents/techlabs/overlays_mono")) == 1145:
            break


def create_neg_dataset(path):
    directory_neg = os.fsencode(path)
    for file in os.listdir(directory_neg):
        filename_neg = os.fsdecode(file)
        if filename_neg.endswith(".wav"):
            file_neg = AudioSegment.from_wav(path + filename_neg)
            mono_neg = file_neg.split_to_mono()
            mono_neg[1].export(path + "mono_" + "_" + filename_neg, format="wav")


def main():
    print(len(os.listdir("/Users/annikaschilk/Documents/techlabs/")))
    create_pos_dataset("/Users/annikaschilk/Documents/techlabs/")
    create_neg_dataset("/Users/annikaschilk/Documents/techlabs/overlays_mono/")

    # data used in this model: https://colab.research.google.com/drive/1r2EFf-oF5TG4EeE4RLaLxPdFRnPoJsYh?usp=sharing
    # result: more promising approaches were continued

if __name__ == '__main__':
    main()