"""
An ear is a thing that hears and classifies. This module handles inference for our audio model for classifying sounds. 
"""

from typing import BinaryIO

from speechbrain.inference.classifiers import EncoderClassifier
import torchaudio
import torch
import tempfile
from pydub import AudioSegment
from labear_api.brain import Brains

default_classifier = EncoderClassifier.from_hparams(source="speechbrain/urbansound8k_ecapa", savedir="models/gurbansound8k_ecapa")    

brains = Brains()

def load_audio(file: BinaryIO, format: str):
    """
    This implementation copies EncoderClassifier.load_audio, but accepts a binary file 
    object instead of a file path.
    """
    signal, sr = None, None
            
    with tempfile.TemporaryFile() as tp:
        audio = AudioSegment.from_file(file, format=format)
        audio = audio[500:] # Remove first 0.5 second to omit blank signal at beginning of recording
        audio.export(tp, format='wav')
        
        signal, sr = torchaudio.load(tp, channels_first=False)
    return signal, sr

def predict(user: str, in_file: BinaryIO, format: str):
    """
    This implemetation copies EncoderClassifier.classify_file, but accepts a binary file 
    object instead of a file path.
    """
    pretrained_only = False
    classifier, cats = brains.brain(user) # gets a specific brain (classifier) associated with user
    if classifier is None:
        classifier = default_classifier
        pretrained_only = True
    signal, sr = load_audio(in_file, format)
    waveform = classifier.audio_normalizer(signal, sr)
    batch = waveform.unsqueeze(0)
    rel_length = torch.tensor([1.0])
    emb = classifier.eval().encode_batch(batch, rel_length)
    probs = classifier.eval().mods.classifier(emb).squeeze()
    score, index = torch.max(probs, dim=-1)
    if pretrained_only:
        prediction = classifier.hparams.label_encoder.decode_torch(torch.tensor([index]))
        # Build a dictionary like {classname: probability} from tensor of probabilities
        # using the classifier's index to label dict 
        probabilities = {classifier.hparams.label_encoder.ind2lab[i]: prob for i, prob in enumerate(probs.tolist())}
    else:
        prediction = [cats[index]]
        probabilities = {cats[i]: prob for i, prob in enumerate(probs.tolist())}
    return probabilities, prediction, score

if __name__ == "__main__":
    print("Running main")