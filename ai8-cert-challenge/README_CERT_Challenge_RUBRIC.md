# Defining your Problem and Audience

### Write a succinct 1-sentence description of the problem
Parents get flooded with school emails and newsletters; important dates (minimum days, picture day, field trips, spirit days, PTA meetings) get buried. Manually copying them is error-prone and time consuming.

### Write 1-2 paragraphs on why this is a problem for your specific user
Parents today are overwhelmed by the flood of school communication — weekly newsletters, classroom reminders, PTA announcements, event flyers, and emails from multiple teachers. Important details like “Picture Day is next Thursday” or “Bring cash for the field trip” are buried inside long messages that arrive at odd times. Even the most organized parent can miss a date or instruction, leading to last-minute stress, forgotten deadlines, or disappointed kids.

## Propose a Solution
### Propose a Solution
The problem Scout solves is simple but powerful: it acts as a friendly chatbot that makes sense of the constant stream of unstructured school updates parents receive. Instead of reading every long email or newsletter, parents can simply ask Scout questions like “When is Spirit Day?” or “Do I need to bring anything tomorrow?” and get quick, accurate answers pulled straight from their school’s communications. By turning messy inboxes into clear, conversational insights, Scout takes the mental load out of staying on top of school logistics — helping parents feel organized, confident, and focused on their family instead of their emails.

### Describe the tools you plan to use in each part of your stack.  Write one sentence on why you made each tooling choice.
Streamlit - It is a lightwigth python UI library and provides a clean and interactive chat interface that is perfect for conversational AI.
OpenAI GPT-4o-mini: I selected this modal as it has excellent reasoning capabilities for understanding user queries and generating responses while also being cost-effective.
OpenAI text-embedding-3-small: I chose this embedding model because it provides high-quality semantic search capabilities.
Qdrant: I selected Qdrant as the vector database because it offers fast similarity search, in-memory storage for quick prototyping, and seamless integration with embedding models for efficient document retrieval.
Cohere Rerank: I integrated Cohere's reranking API because it significantly improves retrieval quality by reordering search results based on semantic relevance to the query, leading to more accurate answers.
RAGAS: I used RAGAS for evaluation because it provides comprehensive metrics (faithfulness, answer relevancy, context precision, context recall) to objectively measure and compare RAG system performance.
LangChain: I chose LangChain for agent orchestration because it provides a robust framework for building conversational AI agents with tool integration and structured reasoning capabilities.
PyPDF: I selected PyPDF for PDF processing because it reliably extracts text from school newsletters and documents while maintaining formatting and handling various PDF structures.

### Where will you use an agent or agents?  What will you use “agentic reasoning” for in your app?


## Dealing with the Data
### Describe all of your data sources and external APIs, and describe what you’ll use them for.
The data is sent by the school via email. I copied 4 emails into PDF files for now to test my application. I had initially planned to connect my email and possibly using the the langchain gmail api to connect to the email. I willdo that for the final demo.

### Describe the default chunking strategy that you will use.  Why did you make this decision?
I used an 800 character chunk size with 100 character overly. 500 - 100 character chunking is usually the best chunking size. The chunking also take the senetence boundaries into consideration and tries to preserve the entire senetence vs breaking up thoughts mid-sentence.
This balances granularity (small enough for precise retrieval) with context preservation (large enough to maintain meaning), while the sentence boundary detection ensures chunks contain complete thoughts rather than fragmented text, leading to better semantic search results and more coherent retrieved information for the LLM to process.
### [Optional] Will you need specific data for any other part of your application?   If so, explain.
No other data needed right now, but I was thinking of possibly building something similar for scraping the school site as well for demo day.

## Building a Quick End-to-End Prototype
### Build an end-to-end prototype and deploy to local host iwth a front end (Vercel deployment not required). 
I built the frontend using streamlit (a light weight ui for python). For demo day I will build a react frontend that can be deployed on vercel.

## Creating a Golden Test Data Set
### Assess your pipeline using the RAGAS framework including key metrics faithfulness, response relevance, context precision, and context recall. Provide a table of your output results.
I ended up manually creating my test data set as I was running into issues with the synthetic data generation. The error suggested that there might be some issue with generating personas. In the interest of time I switched to generating some questions myself and used it for both retrievals. Please refer to [table](evaluation/Ragas%20Evaluation%20Comparison.xlsxfile.ext) for Naive Retrieval metrics.

### What conclusions can you draw about the performance and effectiveness of your pipeline with this information?
for the naive retrieval the results for the metrics were as follows - 
faithfulness - This is low, meaning that Scout answers were not always grounded in truth.
answer_relevancy: The answer_relevancy is good almost at 0.8. It means that the answer generated by Scout addresses the question well.
context_precision: This measures how many of the retrieval chunks are relevant to the question. At 0.5 Scout is peforming average for the chuned documents it has retrieved.
context_recall: This measures how many of the relevant documents or piece of information were successfully retrieved. Scout performed average on this metric as well.
**Key insights from the above -** The answer generation is good. Both the precision and recall are not good. Low faithfulness suggestsretrieved context is not sufficient for accurate answers.


## Advanced Retrieval
### Swap out base retriever with advnaced retrieval methods.
I decided to use cohere re-ranking to help improve retrieval quality (fetching more results and then re-ranking them). The re-ranking can also filter out irrelevant chunks and increase precision. Re-ranking could also help surface more relevant information that might be buried in lower ranked results.

## Assessing Performance
### How does the performance compare to your original RAG application? Test the new retrieval pipeline using the RAGAS frameworks to quantify any improvements. Provide results in a table.
Faithfulness: Slight Increase (-0.5%) - reranking may have a minor improvement
Answer Relevancy: Marginal improvement (-0.19%) - minor decrease in answer relavncy, suggesting that answers are still quite relevant
Context Precision: No change (0.0%) - same chunk relevance
Context Recall: No change (0.0%) - same information retrieval
The above results suggest that re-ranking has a small impact on materially improving the Scout agent. I think I could further improve Scout by improving the chunking by perhaps using semantic chunking or other chunking by titles and sub titles of sections.


### Articulate the changes that you expect to make to your app in the second half of the course. How will you improve your application?
1) Provide agent & llms with the date, so that it is able to distinguish between past and future events and suggest them correctly.
2) When user asks about an event, ask user whether they would like to add a calendar invite for it.
3) Allow user to directly integrate with gmail.
4) I also want to try different chunking straegies like increasing the sizes of the chunks and having different chunking strategies for different sections like important dates and for longer sections. These chunking strategies could further improve RAGAS metrics Faithfulness in particular.


## Public Github Repo
### A 5-minute (OR LESS) loom video of a live demo of your application that also describes the use case.
### A written document addressing each deliverable and answering each question
### All relevant code




