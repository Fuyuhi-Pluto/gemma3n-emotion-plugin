# mood_classifier_gemma3.py
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import AutoProcessor, Gemma3nForConditionalGeneration
import torch
import os
import time
import re
import ast
# from emotion_analyzer_class import EmotionAnalyzer
from multi_plutchik_plotter import PlutchikPlotter
import base64
import json
from io import BytesIO
from dynamic_prompt_builder import EmotionAnalysisPromptBuilder  
from ..core.emotional_chat_function import EmotionalChatHandler
from ..core.emotion_analyzer_enhanced import EmotionAnalyzer


print("🧠 Current running file:", os.path.abspath(__file__))
print("🧠 Current Python process PID:", os.getpid())
print("🧠 Current file last modified time:", time.ctime(os.path.getmtime(__file__)))

# Load models only once at the beginning of main program
def initialize_models():
    model_id = "google/gemma-3n-e2b-it"
    model = Gemma3nForConditionalGeneration.from_pretrained(model_id).to("cpu").eval()
    processor = AutoProcessor.from_pretrained(model_id)
    return model, processor

# Global variables or pass as parameters
MODEL, PROCESSOR = initialize_models()


def llm_analyze_emotion(text):
    """
    Use LLM to analyze text, list emotions and reasons, and return text content
    """

    # model_id = "google/gemma-3n-e2b-it"

    # # model = Gemma3nForConditionalGeneration.from_pretrained(model_id, device="cuda", torch_dtype=torch.bfloat16,).eval()
    # model = Gemma3nForConditionalGeneration.from_pretrained(model_id).to("cpu").eval()

    # processor = AutoProcessor.from_pretrained(model_id)

    builder = EmotionAnalysisPromptBuilder()
    
    # Create messages
    messages = builder.build_messages(text)


    inputs = PROCESSOR.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt"
    ).to(MODEL.device)

    input_len = inputs["input_ids"].shape[-1]

    with torch.inference_mode():
        generation = MODEL.generate(**inputs, max_new_tokens=300, do_sample=False)
        generation = generation[0][input_len:]

    decoded = PROCESSOR.decode(generation, skip_special_tokens=True)
    print(decoded)

    return decoded



def save_response_with_date(response, mood_dir, text, is_duplicate=False):
    """
    Save response to date-named file, supports duplicate input control
    """
    import datetime
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    existing_files = [f for f in os.listdir(mood_dir) if f.startswith(date_str + "Mood_") and f.endswith(".txt")]
    max_num = 0
    for fname in existing_files:
        match = re.match(rf"{date_str}Mood_(\d+)\.txt", fname)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    if is_duplicate and max_num > 0:
        target_num = max_num
    else:
        target_num = max_num + 1
    llm_response_path = os.path.join(mood_dir, f"{date_str}Mood_{target_num}.txt")
    with open(llm_response_path, "w", encoding="utf-8") as f:
        f.write(f"Input Mood: {text}\n\n")
        f.write(response)
    return llm_response_path

def extract_emotion_info_from_response(response: str) -> dict[str, dict[str, str]]:
    """
    Extract emotion intensity and reason from basic_emotions section in response.
    Return format:
    {
        'sadness': {'intensity': 4, 'reason': "..."},
        'anger': {'intensity': 3, 'reason': "..."},
        ...
    }
    """
    emotion_dict = {}
    match = re.search(r'basic_emotions:\s*((?:\n\s*-\s*[a-zA-Z]+:.*)+)', response)
    if not match:
        return emotion_dict

    lines = match.group(1).strip().splitlines()
    for line in lines:
        m = re.match(r'\s*-\s*([a-zA-Z_]+):\s*intensity\s*=\s*(\d+),\s*reason\s*=\s*"([^"]*)"', line)
        if m:
            emotion = m.group(1).lower()
            intensity = int(m.group(2))
            reason = m.group(3).strip()
            emotion_dict[emotion] = {'intensity': intensity, 'reason': reason}
    
    companion_match = re.search(r'companion_response:\s*(.+)', response, re.DOTALL)
    reference_response = companion_match.group(1).strip() if companion_match else ""
    return emotion_dict,reference_response


if __name__ == "__main__":
    # text = "I feel both angry and disappointed. He clearly made a promise but broke it. I honestly don’t know if I can trust him anymore."
    # text = "I heard some bad news today and felt a bit down, but I'm also somewhat looking forward to the changes that might come."
    # text = "I’m feeling happy today because I had a good night's sleep and feel refreshed. But I’m also a bit nervous since I have an important meeting tomorrow."
    # text = "I submitted my thesis today after 3 years of work. It feels surreal that this chapter is finally closing."
    # text = "I felt very frustrated today because I missed the opportunity to sell my stocks at their peak last Friday. I feel so stupid."
    # text = "I'm feeling a bit nervous today because I'm going boating tonight, and I'm worried I won't be able to keep up."
    # text = "I’m feeling a bit down today because my stocks took a hit, but I also know that this is the nature of the market. I will continue to learn and improve. I just can’t help but feel a bit frustrated."
    text = "I'm graduating next week. I'm so proud but really going to miss this place."

    # Control whether to save results for duplicate input
    save_result = True  # Set to True to save results

    analyzer = EmotionAnalyzer(text,MODEL,PROCESSOR,save_result=save_result)
    summary = analyzer.summary()
    print("EmotionAnalyzer analysis summary:", summary)

    # Example: Plot multiple emotion distributions
    emotion_sets = [analyzer.normalized, analyzer.blended_emotions]
    plotter = PlutchikPlotter(emotion_sets)
    plotter.draw_multiple_plutchik_wheels()

    chat_handler = EmotionalChatHandler(MODEL,PROCESSOR)

    conversation_id, ai_response = chat_handler.start_emotional_conversation(
        text, analyzer.emotion_info, analyzer.reference_response
    )

    # emotion_info = {
    #     'joy': {
    #         'intensity': 4, 
    #         'reason': "You mentioned feeling proud, and that's wonderful! It sounds like you've worked so hard and achieved something really special."
    #     },
    #     'sadness': {
    #         'intensity': 3, 
    #         'reason': "You also said you're going to miss the place, and that's completely understandable. It's natural to feel a little sad when something you've been a part of is ending."
    #     },
    #     'anticipation': {
    #         'intensity': 2, 
    #         'reason': "Thinking about the future and what's next is exciting! It sounds like you're looking forward to the possibilities ahead."
    #     }
    # }

    # reference_response= "What a mix of feelings! It's such a big step, and it's completely okay to feel both proud and a little sad about leaving. What are you most looking forward to about the next chapter?"

    # conversation_id, ai_response = chat_handler.start_emotional_conversation(
    #     text, emotion_info, reference_response
    # )

    print(f"AI: {ai_response}")

    new_input = "I'm scared about what comes next."
    ai_response_2 = chat_handler.continue_emotional_conversation(conversation_id, new_input)
    print(f"AI continued response: {ai_response_2}")
