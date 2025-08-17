def load_ocr_corrections(filepath):
    corrections = {}
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=>" in line:
                wrong, correct = line.split("=>", 1)
            elif "=" in line:
                wrong, correct = line.split("=", 1)
            else:
                continue
            corrections[wrong.strip()] = correct.strip()
    return corrections

def correct_ocr_text(text, corrections):
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    return text