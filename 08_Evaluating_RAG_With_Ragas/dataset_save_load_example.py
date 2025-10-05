"""
Example: Save and Load Ragas Dataset

This example shows how to save a generated dataset and load it later
to avoid regenerating it every time.
"""

from dataset_manager import save_ragas_dataset, load_ragas_dataset, list_ragas_datasets, DatasetManager
from ragas.testset import TestsetGenerator
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader


def generate_and_save_dataset():
    """Generate a dataset and save it for future use."""
    
    # Load documents
    path = "data/"
    loader = DirectoryLoader(path, glob="*.pdf", loader_cls=PyMuPDFLoader)
    docs = loader.load()
    
    # Set up generators
    generator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4"))
    generator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
    
    # Generate dataset
    print("Generating synthetic dataset...")
    generator = TestsetGenerator(llm=generator_llm, embedding_model=generator_embeddings)
    dataset = generator.generate_with_langchain_docs(docs, testset_size=10)
    
    # Save dataset with metadata
    metadata = {
        "testset_size": 10,
        "generator_model": "gpt-4",
        "embedding_model": "text-embedding-3-small",
        "num_source_docs": len(docs),
        "generation_date": "2025-01-27"
    }
    
    save_ragas_dataset(dataset, "loan_data_evaluation", metadata=metadata)
    print("Dataset saved successfully!")
    
    return dataset


def load_saved_dataset():
    """Load a previously saved dataset."""
    
    try:
        # Try to load the saved dataset
        dataset = load_ragas_dataset("loan_data_evaluation")
        print("Dataset loaded successfully!")
        return dataset
    
    except FileNotFoundError:
        print("No saved dataset found. Generating new one...")
        return generate_and_save_dataset()


def main():
    """Main function demonstrating dataset save/load functionality."""
    
    # Check what datasets are available
    print("Available datasets:")
    datasets = list_ragas_datasets()
    if datasets:
        for dataset in datasets:
            print(f"  - {dataset}")
    else:
        print("  No saved datasets found")
    
    print("\n" + "="*50)
    
    # Load or generate dataset
    dataset = load_saved_dataset()
    
    # Display dataset info
    print(f"\nDataset contains {len(dataset)} samples")
    print("Sample questions:")
    for i, sample in enumerate(dataset[:3]):
        print(f"{i+1}. {sample.eval_sample.user_input}")
    
    return dataset


if __name__ == "__main__":
    dataset = main()
