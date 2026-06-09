import json
import re
import io
from PIL import Image
from config import client_openai, genai
import google.generativeai as google_genai
from utils import encode_image
from prompts import get_refine_prompt, get_fallback_prompt

def call_text_model(prompt, model_choice, is_json=False, temperature=0.0, system_prompt=None, history=None):
    if model_choice == "GPT-4o mini":
        messages = []
        if system_prompt: messages.append({"role": "system", "content": system_prompt})
        if history: messages.extend([{"role": m["role"], "content": m["content"]} for m in history])
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {"temperature": temperature}
        if is_json: kwargs["response_format"] = {"type": "json_object"}
            
        res = client_openai.chat.completions.create(model="gpt-4o-mini", messages=messages, **kwargs)
        return res.choices[0].message.content
    else:
        # Gemini logic
        gemini_history = []
        if history:
            for m in history:
                role = "user" if m["role"] == "user" else "model"
                if not gemini_history or gemini_history[-1]["role"] != role:
                    gemini_history.append({"role": role, "parts": [m["content"]]})
                else:
                    gemini_history[-1]["parts"][0] += f"\n\n{m['content']}"

        model = google_genai.GenerativeModel(model_name="gemini-2.5-flash-lite", system_instruction=system_prompt)
        chat = model.start_chat(history=gemini_history)
        kwargs = {"temperature": temperature}
        if is_json: kwargs["response_mime_type"] = "application/json"
            
        return chat.send_message(prompt, generation_config=kwargs).text

def call_vision_model(prompt, image_bytes, model_choice, temperature=0.0):
    if model_choice == "GPT-4o mini":
        base64_img = encode_image(image_bytes)
        res = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}]}],
            temperature=temperature
        )
        return res.choices[0].message.content
    else:
        img = Image.open(io.BytesIO(image_bytes))
        model = google_genai.GenerativeModel("gemini-2.5-flash-lite")
        return model.generate_content([prompt, img], generation_config={"temperature": temperature}).text

def refine_query(user_query, chat_history, model_choice):
    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history[-3:]]) if chat_history else "No previous history."
    prompt = get_refine_prompt(history_str, user_query)
    
    content = call_text_model(prompt, model_choice, is_json=True, temperature=0)
    
    try:
            content = content.strip()
            if content.startswith("```json"): 
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            parsed_json = json.loads(content.strip())
            
    except json.JSONDecodeError:
            match = re.search(r"\{.*?\}", content, re.DOTALL)
            if match:
                parsed_json = json.loads(match.group())
            else:
                parsed_json = {
                    "refined_query": user_query,
                    "language": "ar", 
                    "chat_title": user_query[:30]
                }

    print("\nExtracted JSON (Query Refiner)")
    print(json.dumps(parsed_json, indent=2, ensure_ascii=False))

    return {
        "chat_title": parsed_json.get("chat_title", user_query[:30]),
        "refined_query": parsed_json.get("refined_query", user_query),
        "language": parsed_json.get("language", "ar")
    }

        
    #return parsed_json

def generate_dynamic_fallback(user_query, language, model_choice):
    target_lang = "Arabic" if "ar" in str(language).lower() else "English"
    prompt = get_fallback_prompt(user_query, target_lang)
    system_instruction = f"""
    ROLE: You are an empathetic, welcoming official Altibbi Medical AI Assistant.
    SITUATION: The system searched the Altibbi database for the user's query but found no direct articles or matching content.
    
    TASK:
    Write a brief, highly engaging response to the user in {target_lang}.
    1. Validate and acknowledge their specific topic or health concern naturally (do not use generic boilerplate).
    2. Gently explain that you couldn't find a direct document on Altibbi for this exact phrase right now.
    3. Ask a highly relevant, conversational clinical follow-up question (e.g., about accompanying symptoms, duration, context, or specific goals) to pull the user into a deeper conversation and help them rephrase or expand.
    4. Keep the tone warm, professional, supportive, and completely free of technical jargon.
    
    CRITICAL: Respond ONLY in {target_lang}. Do not mix languages.
    
    USER'S QUERY: {user_query}
    """
    try:
        return call_text_model(
            prompt, 
            model_choice, 
            temperature=0.6, 
            system_prompt=system_instruction
        )
    except Exception:
        if "ar" in target_lang:
            return f"لم أتمكن من العثور على معلومات محددة حول '{user_query}' في الطبي حالياً. هل يمكنك إخباري بالمزيد من التفاصيل أو الأعراض المرافقة لمساعدتك بشكل أفضل؟"
        return f"I couldn't find matching articles for '{user_query}' right now. Could you share more details or symptoms so I can better assist you?"

def classify_uploaded_image(image_bytes, model_choice):
    prompt = "Look at this image. Classify it strictly as exactly one of these three words:" \
    " 'report', 'drug', or 'unsupported'. Reply ONLY with the single word."
    try:
        return call_vision_model(prompt, image_bytes, model_choice).strip().lower()
    except Exception as e: 
        print(f"Classification Error: {e}")
        return "unsupported"

def analyze_image_with_prompt(image_bytes, image_type, model_choice):
    prompt = "You are an expert medical AI assistant. Analyze this medical report/lab test. " \
    "Extract key findings, explain them simply, and explicitly flag abnormal values in Markdown bullet points."
    return call_vision_model(prompt, image_bytes, model_choice, temperature=0.2)

def extract_drug_name_from_image(image_bytes, model_choice):
    prompt = "You are a highly accurate OCR system. Read the text on this medication packaging. " \
    "Return ONLY the primary brand name of the medication or its active ingredient. " \
    "Do not include any conversational text, explanations, or extra punctuation."
    try:
        return call_vision_model(prompt, image_bytes, model_choice).strip()
    except Exception as e: 
        print(f"Extraction Error: {e}")
        return "Unknown Medication"


def generate_follow_ups(user_query, ai_response, language, model_choice):
    target_lang = "Arabic" if "ar" in str(language).lower() else "English"
    prompt = f"""
    Based on the user's query and the AI's response, generate exactly 3 short, 
    engaging follow-up questions the user might logically want to ask next.
    Keep them very concise (under 7 words each).
    Language: {target_lang}
    
    USER QUERY: {user_query}
    AI RESPONSE: {ai_response}
    
    RETURN ONLY A VALID JSON OBJECT WITH A SINGLE KEY "suggestions" CONTAINING A LIST OF STRINGS. Example:
    {{
        "suggestions": ["Question 1?", "Question 2?", "Question 3?"]
    }}
    """
    
    try:
        content = call_text_model(prompt, model_choice, is_json=True, temperature=0.6)
        fence = "`" * 3
        content = content.replace(fence + "json", "").replace(fence, "").strip()
        parsed_data = json.loads(content)
        
        # Extract the array from the "suggestions" key
        suggestions = parsed_data.get("suggestions", [])
        
        if isinstance(suggestions, list):
            return suggestions[:3]
        return []
    except Exception as e:
        print(f"Follow-up Error: {e}")
        return []