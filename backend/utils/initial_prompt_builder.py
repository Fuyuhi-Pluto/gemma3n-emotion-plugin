import json
from typing import Dict, Any, List
import os

class InitialPromptBuilder:
    """
    Builder for generating initial response prompts based on emotion analysis results
    """

    def get_project_root():
        """Get project root directory"""
        current_dir = os.path.dirname(__file__)  # core directory
        return os.path.dirname(current_dir)      # backend directory

    CONFIG_PATH = os.path.join(get_project_root(), "prompts", "initial_config.json")


    def __init__(self, config_path: str = CONFIG_PATH):
        """Initialize builder and load configuration"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def analyze_emotions(self, emotions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze emotion combinations and intensity"""
        emotion_list = list(emotions.keys())
        intensities = [emotions[emotion]['intensity'] for emotion in emotion_list]
        max_intensity = max(intensities)
        
        # Determine intensity level
        if max_intensity <= 2:
            intensity_level = "mild"
        elif max_intensity == 3:
            intensity_level = "moderate"
        else:
            intensity_level = "strong"
        
        # Determine emotion type
        if len(emotion_list) == 1:
            emotion_type = "single"
            primary_emotion = emotion_list[0]
        elif len(emotion_list) == 2:
            emotion_type = "two_emotions"
            primary_emotion = emotion_list[0]  # Take first as primary emotion
        else:
            emotion_type = "complex_emotions"
            primary_emotion = emotion_list[0]
        
        return {
            "emotion_type": emotion_type,
            "primary_emotion": primary_emotion,
            "emotion_list": emotion_list,
            "intensity_level": intensity_level,
            "max_intensity": max_intensity
        }
    
    def build_emotion_guidance(self, emotions: Dict[str, Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """Build emotion handling guidance"""
        templates = self.config["emotion_templates"]
        
        guidance = "EMOTION GUIDANCE:\n"
        
        if analysis["emotion_type"] == "single":
            # 单一情绪
            emotion = analysis["primary_emotion"]
            if emotion in templates["single_emotions"]:
                template = templates["single_emotions"][emotion]
                guidance += f"Template for {emotion}: \"{template}\"\n"
        
        elif analysis["emotion_type"] == "two_emotions":
            # 两种情绪
            emotion1, emotion2 = analysis["emotion_list"]
            template = templates["mixed_emotions"]["two_emotions"].format(
                emotion1=emotion1, emotion2=emotion2
            )
            guidance += f"Template for mixed emotions: \"{template}\"\n"
        
        else:
            # 复杂情绪
            template = templates["mixed_emotions"]["complex_emotions"]
            guidance += f"Template for complex emotions: \"{template}\"\n"
        
        return guidance
    
    def build_intensity_guidance(self, analysis: Dict[str, Any]) -> str:
        """Build intensity guidance"""
        intensity_config = self.config["intensity_language"][analysis["intensity_level"]]
        
        guidance = f"""INTENSITY GUIDANCE:
        Use these descriptors: {', '.join(intensity_config['descriptors'])}
        Validation approach: {intensity_config['validation']}
        """
        return guidance
    
    def build_language_guidance(self) -> str:
        """Build language style guidance"""
        language = self.config["language_guidelines"]
        
        guidance = f"""LANGUAGE GUIDELINES:
        Use warm phrases like: {', '.join(language['warmth_phrases'])}
        Use validation phrases like: {', '.join(language['validation_phrases'])}

        AVOID these phrases: {', '.join(language['avoid_phrases'])}
        """
        return guidance
    
    def build_reference_guidance(self, reference_response: str) -> str:
        """Build reference response guidance"""
        if not reference_response:
            return ""
        
        guidance = f"""REFERENCE RESPONSE:
        \"{reference_response}\"

        {self.config['reference_analysis']['use_reference']}
        - Notice the acknowledgment style in the reference
        - Notice the validation approach in the reference  
        - Notice the invitation method in the reference
        Create your own response with similar warmth but based on the specific emotions detected.
        """
        return guidance
    
    def build_invitation_guidance(self) -> str:
        """Build invitation guidance"""
        invitations = self.config["gentle_invitations"]
        
        guidance = f"""GENTLE INVITATION OPTIONS:
        {chr(10).join(f'• "{invitation}"' for invitation in invitations)}
        """
        return guidance
    
    def format_emotions_for_prompt(self, emotions: Dict[str, Dict[str, Any]]) -> str:
        """Format emotion analysis results"""
        formatted = []
        for emotion, data in emotions.items():
            formatted.append(f"• {emotion}: intensity={data['intensity']}, reason=\"{data['reason']}\"")
        return "\n".join(formatted)
    
    def build_system_message(self) -> Dict[str, Any]:
        """Build system message"""
        return {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": self.config["system_message"]["content"]
                }
            ]
        }
    
    def build_user_message(self, emotions: Dict[str, Dict[str, Any]], reference_response: str = "") -> Dict[str, Any]:
        """Build user message"""
        
        # Analyze emotions
        analysis = self.analyze_emotions(emotions)
        
        # Build various guidance sections
        sections = [
            "TASK: Create a warm, empathetic initial response based on the emotion analysis results.",
            "",
            "DETECTED EMOTIONS:",
            self.format_emotions_for_prompt(emotions),
            "",
            self.build_emotion_guidance(emotions, analysis),
            self.build_intensity_guidance(analysis),
            self.build_language_guidance(),
            self.build_invitation_guidance()
        ]
        
        # Add reference guidance if reference response exists
        if reference_response:
            sections.extend([
                "",
                self.build_reference_guidance(reference_response)
            ])
        
        # Add final requirements
        response_structure = self.config["response_structure"]
        sections.extend([
            "",
            "RESPONSE REQUIREMENTS:",
            f"• Structure: {response_structure['emotion_acknowledgment']} + {response_structure['validation']} + {response_structure['gentle_invitation']}",
            f"• Length: {response_structure['total_length']}",
            f"• Tone: {response_structure['tone']}",
            "",
            "Create a natural, warm response that combines these elements and helps the user feel seen and safe to share more."
        ])
        
        full_content = "\n".join(sections)
        
        return {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": full_content
                }
            ]
        }
    
    def build_messages(self, emotions: Dict[str, Dict[str, Any]], reference_response: str = "") -> List[Dict[str, Any]]:
        """Build complete message list"""
        return [
            self.build_system_message(),
            self.build_user_message(emotions, reference_response)
        ]
    
    def get_emotion_analysis(self, emotions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Get emotion analysis information for debugging"""
        return self.analyze_emotions(emotions)


# Usage example
def main():
    """Usage example"""
    
    builder = InitialPromptBuilder()
    
    # Example 1: Standard input
    emotions1 = {
        'joy': {'intensity': 4, 'reason': "You mentioned feeling proud, and that's wonderful! It sounds like you've worked so hard and achieved something truly special."},
        'sadness': {'intensity': 3, 'reason': "You also said you're going to miss the place, and that's completely understandable. It's natural to feel a sense of loss when something significant comes to an end."},
        'anticipation': {'intensity': 2, 'reason': "Thinking about the future and what's next is exciting! It sounds like you're looking forward to the possibilities ahead."}
    }

    reference_response1 = "What a mix of feelings! It's such a big step, and it's completely okay to feel both proud and a little sad. What are you most looking forward to about the future?"
    
    print("=== Example 1: Mixed emotions + reference response ===")
    print("Input emotions:")
    for emotion, data in emotions1.items():
        print(f"  {emotion}: intensity={data['intensity']}")
    
    print(f"\nReference response: {reference_response1}")
    
    # Build prompt
    messages1 = builder.build_messages(emotions1, reference_response1)
    analysis1 = builder.get_emotion_analysis(emotions1)
    
    print(f"\nEmotion analysis: {analysis1['emotion_type']}, intensity level: {analysis1['intensity_level']}")
    print("✅ Prompt build successful")
    
    
    # Display generated prompt content fragments
    print(f"\n=== Generated Prompt Content Preview ===")
    user_message = messages1[1]["content"][0]["text"]
    lines = user_message.split('\n')
    
    print("Key guidance content:")
    for line in lines:
        if any(keyword in line for keyword in ["DETECTED EMOTIONS:", "Template for", "Use these descriptors:", "REFERENCE RESPONSE:"]):
            print(f"  {line}")
            # If it's DETECTED EMOTIONS, show the following lines
            if "DETECTED EMOTIONS:" in line:
                idx = lines.index(line)
                for i in range(idx + 1, min(idx + 4, len(lines))):
                    if lines[i].strip():
                        print(f"    {lines[i]}")


if __name__ == "__main__":
    main()
