from typing import Dict, Any
from datetime import datetime
from .base_agent import BaseAgent
from ..core.types import CompanyProfile, ResearchPhaseResult
from ..core.logger import setup_logger
from ..services.security import sanitize_company_name

logger = setup_logger("generic_agent")


class GenericResearchAgent(BaseAgent):
    """
    A generic agent that can execute any research phase based on configuration.
    """

    # Required keys in phase_config
    REQUIRED_CONFIG_KEYS = {"name", "description"}

    def __init__(self, phase_id: str, phase_config: Dict[str, Any]):
        super().__init__()

        # Validate phase_config
        if not phase_config:
            raise ValueError(f"phase_config cannot be empty for phase_id: {phase_id}")

        missing_keys = self.REQUIRED_CONFIG_KEYS - set(phase_config.keys())
        if missing_keys:
            raise ValueError(
                f"phase_config missing required keys {missing_keys} for phase_id: {phase_id}"
            )

        self.phase_id = phase_id
        self.phase_config = phase_config
        self.agent_name = f"Agent-{phase_config['name']}"

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        # Sanitize user input for prompts
        safe_name = sanitize_company_name(company.name)

        # 1. Generate Queries
        templates = self.phase_config.get("query_templates", [])
        queries = []
        for tpl in templates:
            try:
                query = tpl.format(
                    company_name=safe_name,
                    industry=company.industry or "general",
                    country=company.country or "Global",
                    year="2024",  # Dynamic year ideally
                )
                queries.append(query)
            except KeyError as e:
                logger.warning(f"Missing key for query template: {e}")

        # 2. Gather Data
        sources = await self._gather_data(queries)

        # 3. Prepare Context
        context = "\n\n".join(
            [f"Source: {s.title}\nContent: {s.content[:2000]}" for s in sources]
        )

        # 4. Determine Template and Output Path
        # phase_id is now like "00-Strategic-Context/01-Company-Overview"
        # We want the template to be "00-Strategic-Context/01-Company-Overview.md"
        # But we keep templates flat or matching structure?
        # Let's match the structure in templates dir for cleanliness, or keep them flat with full name.
        # Let's go with flat templates named after the file: "01-Company-Overview.md"

        if "/" in self.phase_id:
            folder, filename = self.phase_id.split("/")
            template_name = f"{filename}.md"
        else:
            template_name = f"{self.phase_id}.md"

        # Read template content to guide the LLM
        try:
            template_path = self.renderer.templates_dir / template_name
            if not template_path.exists():
                # Try finding it in a subfolder if we decide to organize templates
                pass
            template_content = template_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not read template {template_name}: {e}")
            template_content = "No template found."

        prompt = f"""
        You are an expert researcher tasked with the '{self.phase_config['name']}' phase for {safe_name}.
        
        Goal: {self.phase_config['description']}
        
        Analyze the gathered data and extract structured information to populate the report.
        
        You must return a JSON object that matches the variables used in the following Jinja2 template:
        
        --- TEMPLATE START ---
        {template_content}
        --- TEMPLATE END ---
        
        Ensure all variables (like {{ variable_name }} or {{% for item in list %}}) are populated in the JSON.
        For lists, ensure the items have the correct keys as used in the template.
        
        If specific fields are missing in the data, use "N/A" or reasonable estimates based on the industry.
        
        Data:
        {context}
        """

        # Add specific hints based on phase
        if "Target-Audience" in self.phase_id:
            prompt += '\nEnsure you extract "icps" (list), "customer_journey", and "digital_habits".'
        elif "Marketing-Execution" in self.phase_id:
            prompt += '\nEnsure you extract "channels" (list), "content_pillars", and "funnel_architecture".'

        from ..services.json_parser_helper import robust_json_parse

        # Initialize before try block to avoid NameError in exception handler
        content_json_str = ""

        try:
            content_json_str = await self.ai.generate(prompt, response_format="json")
            data = robust_json_parse(content_json_str)

            # Common fields
            data["company_name"] = company.name
            data["industry"] = company.industry
            data["title"] = self.phase_config["name"]
            data["generated_at"] = datetime.now()  # Add timestamp

            markdown_content = self._render(template_name, data, sources)

        except Exception as e:
            logger.error(f"Error in generic agent {self.phase_id}: {e}")
            markdown_content = f"# Error\n\n{e}\n\nRaw:\n{content_json_str}"

        return ResearchPhaseResult(
            phase_name=self.phase_id,  # Use full path as phase name for file manager
            markdown_content=markdown_content,
            sources=sources,
        )
