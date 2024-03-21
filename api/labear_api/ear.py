"""
An ear is a thing that hears and classifies. This module handles inference for our audio model for classifying sounds. 
"""

from typing import BinaryIO

from speechbrain.inference.classifiers import EncoderClassifier
import torchaudio
import torch

classifier = EncoderClassifier.from_hparams(source="speechbrain/urbansound8k_ecapa", savedir="models/gurbansound8k_ecapa")    

def load_audio(file: BinaryIO):
    """
    This implementation copies EncoderClassifier.load_audio, but accepts a binary file 
    object instead of a file path.
    """
    signal, sr = torchaudio.load(file, channels_first=False)
    return classifier.audio_normalizer(signal, sr)

def predict(in_file: BinaryIO):
    """
    This implemetation copies EncoderClassifier.classify_file, but accepts a binary file 
    object instead of a file path.
    """
    waveform = load_audio(in_file)
    batch = waveform.unsqueeze(0)
    rel_length = torch.tensor([1.0])
    emb = classifier.encode_batch(batch, rel_length)
    out_probs = classifier.mods.classifier(emb).squeeze(1)
    score, index = torch.max(out_probs, dim=-1)
    classname = classifier.hparams.label_encoder.decode_torch(index)
    return out_probs, score, index, classname

def make_probabilities(probs):
    """
    Builds a dictionaru like {classname: probability} from a tensor of probabilities, given the label 
    encoder of the classifier
    """
    return {classifier.hparams.label_encoder.__dict__['ind2lab'][i]: prob for i, prob in enumerate(probs.tolist())}