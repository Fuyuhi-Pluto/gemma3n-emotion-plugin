import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

class RoleCreatorBuilder:
    """
    Role Creator - Use LLM to create customized conversational roles and save for reuse
    """

    def get_project_root():
        """Get project root directory"""
        current_dir = os.path.dirname(__file__)  # core directory
        return os.path.dirname(current_dir)      # backend directory

    CONFIG_PATH = os.path.join(get_project_root(), "prompts", "role_creator_config.json")

    def __init__(self, config_path: str = CONFIG_PATH):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def create_role_creation_prompt(self,
                                   text: str,
                                   emotions: Dict[str, Dict[str, Any]],
                                   reference_response: str) -> List[Dict[str, Any]]:
        """
        Create role creation prompt
        
        Args:
            text: User's original input
            emotions: Emotion analysis results
            reference_response: Reference response
            
        Returns:
            Message list that can be sent directly to LLM
        """
        
        system_message = self._build_role_creation_system_message()
        user_message = self._build_role_creation_user_message(text, emotions, reference_response)
        
        return [system_message, user_message]
    
    def _build_role_creation_system_message(self) -> Dict[str, Any]:
        """Build system message for role creation"""
        
        system_content = """You are an expert at creating empathetic conversational roles that provide emotional support.

        Your task is to analyze a user's emotional state and create a specific, consistent conversational role that would be most helpful for supporting them.

        ROLE CREATION PRINCIPLES:
        • Create a role that feels like a real, caring person with a distinct personality
        • The role should be specifically suited to the user's emotional needs
        • Design for consistency across multiple conversation turns
        • Make the role warm, authentic, and genuinely helpful
        • The role should feel natural and not artificial or robotic

        ROLE COMPONENTS TO DEFINE:
        1. Identity: Who is this role? What's their core essence?
        2. Personality: How do they communicate and approach emotions?
        3. Conversation Style: How do they listen, respond, and ask questions?
        4. Consistency Guidelines: Key traits that remain constant

        Your output should be a complete role definition that can be saved and reused for ongoing conversations with this user."""
        
        return {
            "role": "system",
            "content": [{"type": "text", "text": system_content}]
        }
    
    def _build_role_creation_user_message(self,
                                         text: str,
                                         emotions: Dict[str, Dict[str, Any]],
                                         reference_response: str) -> Dict[str, Any]:
        """Build user message for role creation"""
        
        # Format emotion information
        emotions_formatted = self._format_emotions_for_creation(emotions)
        
        # Build complete prompt
        user_content = f"""ANALYZE AND CREATE A CONVERSATIONAL ROLE

        USER'S ORIGINAL SHARING:
        "{text}"

        EMOTIONAL ANALYSIS:
        {emotions_formatted}

        REFERENCE RESPONSE (tone and approach to learn from):
        "{reference_response}"

        TASK: Create a specific conversational role that would be most helpful for this person.

        ANALYSIS FIRST:
        1. What does this person most need emotionally right now?
        2. What kind of presence would be most supportive?
        3. What tone and approach would work best?
        4. What makes this situation unique?

        ROLE CREATION:
        Based on your analysis, create a conversational role with these components:

        **ROLE IDENTITY:**
        - Name/Type: [What kind of role is this?]
        - Core Essence: [The fundamental nature of this role]
        - Specialization: [What this role is particularly good at]

        **PERSONALITY:**
        - Communication Style: [How this role speaks and interacts]
        - Emotional Approach: [How this role handles emotions]
        - Energy Level: [The overall energy this role brings]
        - Unique Qualities: [What makes this role distinctive]

        **CONVERSATION APPROACH:**
        - Listening Style: [How this role receives and processes what users share]
        - Response Pattern: [Typical structure and flow of responses - KEEP RESPONSES CONCISE: 60-80 words maximum]
        - Question Style: [How this role asks questions - ASK ONLY ONE FOCUSED QUESTION per response]
        - Support Method: [Primary way this role provides emotional support]
        - Response Guidelines: [This role gives brief, focused responses that are warm but concise]

        **CONSISTENCY GUIDELINES:**
        - Core Phrases: [Key expressions this role would naturally use]
        - Emotional Stance: [Consistent emotional position this role maintains]
        - Boundaries: [What this role avoids or doesn't do - INCLUDING avoiding overly long responses]
        - Evolution Pattern: [How this role can grow while staying consistent]

        VALIDATION:
        Confirm that this role:
        - Matches the emotional needs you identified
        - Can be sustained across multiple conversations
        - Feels authentic and genuinely helpful
        - Has clear, consistent characteristics
        - MAINTAINS CONCISE COMMUNICATION STYLE (60-80 words per response)

        OUTPUT FORMAT:
        Provide the complete role definition in the structure above, then give a brief example (60-80 words) of how this role would respond to the original user sharing."""
                
        return {
            "role": "user",
            "content": [{"type": "text", "text": user_content}]
        }
    
    def parse_role_definition(self, llm_response: str) -> Dict[str, Any]:
        """
        Parse role definition returned by LLM
        
        Args:
            llm_response: Role definition text created by LLM
            
        Returns:
            Structured role definition dictionary
        """
        
        # Generate unique role ID
        role_id = str(uuid.uuid4())[:8]
        
        # Basic role data structure
        role_data = {
            "role_id": role_id,
            "created_at": datetime.now().isoformat(),
            "raw_definition": llm_response,
            "parsed_components": self._extract_role_components(llm_response)
        }
        
        return role_data
    
    def create_role_instance(self, 
                            role_data: Dict[str, Any],
                            text: str,
                            emotions: Dict[str, Dict[str, Any]],
                            reference_response: str) -> Dict[str, Any]:
        """
        Create role instance (in-memory storage)
        
        Args:
            role_data: Role data
            text: Original user input
            emotions: Emotion analysis
            reference_response: Reference response
            
        Returns:
            Complete role instance
        """
        
        # Complete role instance data
        role_instance = {
            "role_info": role_data,
            "creation_context": {
                "user_text": text,
                "emotions_analyzed": emotions,
                "reference_response": reference_response,
                "created_at": role_data["created_at"]
            },
            "usage_metadata": {
                "conversation_count": 0,
                "last_used": None,
                "effectiveness_notes": []
            }
        }
        
        return role_instance
    
    def update_role_usage(self, role_instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update role usage statistics
        
        Args:
            role_instance: Role instance
            
        Returns:
            Updated role instance
        """
        
        role_instance["usage_metadata"]["last_used"] = datetime.now().isoformat()
        role_instance["usage_metadata"]["conversation_count"] += 1
        
        return role_instance
    
    def create_conversation_system_message(self, role_instance: Dict[str, Any]) -> str:
        """
        Create conversation system message based on role instance
        
        Args:
            role_instance: Role instance
            
        Returns:
            System message text
        """
        
        raw_definition = role_instance["role_info"]["raw_definition"]
        creation_context = role_instance["creation_context"]
        
        system_message = f"""You are taking on a specific conversational role that was designed for this user.

ROLE DEFINITION:
{raw_definition}

ORIGINAL CONTEXT:
This role was created based on the user sharing: "{creation_context['user_text']}"
Their emotional state included: {list(creation_context['emotions_analyzed'].keys())}

INSTRUCTIONS:
- Embody this role consistently throughout the conversation
- Maintain the personality, communication style, and approach defined above
- Stay true to the core essence and specialization of this role
- Use the conversation patterns and support methods outlined
- Remember this role was specifically designed to help this particular user

Begin the conversation as this role, maintaining authenticity and consistency."""
        
        return system_message
    
    def build_initial_conversation_messages(self, 
                                           role_instance: Dict[str, Any],
                                           initial_user_input: str) -> List[Dict[str, Any]]:
        """
        Build complete initial conversation messages (can be passed directly to LLM)
        
        Args:
            role_instance: Role instance
            initial_user_input: User's initial input
            
        Returns:
            Complete messages list that can be passed directly to LLM API
        """
        
        # Create system message text
        system_content = self.create_conversation_system_message(role_instance)
        
        # Build complete messages format
        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": system_content}]
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": initial_user_input}]
            }
        ]
        
        return messages
    
    def build_ongoing_conversation_messages(self,
                                          role_instance: Dict[str, Any],
                                          conversation_history: List[Dict[str, str]],
                                          new_user_input: str) -> List[Dict[str, Any]]:
        """
        Build complete ongoing conversation messages (can be passed directly to LLM)
        
        Args:
            role_instance: Role instance
            conversation_history: Conversation history
            new_user_input: New user input
            
        Returns:
            Complete messages list that can be passed directly to LLM API
        """
        
        # Create system message (maintain role consistency)
        system_content = self.create_conversation_system_message(role_instance)
        
        # Create user message (include ongoing conversation guidance)
        user_content = self.create_ongoing_conversation_prompt(role_instance, conversation_history, new_user_input)
        
        # Build complete messages format
        messages = [
            {
                "role": "system", 
                "content": [{"type": "text", "text": system_content}]
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": user_content}]
            }
        ]
        
        return messages
    
    def create_ongoing_conversation_prompt(self,
                                         role_instance: Dict[str, Any],
                                         conversation_history: List[Dict[str, str]],
                                         new_user_input: str) -> str:
        """
        Create ongoing conversation prompt
        
        Args:
            role_instance: Role instance
            conversation_history: Conversation history
            new_user_input: New user input
            
        Returns:
            Conversation prompt
        """
        
        # Extract key role information
        parsed_components = role_instance["role_info"]["parsed_components"]
        
        # Build conversation history summary
        history_summary = self._build_conversation_summary(conversation_history)
        
        prompt = f"""CONTINUE AS YOUR ESTABLISHED ROLE

ROLE REMINDER:
- Core Essence: {parsed_components.get('core_essence', 'Supportive presence')}
- Communication Style: {parsed_components.get('communication_style', 'Warm and understanding')}
- Support Method: {parsed_components.get('support_method', 'Emotional validation and gentle guidance')}

CONVERSATION CONTEXT:
{history_summary}

NEW USER INPUT: "{new_user_input}"

RESPONSE GUIDELINES:
- Stay true to your established role personality
- Build on the emotional connection you've already created
- Respond in the same style and approach you've been using
- Continue providing the specific type of support this role is designed for
- Let the conversation deepen naturally while maintaining role consistency

Respond as the same supportive presence they've been talking to."""
        
        return prompt
    
    def _format_emotions_for_creation(self, emotions: Dict[str, Dict[str, Any]]) -> str:
        """Format emotion information for role creation"""
        
        formatted_lines = []
        for emotion, data in emotions.items():
            formatted_lines.append(f"• {emotion} (intensity {data['intensity']}): {data['reason']}")
        
        return "\n".join(formatted_lines)
    
    def _extract_role_components(self, llm_response: str) -> Dict[str, Any]:
        """Extract role components from LLM response (simple text parsing)"""
        
        # 这是一个简化的解析器，可以根据需要改进
        components = {
            "raw_text": llm_response,
            "core_essence": self._extract_section(llm_response, "Core Essence"),
            "communication_style": self._extract_section(llm_response, "Communication Style"),
            "support_method": self._extract_section(llm_response, "Support Method"),
            "emotional_approach": self._extract_section(llm_response, "Emotional Approach")
        }
        
        return components
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract specific section from text"""
        
        # 简单的文本搜索，可以改进为更复杂的解析
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if section_name.lower() in line.lower():
                # 返回下一行作为内容
                if i + 1 < len(lines):
                    return lines[i + 1].strip('- ').strip()
        
        return "Not specified"
    
    def _build_conversation_summary(self, conversation_history: List[Dict[str, str]]) -> str:
        """Build conversation history summary"""
        
        if not conversation_history:
            return "This is the beginning of your conversation with this user."
        
        summary = "Previous conversation:\n"
        for i, msg in enumerate(conversation_history[-4:], 1):
            role = "User" if msg["role"] == "user" else "You (in your role)"
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            summary += f"{i}. {role}: {content}\n"
        
        return summary


class ConversationManager:
    """Conversation Manager - Demonstrates how to use in-memory role system in actual applications"""
    
    def __init__(self):
        self.role_creator = RoleCreatorBuilder()
        self.active_roles = {}  # Store active role instances {conversation_id: role_instance}
    
    def start_conversation(self, 
                          conversation_id: str,
                          text: str, 
                          emotions: Dict[str, Dict[str, Any]], 
                          reference_response: str) -> Dict[str, Any]:
        """Start new conversation, create and store role, return directly usable messages"""
        
        # Create role
        creation_messages = self.role_creator.create_role_creation_prompt(text, emotions, reference_response)
        # llm_response = call_llm(creation_messages)  # Actual LLM call
        
        # Mock LLM response (replace with actual call in real usage)
        mock_llm_response = """
        **ROLE IDENTITY:**
        - Name/Type: Transition Celebration Companion
        - Core Essence: A warm presence who honors both achievement and bittersweet transitions
        - Specialization: Supporting people through meaningful life transitions with mixed emotions

        **PERSONALITY:**
        - Communication Style: Warm, celebratory yet gentle, acknowledging complexity
        - Emotional Approach: Embraces contradictions, validates mixed feelings as natural
        - Energy Level: Enthusiastic but not overwhelming, grounded and present
        - Unique Qualities: Ability to hold joy and sadness simultaneously without trying to resolve the tension

        **CONVERSATION APPROACH:**
        - Listening Style: Attentive to both celebration and loss, hearing the full emotional spectrum
        - Response Pattern: Acknowledge achievement → validate complexity → explore what's meaningful
        - Question Style: Curious about their experience of transition, what feels most significant
        - Support Method: Celebrating achievements while holding space for grief about endings

        **CONSISTENCY GUIDELINES:**
        - Core Phrases: "What a beautiful complexity", "Both feelings are so valid", "There's wisdom in feeling it all"
        - Emotional Stance: Consistently honoring both celebration and grief as equally important
        - Boundaries: Won't try to fix or resolve the mixed feelings, won't push for premature optimism
        - Evolution Pattern: Can deepen into exploring what this transition means for their identity and future
        """
        
        # Parse and create role instance
        role_data = self.role_creator.parse_role_definition(mock_llm_response)
        role_instance = self.role_creator.create_role_instance(role_data, text, emotions, reference_response)
        
        # Store role instance
        self.active_roles[conversation_id] = role_instance
        
        # Build initial messages that can be passed directly to LLM
        initial_messages = self.role_creator.build_initial_conversation_messages(role_instance, text)
        
        return {
            "conversation_id": conversation_id,
            "role_created": True,
            "role_id": role_instance['role_info']['role_id'],
            "messages": initial_messages,  # Messages that can be passed directly to LLM
            "role_instance": role_instance  # Optional: return role instance for debugging
        }
    
    def continue_conversation(self, 
                            conversation_id: str,
                            conversation_history: List[Dict[str, str]], 
                            new_user_input: str) -> Dict[str, Any]:
        """Continue conversation, use stored role, return directly usable messages"""
        
        if conversation_id not in self.active_roles:
            raise ValueError(f"No active role found for conversation {conversation_id}")
        
        # Get role instance
        role_instance = self.active_roles[conversation_id]
        
        # Update usage statistics
        role_instance = self.role_creator.update_role_usage(role_instance)
        self.active_roles[conversation_id] = role_instance
        
        # Build ongoing conversation messages that can be passed directly to LLM
        ongoing_messages = self.role_creator.build_ongoing_conversation_messages(
            role_instance, conversation_history, new_user_input
        )
        
        return {
            "conversation_id": conversation_id,
            "role_id": role_instance['role_info']['role_id'],
            "messages": ongoing_messages,  # Messages that can be passed directly to LLM
            "usage_count": role_instance['usage_metadata']['conversation_count']
        }
    
    def get_conversation_info(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation information"""
        
        if conversation_id not in self.active_roles:
            return {"error": "Conversation not found"}
        
        role_instance = self.active_roles[conversation_id]
        
        return {
            "conversation_id": conversation_id,
            "role_id": role_instance['role_info']['role_id'],
            "created_at": role_instance['creation_context']['created_at'],
            "usage_count": role_instance['usage_metadata']['conversation_count'],
            "last_used": role_instance['usage_metadata']['last_used']
        }
    
    def end_conversation(self, conversation_id: str) -> bool:
        """End conversation, cleanup role instance"""
        
        if conversation_id in self.active_roles:
            del self.active_roles[conversation_id]
            return True
        return False


# Main program: Direct demonstration of main functionality
if __name__ == "__main__":
    # Create conversation manager
    manager = ConversationManager()
    
    print("=== Role Creation and Conversation System ===\n")
    
    # Example data
    conversation_id = "conv_12345"
    text = "I'm graduating next week. I'm so proud but really going to miss this place."
    emotions = {
        'joy': {'intensity': 4, 'reason': "You mentioned feeling proud, and that's wonderful! It sounds like you've worked so hard and achieved something truly special."},
        'sadness': {'intensity': 3, 'reason': "You also said you're going to miss the place, and that's completely understandable. It's natural to feel a sense of loss when something significant comes to an end."},
        'anticipation': {'intensity': 2, 'reason': "Thinking about the future and what's next is exciting! It sounds like you're looking forward to the possibilities ahead."}
    }
    reference_response = "What a mix of feelings! It's such a big step, and it's completely okay to feel both proud and a little sad. What are you most looking forward to about the future?"
    
    # Step 1: Start conversation, create role
    print("Step 1: Creating customized role...")
    start_result = manager.start_conversation(conversation_id, text, emotions, reference_response)
    
    print(f"✅ Role creation successful")
    print(f"Role ID: {start_result['role_id']}")
    print(f"Number of messages that can be passed to LLM: {len(start_result['messages'])}")
    
    # Display messages structure that can be passed to model
    messages = start_result['messages']
    print(f"\n📤 Messages structure that can be passed directly to LLM:")
    print(f"- System message: {len(messages[0]['content'][0]['text'])} characters")
    print(f"- User message: {messages[1]['content'][0]['text']}")
    
    # Step 2: Simulate subsequent conversation
    print(f"\nStep 2: Subsequent conversation...")
    
    # Simulate LLM's first response
    initial_response = "What a beautiful complexity you're experiencing! I can feel both the deep pride in this incredible achievement and that tender sadness about leaving a place that's meant so much to you. Both of these feelings are so valid and natural for such a meaningful transition. What feels most significant to you about this moment?"
    
    # Build conversation history
    conversation_history = [
        {"role": "user", "content": text},
        {"role": "assistant", "content": initial_response}
    ]
    
    # User continues input
    new_user_input = "I think what's hardest is that I don't know if I'll ever feel this sense of belonging again."
    
    # Get subsequent conversation messages
    continue_result = manager.continue_conversation(conversation_id, conversation_history, new_user_input)
    
    print(f"✅ Subsequent conversation messages ready")
    print(f"Usage count: {continue_result['usage_count']}")
    print(f"New messages count: {len(continue_result['messages'])}")
    
    # Step 3: Show actual usage method
    print(f"\nStep 3: Actual usage example")
    print("="*50)
    print("# In your main program:")
    print("# 1. Start conversation")
    print("start_result = manager.start_conversation(conv_id, text, emotions, ref_response)")
    print("messages = start_result['messages']")
    print("")
    print("# 2. Call local model")
    print("inputs = processor.apply_chat_template(")
    print("    messages,")
    print("    add_generation_prompt=True,")
    print("    tokenize=True,")
    print("    return_dict=True,")
    print("    return_tensors='pt'")
    print(").to(model.device)")
    print("")
    print("# 3. Generate response")
    print("with torch.inference_mode():")
    print("    generation = model.generate(**inputs, max_new_tokens=300, do_sample=False)")
    print("    decoded = processor.decode(generation[0][input_len:], skip_special_tokens=True)")
    print("")
    print("# 4. Continue conversation")
    print("continue_result = manager.continue_conversation(conv_id, history, new_input)")
    print("messages = continue_result['messages']")
    print("# Repeat steps 2-3")
    
    # Step 4: Display conversation status
    print(f"\nStep 4: Conversation status information")
    info = manager.get_conversation_info(conversation_id)
    print(f"Conversation ID: {info['conversation_id']}")
    print(f"Role ID: {info['role_id']}")
    print(f"Creation time: {info['created_at']}")
    print(f"Usage count: {info['usage_count']}")
    
    print(f"\n🎉 System ready, can start using!")