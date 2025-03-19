import vertexai
from vertexai.preview import prompts
from config.settings import settings

class PromptManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "initialized", False):
            return

        # Initialize Vertex AI using the project id from settings.
        vertexai.init(project=settings.prompt_setting.project_id)

        # Immediately verify that all prompt IDs in the mapping are available.
        available_prompt_ids = {p.prompt_id for p in prompts.list()}
        missing_prompts = [
            name for name, pid in settings.prompt_setting.prompt_mapping.items()
            if pid not in available_prompt_ids
        ]
        if missing_prompts:
            raise ValueError(
                f"The following prompts are missing in Vertex AI: {missing_prompts}"
            )

    def get_prompt(self, prompt_name: str) -> str:
        prompt_id = settings.prompt_setting.prompt_mapping.get(prompt_name)
        if not prompt_id:
            raise ValueError(f"No prompt id configured for prompt '{prompt_name}'")
        prompt = prompts.get(prompt_id)
        return prompt.prompt_data

    def assemble_prompt(self, prompt_name: str, **kwargs):
        prompt = self.get_prompt(prompt_name)
        try:
            assembled = prompt.assemble_contents(**kwargs)
        except TypeError as e:
            raise ValueError(
                f"Failed to assemble prompt '{prompt_name}'. Ensure that all required input variables are provided. Original error: {e}"
            )
        if not assembled or not assembled[0].text.strip():
            raise ValueError(f"The assembled prompt for '{prompt_name}' is empty. Check your input values.")
        return assembled[0].text.strip()