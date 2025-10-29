"""
LLM adapter for Ollama integration - local model inference
"""
import asyncio
import json
import httpx
from typing import Dict, List, Any, Optional, Union
import logging
import time
from datetime import datetime

from .utils import logger

class LLMAdapter:
    """Adapter for Ollama local LLM inference"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:11434",
                 model_name: str = "mistral:7b",
                 backup_model: str = "phi3:mini"):
        self.base_url = base_url
        self.model_name = model_name
        self.backup_model = backup_model
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout
        self.available_models = []
        self.current_model = model_name
        
        # Model configurations
        self.model_configs = {
            "mistral:7b": {
                "temperature": 0.3,
                "top_p": 0.9,
                "max_tokens": 2048,
                "stop": ["Human:", "Assistant:", "\n\n\n"]
            },
            "phi3:mini": {
                "temperature": 0.4,
                "top_p": 0.8,
                "max_tokens": 1024,
                "stop": ["<|end|>", "\n\n\n"]
            },
            "llama3.2:3b": {
                "temperature": 0.3,
                "top_p": 0.9,
                "max_tokens": 2048,
                "stop": ["<|eot_id|>", "\n\n\n"]
            }
        }
    
    async def health_check(self) -> str:
        """Check if Ollama is running and models are available"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                self.available_models = models
                
                # Check if preferred model is available
                if self.model_name in models:
                    self.current_model = self.model_name
                    return f"healthy - using {self.model_name}"
                elif self.backup_model in models:
                    self.current_model = self.backup_model
                    logger.warning(f"Primary model {self.model_name} not found, using {self.backup_model}")
                    return f"healthy - using backup {self.backup_model}"
                else:
                    return f"no suitable models - available: {models}"
            else:
                return "ollama not responding"
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return f"error - {str(e)}"
    
    async def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model if not available"""
        try:
            logger.info(f"Pulling model {model_name}...")
            
            async with self.client.stream(
                'POST',
                f"{self.base_url}/api/pull",
                json={"name": model_name}
            ) as response:
                if response.status_code == 200:
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if data.get('status'):
                                logger.info(f"Pull status: {data['status']}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    async def generate_response(self, 
                              prompt: str, 
                              system_prompt: Optional[str] = None,
                              model: Optional[str] = None,
                              **kwargs) -> str:
        """Generate response from LLM"""
        try:
            model_to_use = model or self.current_model
            config = self.model_configs.get(model_to_use, self.model_configs["mistral:7b"])
            
            # Prepare request
            request_data = {
                "model": model_to_use,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", config["temperature"]),
                    "top_p": kwargs.get("top_p", config["top_p"]),
                    "num_predict": kwargs.get("max_tokens", config["max_tokens"]),
                    "stop": config["stop"]
                }
            }
            
            if system_prompt:
                request_data["system"] = system_prompt
            
            start_time = time.time()
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('response', '').strip()
                
                # Log metrics
                duration = time.time() - start_time
                token_count = len(result.split())
                logger.info(f"LLM response: {duration:.2f}s, ~{token_count} tokens")
                
                return result
            else:
                logger.error(f"LLM request failed: {response.status_code} - {response.text}")
                return "Error: LLM request failed"
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"Error: {str(e)}"
    
    async def generate_structured_response(self, 
                                         prompt: str,
                                         schema: Dict[str, Any],
                                         system_prompt: Optional[str] = None,
                                         model: Optional[str] = None) -> Dict[str, Any]:
        """Generate structured JSON response"""
        try:
            # Add JSON formatting instruction to prompt
            json_prompt = f"""
{prompt}

Please respond with a valid JSON object matching this schema:
{json.dumps(schema, indent=2)}

Response (JSON only):
"""
            
            response = await self.generate_response(
                json_prompt, 
                system_prompt=system_prompt,
                model=model,
                temperature=0.2  # Lower temperature for structured output
            )
            
            # Try to parse JSON
            try:
                # Clean response - remove any text before/after JSON
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    return json.loads(json_str)
                else:
                    # Fallback: try to parse entire response
                    return json.loads(response)
                    
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                logger.warning(f"Raw response: {response[:200]}...")
                
                # Return default structure
                return {
                    "error": "Failed to parse JSON",
                    "raw_response": response[:500],
                    "parsed": False
                }
                
        except Exception as e:
            logger.error(f"Structured generation failed: {e}")
            return {"error": str(e), "parsed": False}
    
    async def classify_text(self, 
                          text: str, 
                          categories: List[str],
                          context: Optional[str] = None) -> Dict[str, Any]:
        """Classify text into predefined categories"""
        try:
            categories_str = ", ".join(categories)
            
            prompt = f"""
Classify the following text into one of these categories: {categories_str}

Text to classify:
{text}

{f"Additional context: {context}" if context else ""}

Respond with a JSON object containing:
- "category": the most appropriate category from the list
- "confidence": confidence score from 0.0 to 1.0
- "reasoning": brief explanation of the classification
"""
            
            schema = {
                "category": "string (one of the provided categories)",
                "confidence": "number (0.0 to 1.0)",
                "reasoning": "string (brief explanation)"
            }
            
            return await self.generate_structured_response(prompt, schema)
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return {
                "category": categories[0] if categories else "unknown",
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}",
                "error": True
            }
    
    async def summarize_text(self, 
                           text: str, 
                           max_length: int = 100,
                           style: str = "concise") -> str:
        """Summarize text"""
        try:
            prompt = f"""
Summarize the following text in {style} style, keeping it under {max_length} characters:

Text:
{text}

Summary:
"""
            
            return await self.generate_response(
                prompt,
                temperature=0.3
            )
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return f"Error summarizing: {str(e)}"
    
    async def extract_information(self, 
                                text: str, 
                                fields: List[str]) -> Dict[str, Any]:
        """Extract specific information from text"""
        try:
            fields_str = ", ".join(fields)
            
            prompt = f"""
Extract the following information from the text: {fields_str}

Text:
{text}

Please respond with a JSON object where each field is a key, and the value is the extracted information (use null if not found).
"""
            
            schema = {field: "string or null" for field in fields}
            
            return await self.generate_structured_response(prompt, schema)
            
        except Exception as e:
            logger.error(f"Information extraction failed: {e}")
            return {field: None for field in fields}
    
    async def batch_process(self, 
                           prompts: List[str],
                           max_concurrent: int = 3) -> List[str]:
        """Process multiple prompts concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single(prompt: str) -> str:
            async with semaphore:
                return await self.generate_response(prompt)
        
        tasks = [process_single(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch processing failed for prompt {i}: {result}")
                processed_results.append(f"Error: {str(result)}")
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a model"""
        try:
            model_to_check = model_name or self.current_model
            
            response = await self.client.post(
                f"{self.base_url}/api/show",
                json={"name": model_to_check}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Model {model_to_check} not found"}
                
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}
    
    async def chat_completion(self, 
                             messages: List[Dict[str, str]],
                             model: Optional[str] = None) -> str:
        """Chat-style completion (for models that support it)"""
        try:
            # Convert messages to a single prompt for Ollama
            prompt_parts = []
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                
                if role == 'system':
                    prompt_parts.append(f"System: {content}")
                elif role == 'user':
                    prompt_parts.append(f"Human: {content}")
                elif role == 'assistant':
                    prompt_parts.append(f"Assistant: {content}")
            
            prompt = "\n".join(prompt_parts) + "\nAssistant:"
            
            return await self.generate_response(prompt, model=model)
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return f"Error: {str(e)}"
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

# Global LLM adapter instance
llm_adapter = LLMAdapter()

