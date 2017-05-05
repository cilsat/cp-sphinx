#!/usr/bin/env python

import os
import argparse
import pysox
import numpy as np
from multiprocessing import Pool, cpu_count

parser = argparse.ArgumentParser(description="Prepare audio files for Sphinx training")
parser.add_argument("wav_dir", help="Path to directory containing training WAVs")
parser.add_argument("etc_dir", help="Path to sphinxtrain etc directory")
parser.add_argument("-n", "--nrand", type=int, default=0, help="Number of random WAVs to generate for each training WAV. Defaults to 0, in which augmentation is absent")
parser.add_argument("-t", "--test_size", type=int, default=16, help="Proportion of data in wav_dir used for testing")
args = parser.parse_args()

# Specify effects to use for augmentation and the range of values they can take
effects = {"tempo":[0.75, 1.25], "tremolo":[25, 55], "bend":[-250, 250],
        "vol":[0.5, 1.5]}


def main():
    wavs = [w for w in sorted(os.listdir(args.wav_dir)) if w.find('rand_') == -1]
    names = [w.split('.')[0] for w in wavs]

    if args.nrand > 0:
        with Pool(cpu_count()) as p:
            rands = p.starmap(augment, zip([n for n in names], [args.nrand]*len(names)))
        names.extend([n for r in rands for n in r])

    fileids = ["rinal/" + n for n in names]
    transcription = ["<s> " + n.split('_')[0] + " </s> (rinal/" + n + ")" for n in names]

    ts = args.test_size
    with open(os.path.join(args.etc_dir, 'cp-sphinx_train.fileids'), 'w') as f:
        [f.write("rinal/" + n + "\n")
                for n in names if int(n.split('_')[1]) < ts]
    with open(os.path.join(args.etc_dir, 'cp-sphinx_train.transcription'), 'w') as f:
        [f.write("<s> " + n.split('_')[0] + " </s> (rinal/" + n + ")\n")
                for n in names if int(n.split('_')[1]) < ts]
    with open(os.path.join(args.etc_dir, 'cp-sphinx_test.fileids'), 'w') as f:
        [f.write("rinal/" + n + "\n")
                for n in names if int(n.split('_')[1]) >= ts]
                #for n in names if n.find('rand') == -1 and int(n.split('_')[1]) >= ts]
    with open(os.path.join(args.etc_dir, 'cp-sphinx_test.transcription'), 'w') as f:
        [f.write("<s> " + n.split('_')[0] + " </s> (rinal/" + n + ")\n")
                for n in names if int(n.split('_')[1]) >= ts]
                #for n in names if n.find('rand') == -1 and int(n.split('_')[1]) >= ts]


def augment(name, num):
    infile = pysox.CSoxStream(os.path.join(args.wav_dir, name) + ".wav")
    info = infile.get_signal().get_signalinfo()
    length = info['length']/info['rate']

    names = [name + "_rand_" + str(n).zfill(2) for n in range(1, num+1)]
    for n in names:
        infile = pysox.CSoxStream(os.path.join(args.wav_dir, name) + ".wav")
        outfile = pysox.CSoxStream(os.path.join(args.wav_dir, n) + ".wav",
                'w', pysox.CSignalInfo(16000.0,1,16))
        chain = pysox.CEffectsChain(infile, outfile)

        # Pitch bend
        b = np.random.ranf()*0.5*length + 0.15*length
        p = np.random.randint(-250, 250)
        bend = pysox.CEffect("bend", [bytes(str(b)+','+str(p)+','+str(length - b - 0.01), 'utf-8')])
        chain.add_effect(bend)

        # Tremolo
        s = np.random.randint(2,5)/length
        d = np.random.randint(30, 80)
        tremolo = pysox.CEffect("tremolo", [bytes(str(s), 'utf-8'),
            bytes(str(d), 'utf-8')])
        chain.add_effect(tremolo)

        # Tempo
        t = np.random.randint(6,14)*0.1
        tempo = pysox.CEffect("tempo", [b'-s', bytes(str(t), 'utf-8')])
        chain.add_effect(tempo)

        # Gain
        g = np.random.ranf()*1.25 + 0.25
        vol = pysox.CEffect("vol", [bytes(str(g), 'utf-8')])
        chain.add_effect(vol)

        try:
            chain.flow_effects()
        except:
            print(n, b, length)
        outfile.close()

    infile.close()
    return names


if __name__ == "__main__":
    main()
