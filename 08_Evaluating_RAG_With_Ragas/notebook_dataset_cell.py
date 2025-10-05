# Dataset Save/Load Functionality
# Copy this code into your notebook cells

# Import the dataset manager
from dataset_manager import save_ragas_dataset, load_ragas_dataset, list_ragas_datasets

# ========================================
# CELL 1: Generate and Save Dataset (run this once)
# ========================================

# Load documents (assuming you have docs loaded)
# path = "data/"
# loader = DirectoryLoader(path, glob="*.pdf", loader_cls=PyMuPDFLoader)
# docs = loader.load()

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

# ========================================
# CELL 2: Load Saved Dataset (use this for future runs)
# ========================================

# Check what datasets are available
print("Available datasets:")
datasets = list_ragas_datasets()
for dataset in datasets:
    print(f"  - {dataset}")

# Load the saved dataset
try:
    dataset = load_ragas_dataset("loan_data_evaluation")
    print(f"Dataset loaded! Contains {len(dataset)} samples")
except FileNotFoundError:
    print("No saved dataset found. Please generate one first.")

# ========================================
# CELL 3: Quick Save/Load Pattern
# ========================================

# This pattern checks if dataset exists, loads it if it does, generates if it doesn't

def get_or_generate_dataset(dataset_name="loan_data_evaluation", force_regenerate=False):
    """Get existing dataset or generate new one."""
    
    if not force_regenerate:
        try:
            # Try to load existing dataset
            dataset = load_ragas_dataset(dataset_name)
            print(f"Loaded existing dataset: {dataset_name}")
            return dataset
        except FileNotFoundError:
            print(f"No existing dataset found: {dataset_name}")
    
    # Generate new dataset
    print("Generating new dataset...")
    
    # Your existing generation code here
    generator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4"))
    generator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
    
    generator = TestsetGenerator(llm=generator_llm, embedding_model=generator_embeddings)
    dataset = generator.generate_with_langchain_docs(docs, testset_size=10)
    
    # Save the new dataset
    save_ragas_dataset(dataset, dataset_name)
    print(f"Dataset saved as: {dataset_name}")
    
    return dataset

# Use the function
dataset = get_or_generate_dataset()

# ========================================
# CELL 4: Dataset Information
# ========================================

# Display dataset information
print(f"Dataset contains {len(dataset)} samples")
print("\nSample questions:")
for i, sample in enumerate(dataset[:3]):
    print(f"{i+1}. {sample.eval_sample.user_input}")

# Convert to pandas for inspection
df = dataset.to_pandas()
print(f"\nDataset columns: {list(df.columns)}")
print(f"First few rows:")
print(df.head())
