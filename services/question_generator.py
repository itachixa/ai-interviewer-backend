import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
from typing import List
import os


class InterviewQuestionGenerator:
    """Classe pour generer des questions d'entretien a partir d'un CV"""
    
    def __init__(self, model_path: str = "./saved_model"):
        """
        Initialise le generateur de questions
        
        Args:
            model_path: Chemin vers le dossier du modele sauvegarde
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Verifier si le modele existe
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Le modele n'existe pas dans: {model_path}")
        
        self.tokenizer = T5Tokenizer.from_pretrained(model_path)
        self.model = T5ForConditionalGeneration.from_pretrained(model_path)
        self.model = self.model.to(self.device)
        self.model.eval()
        print(f"Modele charge sur: {self.device}")
    
    def generate(self, cv_text: str, max_questions: int = 10) -> List[str]:
        """
        Genere des questions d'entretien a partir d'un CV
        
        Args:
            cv_text: Texte du CV
            max_questions: Nombre maximum de questions a generer
        
        Returns:
            Liste de questions d'entretien
        """
        # Preparer l'entree avec le prompt
        input_text = "Generate interview questions from this resume: " + cv_text
        
        # Tokenizer l'entree
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            max_length=512,
            truncation=True
        ).to(self.device)
        
        # Generer les questions
        with torch.no_grad():
            outputs = self.model.generate(
                inputs["input_ids"],
                max_length=256,
                num_beams=4,
                no_repeat_ngram_size=2,
                early_stopping=True
            )
        
        # Decoder la sortie
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Parser les questions (separees par des points)
        questions = []
        for q in generated_text.split("."):
            q = q.strip()
            if q and len(q) > 10:  # Filtrer les questions trop courtes
                questions.append(q + "?")
                if len(questions) >= max_questions:
                    break
        
        return questions


# Instance globale du generateur (charge au demarrage)
question_generator = None


def get_question_generator(model_path: str = "./saved_model") -> InterviewQuestionGenerator:
    """
    Recupere l'instance du generateur de questions
    
    Args:
        model_path: Chemin vers le modele
    
    Returns:
        Instance du generateur de questions
    """
    global question_generator
    if question_generator is None:
        question_generator = InterviewQuestionGenerator(model_path)
    return question_generator
