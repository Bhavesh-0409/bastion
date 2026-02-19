import torch
import torch.nn.functional as F
from ml.model_loader import load_model

RISK_KEYWORDS = [
    "ignore previous",
    "system prompt",
    "internal safeguards",
    "disable safety",
    "bypass restrictions"
]

def evaluate(prompt: str):
    tokenizer, model, device = load_model()

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=128
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)

    confidence = torch.max(probs).item()
    predicted_id = torch.argmax(probs).item()
    predicted_label = model.config.id2label[predicted_id]

# Get probability of Benign class
    benign_id = model.config.label2id.get("Benign")
    benign_prob = probs[0][benign_id].item()

# Risk = probability that it is NOT benign
    risk_score = 1 - benign_prob

# Hybrid keyword boost
    lower_prompt = prompt.lower()
    for keyword in RISK_KEYWORDS:
        if keyword in lower_prompt:
            risk_score = min(risk_score + 0.1, 1.0)
            break

    return {
        "risk_score": float(risk_score),
        "violation_type": predicted_label,
        "confidence": float(confidence)
    }

