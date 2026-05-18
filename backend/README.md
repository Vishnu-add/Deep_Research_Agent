## Steps to set up and run the backend

### Option 1: Using `conda`

1. Open a terminal.
2. Create a new conda environment:
   - `conda create -n myenv python=3.11 -y`
3. Activate it:
   - `conda activate myenv`
4. Install Poetry with pip:
   - `pip install poetry`
5. Navigate to the backend folder:
   - `cd Deep_Research_Agent/backend`
6. Install dependencies with Poetry:
   - `poetry install`
7. Start the server:
   - `poetry run uvicorn src.backend.app:app --port 8001`

---

### Option 2: Using Python `venv`

1. Open a terminal.
2. Create a virtual environment:
   - `python3 -m venv .venv`
3. Activate it:
   - `source .venv/bin/activate`
4. Install Poetry with pip:
   - `pip install poetry`
5. Navigate to the backend folder:
   - `cd /home/coder/UiA_Labs/DNN/Deep_Research_Agent/backend`
6. Install dependencies with Poetry:
   - `poetry install`
7. Start the server:
   - `poetry run uvicorn src.backend.app:app --port 8001`

---

### Runnning the server
poetry run uvicorn src.backend.app:app --port 8001 --reload

---

### Run python script to accept the streaming response

```python
import httpx

url = "http://localhost:8001/get_stream"
body = {
  "question": "Compare DeepSeek-R1 reinforcement learning with OpenAI o3 reasoning tiers. Analyze compute efficiency, benchmark performance, and scaling approaches.",
  "max_iterations": 3,
  "session_id": "2"
}

async def main():
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            url,
            json=body
        ) as response:

            async for chunk in response.aiter_text():
                print(chunk , end=" | ")

await main()
```


#### these are the intermediate steps which backend streams
```bash
"Planning the research approach..."

"Invoking the planner agent..."

"Planning completed."

"Decomposing the research plan into subqueries..."

"Decomposition completed."

"Searching for information..."

"Validating retrieved sources..."

"Reflecting on the research process..."

"More information needed. Looping back to decomposer."

"Decomposing the research plan into subqueries..."

"Decomposition completed."

"Searching for information..."

"Validating retrieved sources..."

"Reflecting on the research process..."

"More information needed. Looping back to decomposer."

"Decomposing the research plan into subqueries..."

"Decomposition completed."

"Searching for information..."

"Validating retrieved sources..."

"Reflecting on the research process..."

"Maximum loop count reached. Proceeding to synthesis."

"Synthesizing the final answer..."
```

#### this is the final message which we stream
```bash
"Open AI 's documentation highlights the integration ..."
```


### Backend To-DO : 
1. Differentiate the intermediate steps and final answer to be able to display the steps separately in the UI