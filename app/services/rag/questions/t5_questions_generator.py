# /app/services/rag/t5_questions_generator.py

from transformers import RagTokenizer, RagTokenForGeneration
import torch
import gc

def minimal_rag_example():
    try:
        # Initialize the tokenizer and model
        model_name = "facebook/rag-token-nq"
        tokenizer = RagTokenizer.from_pretrained(model_name)
        model = RagTokenForGeneration.from_pretrained(model_name)
        
        # Prepare a simple input
        context = "What is the capital of France?"
        input_ids = tokenizer(context, return_tensors="pt").input_ids
        
        # Move input to GPU if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        input_ids = input_ids.to(device)
        model.to(device)

        # Generate output
        outputs = model.generate(input_ids=input_ids)
        
        # Decode and print the output
        questions = [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]
        print("Generated Questions:", questions)
        del model
        del tokenizer
        gc.collect()
    except Exception as e:
        del model
        del tokenizer
        gc.collect()
        print(f"Error: {e}")

from transformers import T5Tokenizer, T5ForConditionalGeneration

def t5_question_generation_example():
    try:
        model_name = "t5-base"
        tokenizer = T5Tokenizer.from_pretrained(model_name)
        model = T5ForConditionalGeneration.from_pretrained(model_name)

        context = "Flat No. 12060, 12th Floor, Tower 1, XYZ Apartments, New Delhi, India"
        input_text = f"generate questions: {context}"
        input_ids = tokenizer(input_text, return_tensors="pt").input_ids

        outputs = model.generate(input_ids=input_ids, max_length=50, num_beams=4, early_stopping=True)
        print("Raw Outputs:", outputs)
        questions = [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]

        print("Generated Questions:", questions)
        del model
        del tokenizer
        gc.collect()
    except Exception as e:
        del model
        del tokenizer
        gc.collect()
        print(f"Error: {e}")

if __name__ == "__main__":
    t5_question_generation_example()


if __name__ == "__main__":
    minimal_rag_example()


