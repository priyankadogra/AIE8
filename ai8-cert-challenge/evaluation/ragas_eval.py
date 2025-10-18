"""
RAGAS Evaluation Module
Uses manual questions to measure RAG performance metrics with RAGAS
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

def get_api_key():
    """Prompt user for OpenAI API key"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("🔑 OpenAI API Key Required")
        api_key = input("Please enter your OpenAI API key: ").strip()
        if not api_key:
            print("❌ API key is required to run the evaluation")
            sys.exit(1)
    
    # Set the environment variable
    os.environ["OPENAI_API_KEY"] = api_key
    print("✅ API key set successfully!")
    return api_key

# Get API key before importing other modules
get_api_key()

from app.agent import ask
from app.tools import ensure_prepared, AGENT_STATE
from app.data_processing import pdf_to_text
from config import PDF_DIR

class RAGASEvaluator:
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
    
    def run_evaluation(self) -> Dict[str, float]:
        """Run RAGAS evaluation on the agent"""
        
        # Prepare data
        self.prepare_data()
        
        # Generate manual questions for evaluation
        questions = self.generate_manual_questions()
        
        # Get agent responses
        print("🤖 Getting agent responses...")
        agent_responses = []
        contexts = []
        
        for i, q in enumerate(questions):
            print(f"  Processing question {i+1}: {q['question'][:50]}...")
            response = ask(q['question'], self.pdf_folder)
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
        
        return result
    
    def save_results(self, results, output_file: str = "evaluation_results.json"):
        """Save evaluation results to file"""
        
        output_path = Path("evaluation") / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        # Convert EvaluationResult to dictionary for JSON serialization
        results_dict = {}
        if hasattr(results, 'to_pandas'):
            df = results.to_pandas()
            
            # Only process columns that look like metrics (contain numeric data)
            for col in df.columns:
                try:
                    # Try to convert to numeric, skip if it fails
                    pd.to_numeric(df[col], errors='raise')
                    results_dict[col] = float(df[col].mean())
                except (ValueError, TypeError):
                    # Skip non-numeric columns (like questions, answers, etc.)
                    continue
        elif hasattr(results, '__dict__'):
            for attr in dir(results):
                if not attr.startswith('_') and not callable(getattr(results, attr)):
                    try:
                        value = getattr(results, attr)
                        if isinstance(value, (int, float)):
                            results_dict[attr] = float(value)
                    except:
                        pass
        
        with open(output_path, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        print(f"💾 Results saved to {output_path}")
    
    def print_results(self, results):
        """Print evaluation results in a nice format"""
        
        print("\n" + "="*50)
        print("📊 RAGAS EVALUATION RESULTS")
        print("="*50)
        
        # Handle EvaluationResult object
        if hasattr(results, 'to_pandas'):
            # Convert to pandas DataFrame for easier access
            df = results.to_pandas()
            
            # Only process columns that look like metrics (contain numeric data)
            metric_columns = []
            for col in df.columns:
                try:
                    # Try to convert to numeric, skip if it fails
                    pd.to_numeric(df[col], errors='raise')
                    metric_columns.append(col)
                except (ValueError, TypeError):
                    # Skip non-numeric columns (like questions, answers, etc.)
                    continue
            
            for metric in metric_columns:
                try:
                    score = df[metric].mean()
                    print(f"{metric:20}: {score:.3f}")
                except:
                    print(f"{metric:20}: Unable to calculate")
        elif hasattr(results, '__dict__'):
            # Try to access attributes directly
            for attr in dir(results):
                if not attr.startswith('_') and not callable(getattr(results, attr)):
                    try:
                        value = getattr(results, attr)
                        if isinstance(value, (int, float)):
                            print(f"{attr:20}: {value:.3f}")
                    except:
                        pass
        else:
            print("Unable to display results in expected format")
        
        print("="*50)
        
        # Interpretation
        print("\n📈 INTERPRETATION:")
        print("• Faithfulness: How factually accurate are the responses?")
        print("• Answer Relevancy: How relevant are responses to questions?")
        print("• Context Precision: How precise is the retrieved context?")
        print("• Context Recall: How well does the context cover the answer?")

def main():
    """Run RAGAS evaluation"""
    
    print("🚀 Starting RAGAS Evaluation...")
    
    # Create evaluator
    evaluator = RAGASEvaluator()
    
    # Run evaluation
    results = evaluator.run_evaluation()
    
    # Print results
    evaluator.print_results(results)
    
    # Save results
    evaluator.save_results(results)
    
    print("✅ RAGAS evaluation complete!")

if __name__ == "__main__":
    main()