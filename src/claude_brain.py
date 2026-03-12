"""
Claude AI brain for WallPi.
Sends user text to Claude and gets Wall-E personality responses.
"""

import logging
import anthropic

logger = logging.getLogger(__name__)


class ClaudeBrain:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        max_tokens: int = 300
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.conversation_history = []

    def think(self, user_message: str) -> str:
        """
        Send message to Claude and get Wall-E response.
        Maintains conversation history for context.
        """
        logger.info(f"🧠 Thinking about: '{user_message}'")

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages=self.conversation_history
            )

            assistant_message = response.content[0].text

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            # Keep history manageable (last 10 exchanges)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            logger.info(f"💬 Response: '{assistant_message}'")
            return assistant_message

        except anthropic.APIConnectionError:
            logger.error("No internet connection!")
            return "Ουπς! Δεν μπορώ να συνδεθώ. Έχεις internet;"
        except anthropic.RateLimitError:
            logger.error("Rate limit hit!")
            return "Χμμ, χρειάζομαι λίγο χρόνο. Ρώτα με πάλι σε λίγο!"
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return "Ουάου, κάτι πήγε στραβά! Δοκίμασε πάλι!"

    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
