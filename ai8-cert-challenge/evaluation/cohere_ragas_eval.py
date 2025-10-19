"""
Cohere RAGAS Evaluation Module
Uses manual questions to measure Cohere RAG performance metrics with RAGAS
Tests both standard retrieval and Cohere reranking
"""

import os
import sys
import json
from typing import List, Dict, Any
from pathlib import Path
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_api_keys():
    """Prompt user for API keys"""
    openai_key = os.getenv("OPENAI_API_KEY")
    cohere_key = os.getenv("COHERE_API_KEY")
    
    if not openai_key:
        print("🔑 OpenAI API Key Required")
        openai_key = input("Please enter your OpenAI API key: ").strip()
        if not openai_key:
            print("❌ OpenAI API key is required to run the evaluation")
            sys.exit(1)
    
    if not cohere_key:
        print("🔑 Cohere API Key Required")
        cohere_key = input("Please enter your Cohere API key: ").strip()
        if not cohere_key:
            print("❌ Cohere API key is required for reranking evaluation")
            sys.exit(1)
    
    # Set the environment variables
    os.environ["OPENAI_API_KEY"] = openai_key
    os.environ["COHERE_API_KEY"] = cohere_key
    print("✅ API keys set successfully!")
    return openai_key, cohere_key

# Get API keys before importing other modules
get_api_keys()

from app.agent import ask
from app.tools import ensure_prepared, AGENT_STATE
from app.data_processing import pdf_to_text
from config import PDF_DIR

