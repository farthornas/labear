"""
An ear is a thing that hears and classifies. This module handles inference for our audio model for classifying sounds. 
"""

from typing import BinaryIO

from speechbrain.inference.classifiers import EncoderClassifier
import torchaudio
import torch
import tempfile
from pydub import AudioSegment
from labear_api.cloud_connect import download_blob
from google.api_core.exceptions import NotFound


CLASSIFIER_PATH = "data/"
CLASSIFIER_NAME = "fine_tuned.pt"


def load_classifier(user: str):
    """
    Attempt to load a finetuned classifier for a user. 
    If the user is not registered the classifier speechbrain/urbansound8k_ecapa will be used
    """
    path = CLASSIFIER_PATH + user + "/" + CLASSIFIER_NAME
    try:
        classifier = torch.load(path)
    except FileNotFoundError as e:
        print(f"Could not load classifier locally, will try to download classifier...")
        gc_path = user + "/" + CLASSIFIER_NAME
        download_blob(bucket_name="data_labear", source_blob_name=gc_path, destination_file_name=path)
    except NotFound:
        print(f"No classifier available for user: {user}. Reverting to using classifier: speechbrain/urbansound8k_ecapa")
        classifier = EncoderClassifier.from_hparams(source="speechbrain/urbansound8k_ecapa", savedir="models/gurbansound8k_ecapa")    
    else:
        classifier = torch.load(path)
    
    return classifier

def load_audio(file: BinaryIO):
    """
    This implementation copies EncoderClassifier.load_audio, but accepts a binary file 
    object instead of a file path.
    """
    signal, sr = None, None
    with tempfile.TemporaryFile() as tp:
        audio = AudioSegment.from_file(file, format='m4a')
        audio.export(tp, format='wav')
    return torchaudio.load(tp, channels_first=False)

def predict(user: str, in_file: BinaryIO):
    """
    This implemetation copies EncoderClassifier.classify_file, but accepts a binary file 
    object instead of a file path.
    """
    classifier = load_classifier(user)
    signal, sr = load_audio(in_file)
    waveform = classifier.audio_normalizer(signal, sr)
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