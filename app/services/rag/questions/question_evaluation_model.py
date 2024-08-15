import re
import gc
import torch
from typing import List, Dict
from transformers import BertTokenizer, BertForSequenceClassification
from app.config import logger

class QuestionEvaluator:
    def __init__(self, model_name: str = "bert-base-uncased"):
        """
        Initializes the QuestionEvaluator with a pre-trained BERT model for sentence classification.
        """
        try:
            self.tokenizer = BertTokenizer.from_pretrained(model_name)
            self.model = BertForSequenceClassification.from_pretrained(model_name)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            logger.info(f"QuestionEvaluator initialized with model: {model_name} on device: {self.device}")
        except Exception as e:
            logger.error(f"Error initializing QuestionEvaluator with model {model_name}: {e}")
            raise ValueError(f"Failed to load model or tokenizer with name {model_name}") from e

    async def evaluate_question(self, question: str) -> float:
        """
        Evaluate the question to determine its confidence score.

        Args:
            question (str): The question to evaluate.

        Returns:
            float: Confidence score between 0 and 1.
        """
        try:
            inputs = self.tokenizer(question, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Convert the logits to probabilities
            probabilities = torch.softmax(outputs.logits, dim=1).cpu().numpy()

            # Assuming the first label is 'bad' and the second is 'good'
            confidence_score = probabilities[0][1]  # Index [0][1] refers to the confidence for the 'good' class

            return float(confidence_score)

        except Exception as e:
            logger.error(f"Error evaluating question: {e}")
            raise ValueError("Failed to evaluate question confidence score") from e

    async def evaluate_questions(self, questions_str: str) -> List[Dict[str, str]]:
        """
        Splits the questions and assigns a question number and confidence score.

        Args:
            questions_str (str): The string containing all the questions.

        Returns:
            List[Dict[str, str]]: A list of dictionaries with question numbers, questions, and scores.
        """
        # Step 1: Split the string into individual questions
        split_pattern = r'\n\d+\.\s'  # Regex to split at "\n" followed by a number and a dot (e.g., "\n1. ")
        questions = re.split(split_pattern, questions_str.strip())
        
        # Step 2: Handle edge case where the first question starts without a preceding number
        if not questions[0].startswith("1."):
            questions = ["1. " + questions[0]] + questions[1:]
        
        # Step 3: Create a list of dictionaries with question number, question text, and confidence score
        categorized_questions = []
        for index, question in enumerate(questions, start=1):
            # Evaluate the confidence score for each question
            score = await self.evaluate_question(question.strip())
            
            categorized_questions.append({
                "question_no": index,
                "question": question.strip(),
                "score": float(score)
            })

        return categorized_questions
    
    async def combined_evaluation(self, questions_str: str) -> Dict[str, float]:
        """
        Evaluate the combined confidence score for a set of questions.

        Args:
            questions_str (str): The string containing all the questions.

        Returns:
            Dict[str, float]: The combined confidence score and the average score for the set of questions.
        """
        combined_score = await self.evaluate_question(questions_str)
        logger.info(f"Combined confidence score for questions: {combined_score}")
        categorized_questions = await self.evaluate_questions(questions_str)
        logger.info(f"Categorized questions: {categorized_questions}")

        questions = {
            "questions": categorized_questions,
            "average_score": sum([question["score"] for question in categorized_questions]) / len(categorized_questions),
            "combined_score": combined_score
        }
        logger.info(f"Questions with scores: {questions}")
        return questions
    
    def unload(self):
        """
        Unloads the model and tokenizer, freeing up memory.
        """
        try:
            del self.model
            del self.tokenizer
            if self.device == "cuda":
                torch.cuda.empty_cache()
            else:
                gc.collect()
            logger.info("QuestionEvaluator resources have been unloaded.")
        except Exception as e:
            logger.error(f"Error unloading QuestionEvaluator resources: {e}")
            raise
    
# Example Usage
if __name__ == "__main__":
    import asyncio

    async def main():
        questions_str = (
            "1. What is the significance of the name \"Willowbrook\" in the story?\n"
            "2. How does the character Ms. Evelyn influence the plot of \"The Willowbrook Chronicle\"?\n"
            "3. What secrets are hidden in the town of Willowbrook?\n"
            "4. How does the theme of eternity play out in the narrative?\n"
            "5. What role does the library play in the lives of the characters in the book?\n"
            "6. Can you describe the relationship between Hart and Ms. Evelyn in the story?\n"
            "7. What is the mystery surrounding the character known as \"The Stranger\"?\n"
            "8. How does the concept of life and remaining impact the characters' decisions in the novel?\n"
            "9. What kind of knowledge does the reader gain from exploring the secrets of Willowbrook?\n"
            "10. Why is the book placed on the shelf in the library, and what does it signify in the context of the story?"
        )

        evaluator = QuestionEvaluator()
        combined_score = await evaluator.combined_evaluation(questions_str)
        evaluator.unload()

        print(combined_score)

    # Run the example
    asyncio.run(main())
