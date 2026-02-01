import ollama
from config import settings, DEVICE_URLS
import asyncio
import logging
import json

class LLMService:
    def _get_client(self, model_name: str) -> ollama.Client:
        """Return an Ollama client pointed at the correct device URL for this model."""
        url = DEVICE_URLS.get(model_name, settings.ollama_device_a_url)
        return ollama.Client(host=url)

    async def call(self, model_name: str, system_prompt: str, user_content: str) -> str:
        """
        Generic Ollama call. All agents go through here.
        """
        client = self._get_client(model_name)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        # ollama.Client.chat is synchronous — run in executor
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: client.chat(model=model_name, messages=messages)
            )
            return response["message"]["content"]
        except Exception as e:
            logging.error(f"LLM Call failed for {model_name}: {e}")
            raise e

    async def chat(self, system_prompt: str, user_content: str) -> str:
        return await self.call(settings.MODEL_MAIN_REASONER, system_prompt, user_content)

    async def summarize(self, system_prompt: str, user_content: str) -> str:
        return await self.call(settings.MODEL_MAIN_REASONER, system_prompt, user_content)

    async def merge(self, system_prompt: str, user_content: str) -> str:
        return await self.call(settings.MODEL_MAIN_REASONER, system_prompt, user_content)

    async def extract_graph(self, system_prompt: str, user_content: str) -> str:
        """Calls graph-builder on Device B. Caller must catch exceptions."""
        return await self.call(settings.MODEL_GRAPH_BUILDER, system_prompt, user_content)

    async def exploration_chat(self, system_prompt: str, user_content: str) -> tuple[str, str | None]:
        """
        Exploration stub. Attempts exploration model. Falls back to main-reasoner.
        Returns (response_text, fallback_from).
        """
        try:
            # Future: call a 3B exploration model on Device B
            raise NotImplementedError("Exploration model not yet configured")
        except Exception:
            logging.warning("Exploration model not configured or unreachable. Falling back to main-reasoner.")
            response = await self.chat(system_prompt, user_content)
            return response, "exploration"

    async def judge_branch_need(self, conversation_history: str) -> dict:
        """
        Analyze conversation to determine if branching is needed.
        Returns parsed JSON with should_branch, confidence, suggested_branches.
        """
        system_prompt = """You are a conversation analyzer. Analyze the given chat exchange and determine if the conversation has reached a natural branching point where multiple distinct topics should be explored separately. Respond with valid JSON only."""
        
        try:
            response = await self.call(
                settings.MODEL_BRANCH_JUDGE, 
                system_prompt, 
                conversation_history
            )
            # Try to extract JSON from the response
            # Handle cases where model might wrap JSON in markdown code blocks
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            
            return json.loads(clean_response.strip())
        except json.JSONDecodeError as e:
            logging.warning(f"Branch judge returned invalid JSON: {e}")
            return {"should_branch": False, "confidence": 0.0, "reason": "Parse error", "suggested_branches": []}
        except Exception as e:
            logging.warning(f"Branch judge failed: {e}")
            return {"should_branch": False, "confidence": 0.0, "reason": str(e), "suggested_branches": []}

llm_service = LLMService()

