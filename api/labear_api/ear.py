"""
An ear is a thing that hears and classifies. This module handles inference for our audio model for classifying sounds. 
"""

from typing import BinaryIO
from speechbrain.inference.classifiers import EncoderClassifier

classifier = EncoderClassifier.from_hparams(source="speechbrain/urbansound8k_ecapa", savedir="models/gurbansound8k_ecapa")

from contextlib import contextmanager
import os

@contextmanager
def temporary_file():
    try:
        tmp_path = "audioin.wav"
        yield tmp_path
    finally:
        os.remove(tmp_path)

def predict(in_file: BinaryIO):
    with temporary_file() as tmp_path:
        with open(tmp_path, "wb") as f:
            f.write(in_file.read())
        out_prob, score, index, class_name = classifier.classify_file(tmp_path)
    return class_name