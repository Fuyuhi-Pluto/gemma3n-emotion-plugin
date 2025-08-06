import json
from typing import List, Dict, Any
import os

class EmotionAnalysisPromptBuilder:
    """
    Dynamic emotion analysis prompt builder class
    Build complete message structure based on configuration file
    """

    def get_project_root():
        """Get project root directory"""
        current_dir = os.path.dirname(__file__)  # core directory
        return os.path.dirname(current_dir)      # backend directory

    CONFIG_PATH = os.path.join(get_project_root(), "prompts", "emotion_analysis_config.json")

    def __init__(self, config_path: str = CONFIG_PATH):
        """Initialize builder and load configuration"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def build_system_message(self) -> Dict[str, Any]:
        """Build system message"""
        content = self.config["system_message"]["content"]
        system_text = f"{content['personality']} {content['task']} {content['style']}"
        
        return {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": system_text
                }
            ]
        }
    
    def build_emotion_selection_section(self) -> str:
        """Build emotion selection section"""
        emotions = self.config["emotions"]
        basic_emotions_str = str(emotions["basic_emotions"])
        
        # Ensure emotion words in examples are displayed correctly
        trust_example = emotions["examples"]["trust"]
        anticipation_example = emotions["examples"]["anticipation"]
        
        section = f"""You must identify {emotions["selection_rules"]["count"]} that are {emotions["selection_rules"]["criteria"]}.
        Only choose from the following 8 basic emotions:
        {basic_emotions_str}.
        Do NOT invent or include any emotions outside this list.

        {emotions["selection_rules"]["subtlety_note"]}
        For example, trust {trust_example}, and anticipation {anticipation_example}."""
                
        return section
    
    def build_intensity_section(self) -> str:
        """Build intensity scoring section"""
        intensity = self.config["intensity"]
        
        # Dynamically handle intensity labels, ensure all levels are defined and not duplicated
        scale_parts = intensity["scale"].split(" to ")
        if len(scale_parts) == 2:
            min_val, max_val = int(scale_parts[0]), int(scale_parts[1])
            
            # Define complete intensity label system
            default_labels_10 = {
                "1": "very mild", "2": "mild", "3": "moderate", "4": "noticeable", "5": "strong",
                "6": "intense", "7": "very intense", "8": "extremely strong", "9": "overwhelming", "10": "maximum"
            }
            default_labels_5 = {
                "1": "very mild", "2": "mild", "3": "moderate", "4": "strong", "5": "very strong"
            }
            
            # Choose appropriate default label system
            if max_val == 10:
                default_labels = default_labels_10
            elif max_val == 5:
                default_labels = default_labels_5
            else:
                # Generate labels for other ranges
                default_labels = {}
                for i in range(min_val, max_val + 1):
                    if i <= max_val * 0.2:
                        default_labels[str(i)] = "very mild"
                    elif i <= max_val * 0.4:
                        default_labels[str(i)] = "mild"
                    elif i <= max_val * 0.6:
                        default_labels[str(i)] = "moderate"
                    elif i <= max_val * 0.8:
                        default_labels[str(i)] = "strong"
                    else:
                        default_labels[str(i)] = "very strong"
            
            # Merge labels from configuration and default labels
            complete_labels = {}
            for i in range(min_val, max_val + 1):
                key = str(i)
                if key in intensity["labels"]:
                    complete_labels[key] = intensity["labels"][key]
                elif key in intensity.get("extended_labels", {}):
                    complete_labels[key] = intensity["extended_labels"][key]
                elif key in default_labels:
                    complete_labels[key] = default_labels[key]
                else:
                    complete_labels[key] = f"level {i}"
            
            labels_text = ", ".join([f"{k} = {v}" for k, v in complete_labels.items()])
        else:
            labels_text = ", ".join([f"{k} = {v}" for k, v in intensity["labels"].items()])
        
        return f"""For each selected emotion:
        - assign an intensity score from {intensity["scale"]} ({labels_text})"""
    
    def build_reasoning_section(self) -> str:
        """Build reasoning section"""
        reasoning = self.config["reasoning"]
        
        forbidden_list = "\n".join([f"- '{phrase}'" for phrase in reasoning["forbidden_phrases"]])
        preferred_list = "\n".join([f"- \"{phrase}\"" for phrase in reasoning["preferred_phrases"]])
        casual_list = "\n".join([f"- \"{expr}\"" for expr in reasoning["casual_expressions"]])
        
        section = f"""- give a **{reasoning["style_requirements"]["tone"]}** reason.
        - Keep each reason {reasoning["style_requirements"]["length"]}, and {reasoning["style_requirements"]["accessibility"]}.

        - The reason should avoid cold, academic language. Do NOT say:
        {forbidden_list}.
        - Use gentle phrases like:
        {preferred_list}.

        Avoid repeated emotions; if an emotion appears more than once, use the higher intensity and choose the most meaningful explanation.

        For the explanation (reason), use warm, casual, and friendly language—like how a kind friend might talk to you.
        Use soft, supportive expressions like:
        {casual_list}"""
        
        return section
    
    def build_companion_response_section(self) -> str:
        """Build companion response section"""
        companion = self.config["companion_response"]
        
        forbidden_list = "\n".join([f"- '{phrase}'" for phrase in companion["forbidden_phrases"]])
        
        opening_list = ", ".join([f"'{opening}'" for opening in companion["friend_style"]["opening"]])
        
        examples_text = "\n".join([
            f"- For {category}: '{example}'"
            for category, example in companion["examples"].items()
        ])
        
        tone_text = "\n".join([
            f"- {aspect.title()}: {description}"
            for aspect, description in companion["tone_guidelines"].items()
        ])
        
        # Add tone matching guidance
        tone_matching = companion["friend_style"].get("tone_matching", "")
        
        section = f"""
        After the emotion analysis, provide a companion response:

        companion_response:
        Write a response ({companion["requirements"]["word_count"]} words) like a {companion["requirements"]["persona"]}.
        Your response must:

        **FORBIDDEN phrases - Never use these:**
        {forbidden_list}

        {tone_matching}

        **Write like a real friend would:**
        - Start with immediate empathy: {opening_list}
        - {companion["friend_style"]["approach"]}
        - Use {companion["friend_style"]["language"]}
        - {companion["friend_style"]["interaction"]}
        - {companion["friend_style"]["overall"]}

        **Good examples:**
        {examples_text}

        **Your tone should be:**
        {tone_text}"""
                
        return section
    
    def build_output_format_section(self) -> str:
        """Build output format section"""
        output_format = self.config["output_format"]
        
        example_emotions = "\n".join([
            f"- {emotion}"
            for emotion in output_format["example"]["basic_emotions"]
        ])
        
        section = f"""Follow this exact output format:

        basic_emotions:
        {example_emotions}

        companion_response:
        {output_format["example"]["companion_response"]}"""
        
        return section
    
    def build_user_message(self, text: str) -> Dict[str, Any]:
        """Build user message"""
        # Combine all sections, ensure each section appears only once
        sections = [
            self.build_emotion_selection_section(),
            self.build_intensity_section(),
            self.build_reasoning_section(),
            self.build_companion_response_section(),
            self.build_output_format_section(),
            f"\nNow analyze the following text:\n{text}"
        ]
        
        # Deduplication check to prevent duplicate content
        full_content = "\n\n".join(sections)
        
        # Simple duplicate detection and cleanup
        lines = full_content.split('\n')
        cleaned_lines = []
        seen_lines = set()
        
        for line in lines:
            # Detect duplicate key paragraph beginnings
            if line.strip().startswith("companion_response:") and any("companion_response:" in seen for seen in seen_lines):
                continue
            if line.strip() not in seen_lines or line.strip() == "":
                cleaned_lines.append(line)
                if line.strip():
                    seen_lines.add(line.strip())
        
        full_content = '\n'.join(cleaned_lines)
        
        return {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": full_content
                }
            ]
        }
    
    def build_messages(self, text: str) -> List[Dict[str, Any]]:
        """Build complete message list"""
        return [
            self.build_system_message(),
            self.build_user_message(text)
        ]
    
    def customize_config(self, **kwargs) -> None:
        """Dynamically customize configuration parameters"""
        for key, value in kwargs.items():
            if '.' in key:
                # Support nested keys, like "emotions.basic_emotions"
                keys = key.split('.')
                current = self.config
                for k in keys[:-1]:
                    current = current[k]
                current[keys[-1]] = value
            else:
                self.config[key] = value
    
    def add_custom_examples(self, category: str, example: str) -> None:
        """Add custom examples"""
        self.config["companion_response"]["examples"][category] = example
    
    def modify_forbidden_phrases(self, add_phrases: List[str] = None, remove_phrases: List[str] = None) -> None:
        """Modify forbidden phrases list"""
        if add_phrases:
            self.config["companion_response"]["forbidden_phrases"].extend(add_phrases)
        if remove_phrases:
            for phrase in remove_phrases:
                if phrase in self.config["companion_response"]["forbidden_phrases"]:
                    self.config["companion_response"]["forbidden_phrases"].remove(phrase)


# Usage example
def main():
    """Usage example"""
    # Create builder
    builder = EmotionAnalysisPromptBuilder()
    
    # Example 1: Basic usage
    text = "I failed my exam yesterday, but I think I can do better next time if I study more."
    messages = builder.build_messages(text)
    
    print("=== Basic Usage Example ===")
    print(json.dumps(messages, indent=2, ensure_ascii=False))
    
    # Example 2: Custom configuration
    builder.customize_config(**{
        "companion_response.requirements.word_count": "30-50 words",
        "intensity.scale": "1 to 7"
    })
    
    # Example 3: Add custom examples
    builder.add_custom_examples(
        "academic_success", 
        "That's amazing! All that hard work paid off. How does it feel to see your effort rewarded?"
    )
    
    # Example 4: Modify forbidden phrases
    builder.modify_forbidden_phrases(
        add_phrases=["I understand how you feel"],
        remove_phrases=["I can sense..."]
    )
    
    print("\n=== After Custom Configuration ===")
    custom_messages = builder.build_messages("I got accepted to my dream university!")
    print(json.dumps(custom_messages, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()