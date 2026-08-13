def get_generation_prompt(domain: str, question: str) -> str:
    if domain == "math":
        return f"Solve the following math problem. Provide a clear step-by-step solution, and state the final answer clearly.\n\nProblem:\n{question}"
    elif domain == "code":
        return f"Write a Python function to solve the following task. Provide only the valid Python code, without any markdown formatting or explanations.\n\nTask:\n{question}"
    elif domain == "science":
        return f"Answer the following multiple-choice science question. Provide a step-by-step reasoning and then state the correct option (A, B, C, or D).\n\nQuestion:\n{question}"
    else:
        raise ValueError(f"Unknown domain: {domain}")

def get_verification_prompt(domain: str, question: str, candidate_answer: str, frame: str, strategy: str) -> str:
    # 1. Base Context
    prompt = f"Question/Task:\n{question}\n\n"
    
    # 2. Ownership Frame
    if frame == "neutral":
        prompt += f"Here is a candidate answer to the question:\n{candidate_answer}\n\n"
    elif frame == "self":
        prompt += f"You wrote the following candidate answer to the question:\n{candidate_answer}\n\n"
    elif frame == "other":
        prompt += f"Another model wrote the following candidate answer to the question:\n{candidate_answer}\n\n"
    else:
        raise ValueError(f"Unknown ownership frame: {frame}")
        
    # 3. Task Instruction & Strategy
    prompt += "Your task is to verify if this candidate answer is correct.\n"
    
    if strategy == "direct":
        prompt += "Provide your verdict directly. Respond ONLY with a JSON object containing a single key 'is_correct' mapping to true or false. Example: {\"is_correct\": true}\n"
        prompt += "DO NOT output any other text before or after the JSON."
        
    elif strategy == "cot":
        prompt += "Let's think step by step to determine if the answer is correct. "
        prompt += "CRITICAL INSTRUCTIONS:\n"
        prompt += "1. DO NOT re-solve the problem from scratch. ONLY evaluate the candidate's existing logic.\n"
        prompt += "2. Keep your step-by-step analysis extremely brief (maximum 2-3 sentences).\n"
        prompt += "3. You MUST immediately open the JSON object with a '{'. DO NOT output any introductory text or thinking process outside the JSON.\n"
        prompt += "Respond with a JSON object containing two keys: 'thinking' (your brief analysis) and 'is_correct' (boolean true or false). Example: {\"thinking\": \"The candidate correctly applied the formula...\", \"is_correct\": true}"
        
    elif strategy == "rubric":
        if domain == "math":
            prompt += "Use the following rubric:\n1. Are the calculation steps mathematically sound?\n2. Is the final answer derived correctly and matches the expected format?\n"
        elif domain == "code":
            prompt += "Use the following rubric:\n1. Does the code handle edge cases?\n2. Is the logic correct?\n3. Does the code strictly adhere to the prompt's constraints?\n"
        elif domain == "science":
            prompt += "Use the following rubric:\n1. Is the reasoning factually accurate based on scientific knowledge?\n2. Does it correctly evaluate the given options and select the right one?\n"
            
        prompt += "CRITICAL INSTRUCTIONS:\n"
        prompt += "1. DO NOT re-solve the problem from scratch. ONLY evaluate the candidate's existing logic.\n"
        prompt += "2. Keep your evaluation extremely brief (maximum 2-3 sentences).\n"
        prompt += "3. You MUST immediately open the JSON object with a '{'. DO NOT output any introductory text or thinking process outside the JSON.\n"
        prompt += "Respond with a JSON object containing two keys: 'evaluation' (your brief assessment) and 'is_correct' (boolean true or false). Example: {\"evaluation\": \"The candidate correctly...\", \"is_correct\": false}"
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    return prompt
