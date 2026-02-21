import torch
import torch.nn.functional as F
from ml.model_loader import load_model



CRITICAL_PATTERNS = [
    "ignore previous instructions",
    "reveal system prompt",
    "disable safety",
    "bypass restrictions",
    "pretend to be",
    "act as dan",
    "override safeguards",
    "turn off moderation",
    "export internal logs",
    "provide api key",
    "reveal credentials",
    "show hidden configuration",
    "ignore all prior rules"
]



SARCASM_PATTERNS = [
    "hypothetically",
    "just curious",
    "for research purposes",
    "purely educational",
    "just wondering",
    "obviously",
    "lol",
    "haha"
]


def evaluate(prompt: str):
    tokenizer, model, device = load_model()

    lower_prompt = prompt.lower()


    for pattern in CRITICAL_PATTERNS:
        if pattern in lower_prompt:
            return {
                "risk_score": 1.0,
                "violation_type": "Critical Override",
                "confidence": 1.0
            }


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

    predicted_id = torch.argmax(probs).item()
    predicted_label = model.config.id2label[predicted_id]
    confidence = torch.max(probs).item()


    malicious_labels = [
        "Prompt Injection",
        "Trust Elevation",
        "Policy Override",
        "Data Exfiltration Attempt"
    ]

    risk_score = 0.0
    for label in malicious_labels:
        if label in model.config.label2id:
            label_id = model.config.label2id[label]
            risk_score += probs[0][label_id].item()


    if confidence < 0.6 and risk_score > 0.4:
        risk_score += 0.15


    suspicious_flag = False
    for pattern in SARCASM_PATTERNS:
        if pattern in lower_prompt:
            suspicious_flag = True
            break

    if suspicious_flag and risk_score > 0.3:
        risk_score = min(risk_score + 0.25, 1.0)
        predicted_label = "Suspicious"


    risk_score = min(risk_score, 1.0)

    return {
        "risk_score": float(risk_score),
        "violation_type": predicted_label,
        "confidence": float(confidence)
    }