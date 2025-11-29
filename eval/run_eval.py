"""
Q&A Evaluation Script

Evaluates RAG performance on the evaluation dataset.
"""

import json
import requests
import sys
from typing import List, Dict


class QAEvaluator:
    """Evaluates Q&A performance."""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.results = []
    
    def load_dataset(self, dataset_path: str) -> List[Dict]:
        """Load evaluation dataset."""
        with open(dataset_path, 'r') as f:
            return json.load(f)
    
    def evaluate_answer(self, answer: str, expected_keywords: List[str]) -> float:
        """
        Evaluate answer quality based on keyword presence.
        Returns score between 0 and 1.
        """
        answer_lower = answer.lower()
        matches = sum(1 for keyword in expected_keywords if keyword.lower() in answer_lower)
        score = matches / len(expected_keywords) if expected_keywords else 0.0
        return score
    
    def run_evaluation(self, dataset_path: str, document_mapping: Dict[str, int]):
        """
        Run evaluation on dataset.
        
        Args:
            dataset_path: Path to eval dataset JSON
            document_mapping: Mapping of document names to document IDs
                             e.g., {"nda.pdf": 1, "msa.pdf": 2}
        """
        dataset = self.load_dataset(dataset_path)
        
        total_score = 0.0
        total_questions = 0
        
        for item in dataset:
            question = item['question']
            doc_name = item['document_name']
            expected_keywords = item['expected_answer_keywords']
            
            # Get document IDs
            if doc_name == "all":
                document_ids = None  # Query all documents
            else:
                if doc_name not in document_mapping:
                    print(f"Skipping question {item['id']}: Document {doc_name} not found")
                    continue
                document_ids = [document_mapping[doc_name]]
            
            # Call API
            try:
                payload = {"question": question}
                if document_ids:
                    payload["document_ids"] = document_ids
                
                response = requests.post(
                    f"{self.api_base_url}/api/ask",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get('answer', '')
                    citations = data.get('citations', [])
                    
                    # Evaluate answer
                    score = self.evaluate_answer(answer, expected_keywords)
                    
                    result = {
                        'question_id': item['id'],
                        'question': question,
                        'answer': answer,
                        'expected_keywords': expected_keywords,
                        'score': score,
                        'citations_count': len(citations),
                        'has_citations': len(citations) > 0
                    }
                    
                    self.results.append(result)
                    total_score += score
                    total_questions += 1
                    
                    print(f"Q{item['id']}: {question[:50]}... Score: {score:.2f}")
                else:
                    print(f"Q{item['id']}: API Error {response.status_code}")
                    
            except Exception as e:
                print(f"Q{item['id']}: Exception: {e}")
        
        # Calculate final metrics
        avg_score = (total_score / total_questions) if total_questions > 0 else 0.0
        citation_rate = sum(1 for r in self.results if r['has_citations']) / total_questions if total_questions > 0 else 0.0
        
        summary = {
            'total_questions': total_questions,
            'average_score': round(avg_score, 3),
            'citation_rate': round(citation_rate, 3),
            'accuracy_threshold_0.5': sum(1 for r in self.results if r['score'] >= 0.5) / total_questions if total_questions > 0 else 0.0,
            'accuracy_threshold_0.7': sum(1 for r in self.results if r['score'] >= 0.7) / total_questions if total_questions > 0 else 0.0,
        }
        
        return summary
    
    def save_results(self, output_path: str, summary: Dict):
        """Save detailed results to JSON."""
        output = {
            'summary': summary,
            'detailed_results': self.results
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nResults saved to {output_path}")


def main():
    """Main evaluation function."""
    # This should be updated with actual document IDs after ingestion
    # For demo purposes, you would run this after uploading sample contracts
    document_mapping = {
        "nda.pdf": 1,
        "msa.pdf": 2,
        "saas.pdf": 3,
    }
    
    evaluator = QAEvaluator(api_base_url="http://localhost:8000")
    
    print("Starting Q&A Evaluation...")
    print("=" * 60)
    
    summary = evaluator.run_evaluation(
        dataset_path="eval/qa_eval_dataset.json",
        document_mapping=document_mapping
    )
    
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total Questions: {summary['total_questions']}")
    print(f"Average Score: {summary['average_score']:.1%}")
    print(f"Citation Rate: {summary['citation_rate']:.1%}")
    print(f"Accuracy ≥50%: {summary['accuracy_threshold_0.5']:.1%}")
    print(f"Accuracy ≥70%: {summary['accuracy_threshold_0.7']:.1%}")
    print("=" * 60)
    
    # One-line score summary
    print(f"\n📊 SCORE: {summary['average_score']:.1%} accuracy across {summary['total_questions']} questions")
    
    # Save results
    evaluator.save_results("eval/eval_results.json", summary)


if __name__ == "__main__":
    main()
