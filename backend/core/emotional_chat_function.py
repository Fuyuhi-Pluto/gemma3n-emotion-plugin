import torch
import uuid
from typing import Dict, Any, List, Optional, Tuple
from utils.role_creator_builder import ConversationManager

class EmotionalChatHandler:
    """
    Emotional Chat Handler - Integrates role creation and local model calling
    """
    
    def __init__(self, model, processor):
        """
        Initialize handler
        
        Args:
            model: Local language model
            processor: Model processor
        """
        self.model = model
        self.processor = processor
        self.conversation_manager = ConversationManager()
        self.active_conversations = {}  # {conversation_id: conversation_data}
    
    def start_emotional_conversation(self, 
                                    text: str, 
                                    emotion_dict: Dict[str, Dict[str, Any]], 
                                    reference_response: str,
                                    conversation_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Start emotional support conversation
        
        Args:
            text: User input text
            emotion_dict: Emotion analysis results {'joy': {'intensity': 4, 'reason': '...'}, ...}
            reference_response: Reference response
            conversation_id: Optional conversation ID, will auto-generate if not provided
            
        Returns:
            Tuple[str, str]: (conversation_id, ai_response)
        """
        
        # Generate conversation ID
        if conversation_id is None:
            conversation_id = f"conv_{str(uuid.uuid4())[:8]}"
        
        # Create role and get messages
        start_result = self.conversation_manager.start_conversation(
            conversation_id, text, emotion_dict, reference_response
        )
        
        # Call local model
        ai_response = self._call_local_model(start_result['messages'])
        
        # Save conversation state
        self.active_conversations[conversation_id] = {
            "role_id": start_result['role_id'],
            "history": [
                {"role": "user", "content": text},
                {"role": "assistant", "content": ai_response}
            ],
            "original_context": {
                "text": text,
                "emotions": emotion_dict,
                "reference": reference_response
            }
        }
        
        return conversation_id, ai_response
    
    def continue_emotional_conversation(self, 
                                      conversation_id: str, 
                                      new_user_input: str) -> str:
        """
        Continue emotional support conversation
        
        Args:
            conversation_id: Conversation ID
            new_user_input: New user input
            
        Returns:
            str: AI response
        """
        
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Get conversation history
        conversation_data = self.active_conversations[conversation_id]
        history = conversation_data["history"]
        
        # Get subsequent conversation messages
        continue_result = self.conversation_manager.continue_conversation(
            conversation_id, history, new_user_input
        )
        
        # Call local model
        ai_response = self._call_local_model(continue_result['messages'])
        
        # Update conversation history
        conversation_data["history"].extend([
            {"role": "user", "content": new_user_input},
            {"role": "assistant", "content": ai_response}
        ])
        
        return ai_response
    
    def _call_local_model(self, messages: List[Dict[str, Any]]) -> str:
        """
        Call local model to generate response
        
        Args:
            messages: Standard message format
            
        Returns:
            str: Model generated response
        """
        
        # 1. 应用chat template
        inputs = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors='pt'
        ).to(self.model.device)
        
        # 2. 获取输入长度（用于后续截取）
        input_len = inputs["input_ids"].shape[-1]
        
        # 3. 生成回复
        with torch.inference_mode():
            generation = self.model.generate(
                **inputs, 
                max_new_tokens=300, 
                do_sample=False,
                pad_token_id=self.processor.tokenizer.eos_token_id
            )
            generation = generation[0][input_len:]
        
        # 4. 解码生成的文本
        decoded = self.processor.decode(generation, skip_special_tokens=True)
        
        return decoded.strip()
    
    def get_conversation_info(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation information
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Dict: Detailed conversation information
        """
        
        if conversation_id not in self.active_conversations:
            return {"error": "Conversation not found"}
        
        conversation_data = self.active_conversations[conversation_id]
        manager_info = self.conversation_manager.get_conversation_info(conversation_id)
        
        return {
            "conversation_id": conversation_id,
            "role_id": conversation_data["role_id"],
            "message_count": len(conversation_data["history"]),
            "original_context": conversation_data["original_context"],
            "manager_info": manager_info
        }
    
    def end_conversation(self, conversation_id: str) -> bool:
        """
        End conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            bool: Whether successfully ended
        """
        
        # Clean up conversation manager
        manager_ended = self.conversation_manager.end_conversation(conversation_id)
        
        # Clean up local conversation data
        local_ended = False
        if conversation_id in self.active_conversations:
            del self.active_conversations[conversation_id]
            local_ended = True
        
        return manager_ended and local_ended
    
    def list_active_conversations(self) -> List[str]:
        """
        List all active conversation IDs
        
        Returns:
            List[str]: List of conversation IDs
        """
        
        return list(self.active_conversations.keys())


# Simplified usage functions
def create_emotional_response(text: str, 
                            emotion_dict: Dict[str, Dict[str, Any]], 
                            reference_response: str,
                            model, 
                            processor) -> Tuple[str, str]:
    """
    Simplified one-time emotional response generation function
    
    Args:
        text: User input text
        emotion_dict: Emotion analysis results
        reference_response: Reference response  
        model: Local language model
        processor: Model processor
        
    Returns:
        Tuple[str, str]: (conversation_id, ai_response)
    """
    
    handler = EmotionalChatHandler(model, processor)
    return handler.start_emotional_conversation(text, emotion_dict, reference_response)


def continue_emotional_response(conversation_id: str,
                              new_user_input: str, 
                              model,
                              processor,
                              handler: Optional[EmotionalChatHandler] = None) -> str:
    """
    Simplified function for continuing emotional conversation
    
    Args:
        conversation_id: Conversation ID
        new_user_input: New user input
        model: Local language model
        processor: Model processor
        handler: Optional existing handler instance
        
    Returns:
        str: AI response
    """
    
    if handler is None:
        handler = EmotionalChatHandler(model, processor)
    
    return handler.continue_emotional_conversation(conversation_id, new_user_input)


# Usage example
def demo_usage():
    """Usage example (requires actual model and processor)"""
    
    # Assume you have loaded model and processor
    # model = your_loaded_model
    # processor = your_loaded_processor
    
    print("=== Emotional Chat Handler Usage Example ===\n")
    
    # Example data
    text = "I'm graduating next week. I'm so proud but really going to miss this place."
    emotion_dict = {
        'joy': {'intensity': 4, 'reason': "You mentioned feeling proud, and that's wonderful!"},
        'sadness': {'intensity': 3, 'reason': "You also said you're going to miss the place."},
        'anticipation': {'intensity': 2, 'reason': "Thinking about the future and what's next is exciting!"}
    }
    reference_response = "What a mix of feelings! It's such a big step, and it's completely okay to feel both proud and a little sad."
    
    print("Method 1: Using EmotionalChatHandler class")
    print("Code example:")
    print("""
# Initialize handler
handler = EmotionalChatHandler(model, processor)

# Start conversation
conversation_id, ai_response = handler.start_emotional_conversation(
    text, emotion_dict, reference_response
)

# Continue conversation
user_input_2 = "I'm scared about what comes next."
ai_response_2 = handler.continue_emotional_conversation(conversation_id, user_input_2)

# Get conversation info
info = handler.get_conversation_info(conversation_id)

# End conversation
handler.end_conversation(conversation_id)
    """)
    
    print("\nMethod 2: Using simplified functions")
    print("Code example:")
    print("""
# One-time response generation
conversation_id, ai_response = create_emotional_response(
    text, emotion_dict, reference_response, model, processor
)

# Continue conversation
ai_response_2 = continue_emotional_response(
    conversation_id, "I'm scared about what comes next.", model, processor
)
    """)
    
    print("\nMethod 3: Actual integration in main program")
    print("Code example:")
    print("""
# In your main program
def main():
    # Load models
    model = load_your_model()
    processor = load_your_processor()
    
    # Create handler
    chat_handler = EmotionalChatHandler(model, processor)
    
    # Process user input
    user_text = get_user_input()
    emotions = analyze_emotions(user_text)  # Your emotion analysis
    reference = get_reference_response()    # Your reference response
    
    # Generate emotional support response
    conv_id, response = chat_handler.start_emotional_conversation(
        user_text, emotions, reference
    )
    
    print(f"AI: {response}")
    
    # Continue conversation loop
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
            
        ai_response = chat_handler.continue_emotional_conversation(conv_id, user_input)
        print(f"AI: {ai_response}")
    
    # Cleanup
    chat_handler.end_conversation(conv_id)
    """)

if __name__ == "__main__":
    demo_usage()
