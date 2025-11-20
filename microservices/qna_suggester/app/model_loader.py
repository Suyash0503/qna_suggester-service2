from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# -----------------------------
# 1️⃣ Load model & tokenizer once at startup
# -----------------------------
MODEL_NAME = "MBZUAI/LaMini-Flan-T5-783M"

# Automatically use GPU if available, otherwise CPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[INFO] Using device: {DEVICE}")

# Load tokenizer & model
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(DEVICE)

# -----------------------------
# 2️⃣ Function: Generate from Flan-T5
# -----------------------------
def generate_from_flant5(prompt: str, max_tokens: int = 100) -> str:
    """
    Generate text output from the Flan-T5 model.
    :param prompt: Question or instruction for the model
    :param max_tokens: Number of new tokens to generate
    :return: Generated string output
    """
    try:
        # Tokenize input and move to device
        inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)

        # Generate with controlled randomness
        outputs = model.generate(
            inputs["input_ids"],
            max_new_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            num_return_sequences=1
        )

        # Decode output text
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return generated_text.strip()

    except Exception as e:
        return f"❌ Error generating text: {str(e)}"
