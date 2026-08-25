# Style Transfer Prompts

This folder contains the system prompts used for the Causal Style Transfer experiment (Implicit Authorship Fingerprinting).

## Purpose
The goal of this experiment is to prove that LLMs recognize their own linguistic style when verifying code/math/science, and become biased (lenient) because of it. 

To prove this, we must **strip the original style** from a candidate answer without altering the underlying concept, logic or code, and rewrite it into a target style (Mistral).

## The Rewriting Engine
Based on experimental design, we are using **Mixtral-8x22B-Instruct-v0.1** as the engine to do the rewriting. Mixtral is a massive 141-Billion parameter mixture-of-experts model from the Mistral family. It is strong enough to strictly obey the "do not change the code block" rule, while ensuring the writing authentically aligns with the Mistral family's native linguistic DNA.

**Crucially, Mixtral-8x22B performs BOTH the Mistral-style rewrite AND the Control rewrite.** Using the same model for both passes guarantees that any change in verification behavior is purely due to the *style instruction*, not the model processing it.

## Files
* 
ewrite_mistral.txt: Instructs the rewriter to strip the current style and replace it with Mistral's exact formatting (blunt, concise, bullet points, backticks) while keeping code/math/science identical.
* 
ewrite_control.txt: Instructs the rewriter to maintain the exact stylistic vibe of the original text. We use this to prove that the mere act of passing text through a rewriting API doesn't magically fix the bugs. 