class CohereRAGASEvaluator:
    def __init__(self, pdf_folder: str = PDF_DIR):
        self.pdf_folder = pdf_folder
        self.metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
        
    def generate_manual_questions(self) -> List[Dict[str, Any]]:
        """Generate 10 manual questions for evaluation"""
    
        return [
        {
            "question": "When is Unity Day?",
            "expected_answer": "Unity Day is on October 22nd, 2025. Students should wear orange.",
            "context": "Unity Day is the signature event of National Bullying Prevention Month."
        },
        {
            "question": "What events are happening on October 31st?",
            "expected_answer": "On October 31st, there are two events: Oak Halloween Parade at 9:00 AM and Oak Spooktacular from 2:30-4:40 PM.",
            "context": "Halloween events include parade and Spooktacular fundraiser."
        },
        {
            "question": "When is the PTA meeting?",
            "expected_answer": "The PTA Association Meeting is on November 5th at 7:00 PM in the Multi room.",
            "context": "PTA meeting scheduled for November 5th."
        },
        {
            "question": "What grade levels need vision screening?",
            "expected_answer": "Vision screening is for Kindergarten, 2nd grade, and 5th grade students on November 13th.",
            "context": "Vision screening scheduled for K, 2nd, and 5th grades."
        },
        {
            "question": "When is the Oak Chorus performance?",
            "expected_answer": "The Oak Chorus Performance is on November 14th from 12:50-1:30 PM in the Multi room.",
            "context": "Chorus performance scheduled for November 14th."
        },
        {
            "question": "What is the Spooktacular event?",
            "expected_answer": "The Oak Spooktacular is a fundraiser event on October 31st from 2:30-4:40 PM in the Multi room to support the 6th Grade graduation party.",
            "context": "Spooktacular fundraiser for 6th grade graduation party."
        },
        {
            "question": "When is picture retake day?",
            "expected_answer": "Picture Re-take Day is on October 22nd, 2025.",
            "context": "Picture retake day scheduled for October 22nd."
        },
        {
            "question": "What should students wear on Unity Day?",
            "expected_answer": "Students should wear orange on Unity Day.",
            "context": "Unity Day is about wearing orange for bullying prevention."
        },
        {
            "question": "Where is the Halloween parade?",
            "expected_answer": "The Oak Halloween Parade is on the blacktop at 9:00 AM on October 31st.",
            "context": "Halloween parade location is the blacktop."
        },
        {
            "question": "What time does the chorus performance start?",
            "expected_answer": "The Oak Chorus Performance starts at 12:50 PM on November 14th.",
            "context": "Chorus performance starts at 12:50 PM."
        }
    ]


    def prepare_data(self):
        """Prepare the agent data for evaluation"""
        print("🔄 Preparing data for evaluation...")
        ensure_prepared(self.pdf_folder)
        print(f"✅ Data prepared. Events loaded: {len(AGENT_STATE.get('all_events', []))}")
    
    def run_evaluation(self, use_reranking: bool = False) -> Dict[str, float]:
        """Run RAGAS evaluation on the agent with optional reranking"""
        
        # Prepare data
        self.prepare_data()
        
        # Generate manual questions for evaluation
        questions = self.generate_manual_questions()
        
        # Get agent responses
        method_name = "Cohere Reranking" if use_reranking else "Standard Retrieval"
        print(f"🤖 Getting agent responses using {method_name}...")
        agent_responses = []
        contexts = []
        
        for i, q in enumerate(questions):
            print(f"  Processing question {i+1}: {q['question'][:50]}...")
            response = ask(q['question'], self.pdf_folder, use_reranking=use_reranking)
            agent_responses.append(response)
            contexts.append([q['context']])
        
        # Create dataset for RAGAS evaluation
        dataset = Dataset.from_dict({
            "question": [q['question'] for q in questions],
            "answer": agent_responses,
            "contexts": contexts,
            "ground_truth": [q['expected_answer'] for q in questions]
        })
        
        print("📊 Running RAGAS evaluation...")
        
        # Run evaluation
        result = evaluate(
            dataset,
            metrics=self.metrics
        )
        
        # Extract scores (handle both single values and lists)
        def extract_score(score_data):
            if isinstance(score_data, list):
                return sum(score_data) / len(score_data)  # Average if it's a list
            return score_data
        
        scores = {
            "faithfulness": extract_score(result["faithfulness"]),
            "answer_relevancy": extract_score(result["answer_relevancy"]),
            "context_precision": extract_score(result["context_precision"]),
            "context_recall": extract_score(result["context_recall"])
        }
        
        return scores
    
    def compare_methods(self) -> Dict[str, Any]:
        """Compare standard retrieval vs Cohere reranking"""
        print("🔬 Comparing Standard Retrieval vs Cohere Reranking")
        print("=" * 60)
        
        # Test standard retrieval
        print("\n📊 Testing Standard Retrieval...")
        standard_scores = self.run_evaluation(use_reranking=False)
        
        # Test Cohere reranking
        print("\n🧠 Testing Cohere Reranking...")
        cohere_scores = self.run_evaluation(use_reranking=True)
        
        # Compare results
        comparison = {
            "standard_retrieval": standard_scores,
            "cohere_reranking": cohere_scores,
            "improvement": {}
        }
        
        print("\n📈 Performance Comparison:")
        print("-" * 40)
        
        for metric in standard_scores.keys():
            standard_val = standard_scores[metric]
            cohere_val = cohere_scores[metric]
            improvement = cohere_val - standard_val
            improvement_pct = (improvement / standard_val) * 100 if standard_val > 0 else 0
            
            comparison["improvement"][metric] = {
                "absolute": improvement,
                "percentage": improvement_pct
            }
            
            print(f"{metric.replace('_', ' ').title():<20}: {standard_val:.3f} → {cohere_val:.3f} ({improvement:+.3f}, {improvement_pct:+.1f}%)")
        
        return comparison
    
    def save_results(self, results: Dict[str, Any], filename: str = "cohere_evaluation_results.json"):
        """Save evaluation results to file"""
        results_path = Path(__file__).parent / filename
        
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved to: {results_path}")
        return results_path

def main():
    """Main evaluation function"""
    print("🧪 Cohere RAGAS Evaluation")
    print("=" * 50)
    
    evaluator = CohereRAGASEvaluator()
    
    # Run comparison
    results = evaluator.compare_methods()
    
    # Save results
    results_path = evaluator.save_results(results)
    
    print(f"\n🎉 Evaluation complete!")
    print(f"📊 Results saved to: {results_path}")
    
    # Print summary
    print("\n📋 Summary:")
    print("-" * 30)
    
    for metric, improvement in results["improvement"].items():
        direction = "📈" if improvement["percentage"] > 0 else "📉" if improvement["percentage"] < 0 else "➡️"
        print(f"{direction} {metric.replace('_', ' ').title()}: {improvement['percentage']:+.1f}%")

if __name__ == "__main__":
    main()
