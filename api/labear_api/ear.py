"""
An ear is a thing that hears and classifies. This module handles inference for our audio model for classifying sounds. 
"""

from typing import BinaryIO

from speechbrain.inference.classifiers import EncoderClassifier
import torchaudio
import torch
import tempfile
from pydub import AudioSegment
classifier = EncoderClassifier.from_hparams(source="speechbrain/urbansound8k_ecapa", savedir="models/gurbansound8k_ecapa")    

def load_audio(file: BinaryIO):
    """
    This implementation copies EncoderClassifier.load_audio, but accepts a binary file 
    object instead of a file path.
    """
    signal, sr = None, None
    with tempfile.TemporaryFile() as tp:
        audio = AudioSegment.from_file(file, format='m4a')
        audio.export(tp, format='wav')
        signal, sr = torchaudio.load(tp, channels_first=False)
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
    probs = classifier.mods.classifier(emb).squeeze()
    score, index = torch.max(probs, dim=-1)
    prediction = classifier.hparams.label_encoder.decode_torch(torch.tensor([index]))
    # Build a dictionary like {classname: probability} from tensor of probabilities
    # using the classifier's index to label dict 
    probabilities = {classifier.hparams.label_encoder.ind2lab[i]: prob for i, prob in enumerate(probs.tolist())}
    return probabilities, prediction, score