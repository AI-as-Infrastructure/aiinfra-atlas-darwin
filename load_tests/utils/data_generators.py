import random
from faker import Faker
from typing import List, Dict, Any

fake = Faker()

class DataGenerator:
    """Generate realistic test data for ATLAS load testing"""
    
    def __init__(self):
        # Darwin correspondence questions - focused on what would be discussed in letters
        self.darwin_questions = [
            "What did Darwin write about his doubts regarding species mutability?",
            "How did Darwin discuss his theory with other scientists before publication?",
            "What experiments did Darwin describe in his letters to colleagues?",
            "How did Darwin respond to criticisms of his evolutionary theory?",
            "What did Darwin write about the reception of On the Origin of Species?",
            "How did Darwin discuss his work on orchid fertilization with correspondents?",
            "What observations about plant movement did Darwin share in his letters?",
            "How did Darwin explain his ideas about sexual selection to other scientists?",
            "What did Darwin write about his correspondence with Alfred Russel Wallace?",
            "How did Darwin discuss his health problems in letters to friends?",
            "What experimental results did Darwin share with the scientific community?",
            "How did Darwin respond to religious objections to his theory?",
            "What did Darwin write about his work on climbing plants?",
            "How did Darwin discuss the problem of the eye in evolutionary theory?",
            "What questions did Darwin pose to his correspondents about animal behavior?",
            "How did Darwin explain variation under domestication to other scientists?",
            "What did Darwin write about his observations of earthworms?",
            "How did Darwin discuss the geological evidence for evolution?",
            "What challenges in his theory did Darwin acknowledge to correspondents?",
            "How did Darwin describe his method of collecting evidence?",
            "What did Darwin write about inheritance and variation?",
            "How did Darwin discuss the origin of moral sentiments?",
            "What experimental requests did Darwin make to his correspondents?",
            "How did Darwin explain his ideas about coral reef formation?",
            "What did Darwin write about plant hybridization experiments?",
            "How did Darwin discuss biogeographical distribution with colleagues?",
            "What observations about insect behavior did Darwin share?",
            "How did Darwin respond to questions about human evolution?",
            "What did Darwin write about his botanical investigations?",
            "How did Darwin discuss the struggle for existence with other naturalists?"
        ]
        
        # General questions about Darwin's thoughts and discussions in correspondence
        self.general_questions = [
            "What did Darwin think about scientific method?",
            "How did Darwin view the relationship between science and religion?",
            "What were Darwin's thoughts on scientific collaboration?",
            "How did Darwin approach experimental design?",
            "What did Darwin believe about the nature of scientific evidence?",
            "How did Darwin handle scientific disagreements?",
            "What were Darwin's views on publishing controversial ideas?",
            "How did Darwin discuss the importance of observation?",
            "What did Darwin think about the role of hypothesis in science?",
            "How did Darwin view the scientific community of his time?"
        ]
        
        # Intentionally sub-optimal questions for edge case testing (10% of questions)
        self.suboptimal_questions = [
            "What is evolution?",  # Too generic
            "Who was Darwin?",  # Overly simple
            "What is natural selection?",  # Basic concept without context
            "How did species change?",  # Vague question
            "What is science?",  # Too broad, not Darwin-specific
        ]
        
        self.feedback_comments = [
            "This answer was very helpful and accurate.",
            "The response could be more detailed.",
            "Excellent historical context provided.",
            "The information seems incomplete.",
            "Very relevant to my research needs.",
            "Could include more specific dates.",
            "Great breakdown of the parliamentary process.",
            "The answer was too general.",
            "Perfect for understanding the historical context.",
            "Would benefit from more examples."
        ]
        
        self.corpus_filters = [
            {"corpus": "darwin"},
            {"corpus": "all"}
        ]
    
    def generate_question_and_filter(self) -> tuple[str, str]:
        """Generate a question with its optimal filter for Darwin dataset testing"""
        # 10% chance for sub-optimal questions (for edge case testing)
        if random.random() < 0.1:
            question = random.choice(self.suboptimal_questions)
            # Random filter for sub-optimal questions to test mismatches
            filter_choice = random.choice(["darwin", "all"])
            return question, filter_choice
        
        # 90% optimal question-filter matching
        choice = random.random()
        if choice < 0.8:  # 80% Darwin-specific questions
            question = random.choice(self.darwin_questions)
            return question, "darwin"
        else:  # 20% general questions with "all" filter
            question = random.choice(self.general_questions)
            return question, "all"
    
    def generate_question(self) -> str:
        """Generate a realistic parliamentary question (backward compatibility)"""
        question, _ = self.generate_question_and_filter()
        return question
    
    def generate_custom_question(self) -> str:
        """Generate a more varied question using Faker"""
        topics = ["federation", "colonial administration", "tariff policy", "imperial relations", "land settlement", "mining", "railway construction", "labor disputes", "public works", "military defense", "public health", "education", "postal services", "Aboriginal affairs", "agricultural development", "banking", "women's suffrage", "immigration"]
        topic = random.choice(topics)
        
        patterns = [
            f"What did Parliament discuss about {topic} in 1901?",
            f"Can you find debates on {topic} policy in 1901?",
            f"How did the government address {topic} concerns in 1901?",
            f"What was the opposition's stance on {topic} legislation in 1901?",
            f"Can you provide details about {topic} discussions in 1901?"
        ]
        
        pattern = random.choice(patterns)
        return pattern
    
    def generate_session_id(self) -> str:
        """Generate a realistic session ID"""
        return fake.uuid4()
    
    def generate_qa_id(self) -> str:
        """Generate a realistic QA ID"""
        return fake.uuid4()
    
    def generate_corpus_filter(self) -> str:
        """Generate corpus filter parameters"""
        return random.choice(["all", "darwin"])
    
    def generate_feedback_data(self, qa_id: str, session_id: str, question: str = None, answer: str = None) -> Dict[str, Any]:
        """Generate feedback submission data matching actual UI format exactly"""
        
        # Generate realistic LLM response if not provided
        if not answer:
            answer = f"Based on parliamentary records, {random.choice(['the government', 'MPs', 'the opposition'])} discussed this matter extensively. Here are the key points: 1) Policy implementation required careful consideration, 2) Various stakeholders provided input, 3) The outcome reflected balanced decision-making."
        
        if not question:
            question = self.generate_question()
        
        # Match the EXACT UI feedback format from actual payload you provided
        data = {
            "session_id": session_id,
            "qa_id": qa_id,
            "trace_id": self.generate_qa_id(),
            "relevance": random.randint(1, 5),
            "factual_accuracy": random.choice(["true", "false", "mixed"]),  # UI uses "mixed" not just true/false
            "source_quality": random.randint(1, 5),
            "clarity": random.randint(1, 5),
            "question_rating": random.randint(1, 5),
            "user_category": random.choice(["General User", "Hansard Expert", "Digital HASS Researcher", "GLAM Practitioner"]),
            "tags": random.sample(["hallucination", "anachronism", "biased", "off-topic", "well-sourced"], k=random.randint(0, 3)),  # Can be empty
            "feedback_text": random.choice(self.feedback_comments),
            "model_answer": answer or "",
            "test_target": {},  # UI often sends empty object
            "question": question,
            "answer": answer,
            "citations": [],
            "timestamp": fake.iso8601()
        }
        
        return data
    
    def generate_ask_request(self, session_id: str = None) -> Dict[str, Any]:
        """Generate a complete ask request payload matching UI format exactly"""
        if not session_id:
            session_id = self.generate_session_id()
            
        # Use optimized question-filter matching
        question, corpus_filter = self.generate_question_and_filter()
        qa_id = self.generate_qa_id()
        
        # Match the exact UI request format
        request = {
            "question": question,
            "session_id": session_id,
            "qa_id": qa_id,
            "chat_history": [
                {
                    "role": "user",
                    "content": question
                }
            ],
            "corpus_filter": corpus_filter,
            "previous_corpus_filter": "all",
            "provider": "ANTHROPIC"
        }
        
        return request
    
    def generate_async_request(self, session_id: str = None) -> Dict[str, Any]:
        """Generate async processing request"""
        if not session_id:
            session_id = self.generate_session_id()
            
        return {
            "question": self.generate_question(),
            "session_id": session_id,
            "corpus_filter": self.generate_corpus_filter(),
            "priority": random.choice(["normal", "high"]),
            "callback_url": None  # For load testing, we don't need callbacks
        }
    
    def generate_user_scenario(self) -> Dict[str, Any]:
        """Generate a complete user interaction scenario"""
        session_id = self.generate_session_id()
        
        # Generate 1-3 questions per session
        num_questions = random.randint(1, 3)
        questions = []
        
        for _ in range(num_questions):
            qa_id = self.generate_qa_id()
            question_data = self.generate_ask_request(session_id)
            
            # Generate feedback for some questions (70% chance)
            feedback_data = None
            if random.random() < 0.7:
                # Pass question and generated answer for realistic feedback
                question_text = question_data.get("question", "")
                answer_text = f"Based on parliamentary records, this {random.choice(['policy', 'legislation', 'debate'])} involved {random.choice(['extensive', 'careful', 'thorough'])} consideration by {random.choice(['MPs', 'the government', 'committees'])}."
                feedback_data = self.generate_feedback_data(qa_id, session_id, question_text, answer_text)
            
            questions.append({
                "qa_id": qa_id,
                "question_data": question_data,
                "feedback_data": feedback_data
            })
        
        return {
            "session_id": session_id,
            "questions": questions,
            "user_type": random.choice(["researcher", "student", "journalist", "academic"])
        }

# Global instance for easy import
data_generator = DataGenerator()