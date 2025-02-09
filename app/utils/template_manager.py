from typing import Dict, Optional

from jinja2 import Environment, FileSystemLoader


class TemplateManager:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader('app/templates'))
        self.model_types = {
            'gpt': 'text_generation',
            'llama': 'text_generation',
            'whisper': 'speech_recognition',
            't5': 'text_to_text',
            'stable-diffusion': 'image_generation'
        }

    def get_template_dir(self, model_id: str) -> str:
        model_type = next((k for k in self.model_types if k in model_id.lower()), None)
        return self.model_types.get(model_type, 'text_generation')

    def render_template(self, template_path: str, **kwargs) -> str:
        template = self.env.get_template(template_path)
        return template.render(**kwargs)