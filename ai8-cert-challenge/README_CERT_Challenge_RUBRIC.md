# Defining your Problem and Audience

### Write a succinct 1-sentence description of the problem
Parents get flooded with school emails and newsletters; important dates (minimum days, picture day, field trips, spirit days, PTA meetings) get buried. Manually copying them is error-prone and time consuming.

### Write 1-2 paragraphs on why this is a problem for your specific user
Parents today are overwhelmed by the flood of school communication — weekly newsletters, classroom reminders, PTA announcements, event flyers, and emails from multiple teachers. Important details like “Picture Day is next Thursday” or “Bring cash for the field trip” are buried inside long messages that arrive at odd times. Even the most organized parent can miss a date or instruction, leading to last-minute stress, forgotten deadlines, or disappointed kids.

## Propose a Solution
### Propose a Solution
The problem Scout solves is simple but powerful: it acts as a friendly chatbot that makes sense of the constant stream of unstructured school updates parents receive. Instead of reading every long email or newsletter, parents can simply ask Scout questions like “When is Spirit Day?” or “Do I need to bring anything tomorrow?” and get quick, accurate answers pulled straight from their school’s communications. By turning messy inboxes into clear, conversational insights, Scout takes the mental load out of staying on top of school logistics — helping parents feel organized, confident, and focused on their family instead of their email.

### Describe the tools you plan to use in each part of your stack.  Write one sentence on why you made each tooling choice.

### Where will you use an agent or agents?  What will you use “agentic reasoning” for in your app?

## Dealing with the Data
### Describe all of your data sources and external APIs, and describe what you’ll use them for.
The data is sent by the school via email. I copied 4 emails into PDF files for now to test my application. I had initially planned to connect my email and possibly using the the langchain gmail api to connect to the email. I willdo that for the final demo.

### Describe the default chunking strategy that you will use.  Why did you make this decision?
I used an 800 character chunk size with 100 character overly. 500 - 100 character chunking is usually the best chunking size. The chunking also take the senetence boundaries into consideration and tries to preserve the entire senetence vs breaking up thoughts mid-sentence.
### [Optional] Will you need specific data for any other part of your application?   If so, explain.
No othet data needed right now, but I was thinking of possibly building something similar for scraping the school site as well for demo day.

## Building a Quick End-to-End Prototype
# Build an end-to-end prototype and deploy to local host iwth a front end (Vercel deployment not required). I built the frontend using streamlit (a light weight ui for python). For demo day I will build a react frontend that can be deployed.

## Creating a Golden Test Data Set
# Assess your pipeline using the RAGAS framework including key metrics faithfulness, response relevance, context precision, and context recall. Provide a table of your output results.

# What conclusions can you draw about the performance and effectiveness of your pipeline with this information?

## Advanced Retrieval
# Swap out base retriever with advnaced retrieval methods.

## Assessing Performance
# How does the performance compare to your original RAG application? Test the new retrieval pipeline using the RAGAS frameworks to quantify any improvements. Provide results in a table.
# Articulate the changes that you expect to make to your app in the second half of the course. How will you improve your application?

## Public Github Repo
# A 5-minute (OR LESS) loom video of a live demo of your application that also describes the use case.
# A written document addressing each deliverable and answering each question
# All relevant code




