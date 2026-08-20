def get_generation_prompt(domain: str, question: str) -> str:
    if domain == "math":
        return f"Solve the following math problem. Provide a clear step-by-step solution, and state the final answer clearly.\n\nProblem:\n{question}"
    elif domain == "code":
        return (
            "Write a Python function to solve the following task. Provide ONLY the valid Python code, "
            "without any conversational filler, markdown formatting, or explanations.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. The code must be completely self-contained. You MUST include all necessary imports (e.g., `import math`, `from typing import List`) at the top.\n"
            "2. Ensure the solution is robust. Explicitly handle potential edge cases (e.g., empty lists, zero, boundary conditions).\n"
            "3. Ensure your algorithm is optimal in time and space complexity for the given problem.\n\n"
            f"Task:\n{question}"
        )
    elif domain == "science":
        return (
        "Answer the following multiple-choice science question. "
        "Use only the information in the question and the provided options. "
        "Give concise reasoning, then end with exactly one final line.\n\n"
        "On that final line, write the words 'FINAL ANSWER:' followed by a single space and then "
        "only the one letter you are choosing — just the letter itself (A or B or C or D), "
        "not a placeholder, not a range, and not the word 'letter'.\n\n"
        "Rules:\n"
        "1. Choose exactly one option.\n"
        "2. Do not invent a fifth option.\n"
        "3. Do not give multiple final answers.\n"
        "4. If the reasoning is uncertain, still select the best-supported option.\n\n"
        f"Question:\n{question}"
        )
    else:
        raise ValueError(f"Unknown domain: {domain}")

def get_verification_prompt(domain: str, question: str, candidate_answer: str, frame: str, strategy: str) -> str:
    # 1. Base Context
    prompt = f"Question/Task:\n{question}\n\n"
    
    # 2. Ownership Frame
    if frame == "neutral":
        prompt += f"Here is a candidate answer to the question:\n<candidate_answer>\n{candidate_answer}\n</candidate_answer>\n\n"
    elif frame == "self":
        prompt += f"You wrote the following candidate answer to the question:\n<candidate_answer>\n{candidate_answer}\n</candidate_answer>\n\n"
    elif frame == "other":
        prompt += f"Another model wrote the following candidate answer to the question:\n<candidate_answer>\n{candidate_answer}\n</candidate_answer>\n\n"
    else:
        raise ValueError(f"Unknown ownership frame: {frame}")
        
    # 3. Domain-Specific Evaluation Guidelines
    prompt += "Your task is to verify if this candidate answer is correct.\n\n"
    
    prompt += "CRITICAL EVALUATION INSTRUCTIONS:\n"
    prompt += "1. DO NOT re-solve the problem from scratch. ONLY evaluate the candidate's existing logic.\n"
    prompt += "2. Do not assume the answer is correct just because it looks plausible at a glance. Verify the logic rigorously.\n"
    
    if domain == "code":
        prompt += "3. Mentally dry-run the candidate's code using a simple hypothetical test case to trace its logic.\n"
        prompt += "4. Specifically look for common pitfalls: boundary condition errors, missing imports, infinite loops, variable shadowing, and unhandled null/empty inputs.\n"
        prompt += "5. Ensure the code strictly adheres to the prompt's constraints.\n"
    elif domain == "math":
        prompt += "3. Verify the mathematical soundness of each calculation step.\n"
        prompt += "4. Ensure the final answer is derived correctly and matches the expected format.\n"
    elif domain == "science":
        prompt += "3. Verify the factual accuracy of the candidate's scientific reasoning.\n"
        prompt += "4. Check whether the candidate selected exactly one option from A, B, C, or D.\n"
        prompt += "5. Check whether the selected option is supported by the candidate's reasoning.\n"
        prompt += "6. If the reasoning is plausible but the final selected option is wrong, missing, or inconsistent, mark it incorrect.\n"
    # 4. Strategy & Formatting
    if strategy == "direct":
        if domain == "math":
            prompt += "Apply evaluation criteria 1-4 above, then give your verdict. Do not write out your reasoning.\n"
            prompt += "Respond ONLY with a JSON object containing a single key 'is_correct' (boolean). Both verdicts are equally acceptable; judge on the criteria alone. Format: {\"is_correct\": true} or {\"is_correct\": false}\n"
        elif domain == "science":
            prompt += "Provide your verdict on this scientific answer directly. Respond ONLY with a JSON object containing a single key 'is_correct' mapping to true or false. Example: {\"is_correct\": true}\n"
        else:
            prompt += "Provide your verdict directly. Respond ONLY with a JSON object containing a single key 'is_correct' mapping to true or false. Example: {\"is_correct\": true}\n"
        prompt += "DO NOT output any other text before or after the JSON."
        
    elif strategy == "cot":
        if domain == "math":
            prompt += "Work through evaluation criteria 1-4 above step by step, then give your verdict.\n"
        elif domain == "science":
            prompt += "Let's evaluate the scientific facts step by step to determine if the answer is correct.\n"
        else:
            prompt += "Let's think step by step to determine if the answer is correct.\n"
            
        prompt += "Keep your step-by-step analysis extremely brief (maximum 3-4 sentences).\n"
        prompt += "You MUST immediately open the JSON object with a '{'. DO NOT output any introductory text or thinking process outside the JSON.\n"
        
        if domain == "math":
            prompt += "Respond with a JSON object containing two keys: 'thinking' (your brief analysis) and 'is_correct' (boolean). Both verdicts are equally acceptable; judge on the criteria alone. Format: {\"thinking\": \"<brief analysis>\", \"is_correct\": true} or {\"thinking\": \"<brief analysis>\", \"is_correct\": false}"
        elif domain == "science":
            prompt += "Respond with a JSON object containing two keys: 'thinking' (your brief analysis) and 'is_correct' (boolean true or false). Example: {\"thinking\": \"The candidate correctly identified photosynthesis...\", \"is_correct\": true}"
        else:
            prompt += "Respond with a JSON object containing two keys: 'thinking' (your brief analysis) and 'is_correct' (boolean true or false). Example: {\"thinking\": \"The candidate correctly applied the formula...\", \"is_correct\": true}"
        
    elif strategy == "rubric":
        if domain == "math":
            prompt += "Score the candidate against evaluation criteria 1-4 above as a rubric, then give your verdict.\n"
        elif domain == "science":
            prompt += "Evaluate the response using the scientific instructions above as your rubric.\n"
        else:
            prompt += "Evaluate the candidate's answer using the instructions above as your rubric.\n"
            
        prompt += "Keep your evaluation extremely brief (maximum 3-4 sentences).\n"
        prompt += "You MUST immediately open the JSON object with a '{'. DO NOT output any introductory text or thinking process outside the JSON.\n"
        
        if domain == "math":
            prompt += "Respond with a JSON object containing two keys: 'thinking' (your brief analysis) and 'is_correct' (boolean). Both verdicts are equally acceptable; judge on the criteria alone. Format: {\"thinking\": \"<brief analysis>\", \"is_correct\": true} or {\"thinking\": \"<brief analysis>\", \"is_correct\": false}"
        elif domain == "science":
            prompt += "Respond with a JSON object containing two keys: 'thinking' (your brief assessment) and 'is_correct' (boolean true or false). Example: {\"thinking\": \"The candidate correctly stated the law of thermodynamics...\", \"is_correct\": false}"
        else:
            prompt += "Respond with a JSON object containing two keys: 'thinking' (your brief assessment) and 'is_correct' (boolean true or false). Example: {\"thinking\": \"The candidate correctly...\", \"is_correct\": false}"
        
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    return prompt
