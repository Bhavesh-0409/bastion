import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

MODEL_PATH = "ml/saved_model"

device = torch.device("cpu")

_tokenizer = None
_model = None

def load_model():
    global _tokenizer, _model

    if _tokenizer is None or _model is None:
        _tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_PATH)
        _model = DistilBertForSequenceClassification.from_pretrained(
            MODEL_PATH
        )

        _model.to(device)
        _model.eval()

    return _tokenizer, _model, device
