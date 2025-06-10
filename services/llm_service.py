import logging
from typing import Optional
from groq import Groq

from config import Config

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.conversation_history = []
        self.system_prompt = """You are a helpful AI voice assistant. 
        Keep your responses conversational, concise, and engaging. 
        Respond as if you're speaking naturally in a conversation.
        Avoid overly long responses to maintain good conversation flow."""
        
    async def generate_response(self, user_input: str) -> Optional[str]:
        """Generate response using Groq LLM"""
        try:
            # Add user input to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Prepare messages for LLM
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add recent conversation history (keep last 10 exchanges to manage token limit)
            recent_history = self.conversation_history[-10:]
            messages.extend(recent_history)
            
            # Generate response using Groq
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",  # Fast model for low latency
                messages=messages,
                max_tokens=150,  # Keep responses concise for voice
                temperature=0.7,
                stream=False  # Use non-streaming for simpler implementation
            )
            
            if response.choices and len(response.choices) > 0:
                assistant_response = response.choices[0].message.content
                
                # Add assistant response to history
                self.conversation_history.append({"role": "assistant", "content": assistant_response})
                
                logger.info(f"Generated LLM response: {assistant_response[:100]}...")
                return assistant_response
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            # Return fallback response
            return "I'm sorry, I didn't catch that. Could you please repeat?"
        
        return None
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_conversation_summary(self) -> dict:
        """Get conversation summary for metrics"""
        return {
            "total_exchanges": len(self.conversation_history) // 2,
            "total_tokens_estimated": sum(len(msg["content"].split()) for msg in self.conversation_history),
            "conversation_length": len(self.conversation_history)
        }
