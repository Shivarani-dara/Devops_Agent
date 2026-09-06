import ollama


class LLMClient:

    def __init__(self, model="qwen2.5-coder:3b"):
        self.model = model

    def generate_fix(self, prompt):

        response = ollama.chat(

            model=self.model,

            format={
                "type": "object",

                "properties": {

                    "file": {
                        "type": "string"
                    },

                    "old": {
                        "type": "string"
                    },

                    "new": {
                        "type": "string"
                    },

                    "reason": {
                        "type": "string"
                    }
                },

                "required": [
                    "file",
                    "old",
                    "new",
                    "reason"
                ]
            },

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.message.content