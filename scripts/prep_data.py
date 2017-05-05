#!/usr/bin/env python

import os
import argparse
import pysox

parser = argparse.ArgumentParser(description="Prepare audio files for Sphinx training")
parser.add_argument("train_dir", help="Path to directory containing training WAVs")
parser.add_argument("test_dir", help="Path to directory containing testing WAVs")
parser.add_argument("etc_dir", help="Path to sphinxtrain etc directory")
parser.add_argument("-n", "--nrand", type=int, default=0, help="Number of random WAVs to generate for each training WAV. Defaults to 0, in which augmentation is absent")
args = parser.parse_args()

def main():
    for wav in sorted(os.listdir(args.train_dir)):
        name = wav.split('.')[0]
        names = augment(name, args.nrand) if args.nrand > 0 else [name]
        word = wav.split('_')[0]
        fileid = ["rinal/" + n for n in names]
        transcript = ["<s> " + word + " </s> (" + n + ")"
                for n in fileid]


def augment(name, num):
    names = [name + "_rand_" + str(n).zfill(2)
            for n in range(1, num+1)]
    infile = pysox.CSoxStream(os.path.join(args.train_dir, name))
    signal = infile.get_signal()
    for n in names:
        outfile = pysox.CSoxStream(os.path.join(args.train_dir, n) + ".wav",
                'w', signal)


    return [name]+names


if __name__ == "__main__":
    main()
