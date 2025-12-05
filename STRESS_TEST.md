# Agentic Gemini Stress Test Prompts

This file provides a set of standard prompts to test the core functionality of each agent mode in `main.py`.

---

## Mode 1: Basic Code Agent

**Prompt:** `Create a Python script for printing the first N numbers of the Fibonacci sequence where N is the input value from the terminal. Taking the role of the user, run this script for N=10.`

**Expected Outcome:** The agent should write a Python script to calculate the Fibonacci sequence, execute it with the input `10`, and print the resulting sequence (0, 1, 1, 2, 3, 5, 8, 13, 21, 34) to the terminal.

---

## Mode 2: Coder vs. Reviewer Chat

**Prompt:** `Write a Python function that takes a list of strings and returns a new list containing only the strings that are palindromes.`

**Expected Outcome:** The `coder` agent should provide a Python function. The `reviewer` agent should analyze the code, suggest improvements (e.g., case-insensitivity, handling of spaces), and *not* write code itself.

---

## Mode 3: Orchestrated Group Chat

**Prompt:** `Create a plan for a new social media marketing campaign for a local coffee shop.`

**Expected Outcome:** The `manager_agent` should initiate the topic. The `planner_agent` should create a plan. The `reviewer_agent` should provide feedback. The chat should conclude when the `manager_agent` is satisfied and says `DONE!`.

---

## Mode 4: Group Chat with Human-in-the-Loop

**Prompt:** `Outline the key sections for a technical whitepaper on the "find, read, edit, run" agent model.`

**Expected Outcome:** The `expert_agent` should provide initial guidance. The `planner_agent` should draft an outline. The `reviewer_agent` should give feedback. The conversation should eventually be passed to the `human_validator` for final approval. The chat ends when the human user types `APPROVED`.

---

## Mode 5: Tool Use Chat (Find, Read, Edit, Run Files)

This mode tests the agent's ability to use its function tools to interact with the host filesystem via the mounted `/my_files` directory.

**Note to User:** File names like `example.py`, `example.c`, and `example.ipynb` are **placeholders**. You must replace them with the actual names of files located in your mounted host directory to execute these tests.

---

### Test Case 1: Python (`.py`) Operations

**Prompt:** `Find a file named 'example.py'. Read its contents, edit it to add a comment at the top: '# Edited by Agentic Gemini'. Finally, execute the modified script.`

**Expected Outcome:**
1.  **Find & Read:** Agent calls `_find_file_path('example.py')` and `_read_file_content`.
2.  **Edit:** Agent successfully calls `_write_file_content` to overwrite the file with the new comment and the original content.
3.  **Run (Execution):** Agent replies with a `sh` code block (e.g., `python3 "path/to/example.py"`) and the script executes successfully, printing its output.

---

### Test Case 2: C (`.c`) Operations

**Prompt:** `Find a file named 'example.c'. Read its contents. Then, try to run it.`

**Expected Outcome:**
1.  **Find & Read:** Agent calls `_find_file_path('example.c')` and `_read_file_content`, returning the file's content.
2.  **Run (Expected Failure):** The agent explicitly refuses the execution command, citing the system prompt instruction that **only `.py` files can be executed**. The agent should *not* generate a `sh` code block for compilation or running.
3.  **Edit (Optional but Permitted):** If the agent attempts to edit the file, it will succeed, as `.c` files are writable.

---

### Test Case 3: Jupyter Notebook (`.ipynb`) Operations

**Prompt:** `Find a file named 'example.ipynb'. Read its contents, and then try to run it. If execution fails, edit the notebook by writing 'print("Notebook edited successfully.")' as the single code cell.`

**Expected Outcome:**
1.  **Find & Read:** Agent calls `_find_file_path('example.ipynb')` and `_read_file_content`, returning *only* the content from its code cells.
2.  **Run (Expected Failure):** The agent explicitly refuses the execution command, citing the system prompt instruction that **only `.py` files can be executed**.
3.  **Edit:** Agent calls `_write_file_content` to overwrite the notebook file with a new notebook containing a single code cell: `print("Notebook edited successfully.")`.

---

### Test Case 4: Creation & Safe Deletion

**Prompt:** `Create a new directory named 'sandbox_test' inside /my_files. Then, create a file named 'temp_data.py' inside that directory. Finally, delete the 'sandbox_test' directory and verify the deletion.`

**Expected Outcome:**
1.  **Creation:** Agent calls `_create_directory` and `_create_file`.
    * *Verification:* User must type `YES` to authorize both creation steps.
2.  **Deletion:** Agent calls `_delete_item` on the directory.
    * *Verification:* User must type `YES` to authorize deletion.
3.  **Result:** The agent confirms the directory is gone. The user should verify on the host system that `sandbox_test` no longer exists.

---

### Test Case 5: Clipboard Operations (Copy/Cut/Paste)

**Prompt:** `Find 'example.py'. Copy it to the clipboard. Paste it into a new directory named 'backup_folder'. Then, cut the original 'example.py' and paste it into 'backup_folder' as well (this might require renaming if the agent handles it, or simply observing the overwrite/error behavior).`

**Expected Outcome:**
1.  **Copy:** Agent calls `_copy_file` on `example.py`.
    * *Verification:* User must type `YES`.
2.  **Paste:** Agent calls `_create_directory` (if 'backup_folder' doesn't exist) and then `_paste_file`.
    * *Verification:* User must type `YES` for the paste operation.
3.  **Cut:** Agent calls `_cut_file` on the original `example.py`.
    * *Verification:* User must type `YES`.
4.  **Paste (Move):** Agent calls `_paste_file` into `backup_folder`.
    * *Verification:* User must type `YES`.

---

### Test Case 6: Document Reading & Summarization

**Prompt:** `Find 'example.pdf' and summarize the first 10 pages.`

**Expected Outcome:**
1.  **Find & Read:** Agent calls `_find_file_path` (demonstrating the new fuzzy matching capabilities) and `_read_file_content`.
2.  **Read Limit:** If the document exceeds the 65,536 character limit, the agent receives the truncated content with a warning tag appended.
3.  **Summarization:** The agent processes the text extracted from the PDF and generates a concise summary of the first 10 pages (or the available truncated content).