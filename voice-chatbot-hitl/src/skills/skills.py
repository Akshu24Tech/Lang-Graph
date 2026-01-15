"""
Agent Skills System - Enhances user prompts with meta-instructions for better LLM responses.

This module loads skills from skills.md and applies them to user messages before LLM processing.
"""

import os
import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Skill:
    """Represents a single agent skill."""
    id: str
    name: str
    enabled: bool
    purpose: str
    enhancement: str
    
    def __repr__(self):
        status = "✅" if self.enabled else "❌"
        return f"{status} {self.name} ({self.id})"


class SkillsManager:
    """Manages loading and applying agent skills."""
    
    def __init__(self, skills_file: str = "src/skills/skills.md"):
        """
        Initialize the SkillsManager.
        
        Args:
            skills_file: Path to the skills.md configuration file
        """
        self.skills_file = skills_file
        self.skills: List[Skill] = []
        self.load_skills()
    
    def load_skills(self) -> None:
        """Load skills from the skills.md file."""
        if not os.path.exists(self.skills_file):
            print(f"⚠️ Skills file '{self.skills_file}' not found. No skills loaded.")
            return
        
        try:
            with open(self.skills_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse skills using regex
            self.skills = self._parse_skills(content)
            
            enabled_count = sum(1 for s in self.skills if s.enabled)
            print(f"✅ Loaded {len(self.skills)} skills ({enabled_count} enabled)")
            
        except Exception as e:
            print(f"❌ Error loading skills: {e}")
            self.skills = []
    
    def _parse_skills(self, content: str) -> List[Skill]:
        """
        Parse skills from markdown content.
        
        Args:
            content: Raw markdown content from skills.md
            
        Returns:
            List of Skill objects
        """
        skills = []
        
        # Pattern to match skill sections
        # Matches: ### [number]. [name]
        skill_pattern = r'###\s+\d+\.\s+(.+?)\n\*\*ID:\*\*\s+`(.+?)`\s+\n\*\*Enabled:\*\*\s+`(true|false)`\s+\n\*\*Purpose:\*\*\s+(.+?)\n\n\*\*Enhancement:\*\*\n```\n(.+?)\n```'
        
        matches = re.finditer(skill_pattern, content, re.DOTALL)
        
        for match in matches:
            name = match.group(1).strip()
            skill_id = match.group(2).strip()
            enabled = match.group(3).strip().lower() == 'true'
            purpose = match.group(4).strip()
            enhancement = match.group(5).strip()
            
            skills.append(Skill(
                id=skill_id,
                name=name,
                enabled=enabled,
                purpose=purpose,
                enhancement=enhancement
            ))
        
        return skills
    
    def get_enabled_skills(self) -> List[Skill]:
        """Get all enabled skills."""
        return [s for s in self.skills if s.enabled]
    
    def get_skill_by_id(self, skill_id: str) -> Optional[Skill]:
        """Get a specific skill by ID."""
        for skill in self.skills:
            if skill.id == skill_id:
                return skill
        return None
    
    def enhance_prompt(self, user_message: str, skills_to_apply: Optional[List[str]] = None) -> str:
        """
        Enhance a user message with meta-instructions from enabled skills.
        
        Args:
            user_message: The original user message
            skills_to_apply: Optional list of skill IDs to apply. If None, uses all enabled skills.
            
        Returns:
            Enhanced prompt with skill instructions
        """
        if not user_message or not user_message.strip():
            return user_message
        
        # Determine which skills to use
        if skills_to_apply:
            skills = [s for s in self.skills if s.id in skills_to_apply and s.enabled]
        else:
            skills = self.get_enabled_skills()
        
        if not skills:
            return user_message
        
        # Build the enhanced prompt
        enhancement_lines = []
        
        for skill in skills:
            enhancement_lines.append(skill.enhancement)
        
        # Combine enhancements into a meta-instruction block
        meta_instructions = "\n\n".join(enhancement_lines)
        
        # Format: [META-INSTRUCTIONS]\n\n[USER MESSAGE]
        enhanced_prompt = f"""<META-INSTRUCTIONS>
{meta_instructions}
</META-INSTRUCTIONS>

<USER-REQUEST>
{user_message}
</USER-REQUEST>

Remember to follow the meta-instructions above when responding to the user request."""
        
        return enhanced_prompt
    
    def get_skills_summary(self) -> str:
        """Get a summary of all loaded skills."""
        if not self.skills:
            return "No skills loaded."
        
        lines = [f"📋 **Agent Skills Summary** ({len(self.skills)} total)\n"]
        
        for skill in self.skills:
            status = "✅ Enabled" if skill.enabled else "❌ Disabled"
            lines.append(f"**{skill.name}** (`{skill.id}`)")
            lines.append(f"  {status} - {skill.purpose}")
            lines.append("")
        
        return "\n".join(lines)
    
    def reload_skills(self) -> None:
        """Reload skills from the markdown file."""
        print("🔄 Reloading skills...")
        self.load_skills()


# Global skills manager instance
_skills_manager = None


def get_skills_manager(skills_file: str = "src/skills/skills.md") -> SkillsManager:
    """
    Get or create the global SkillsManager instance.
    
    Args:
        skills_file: Path to the skills.md file
        
    Returns:
        SkillsManager instance
    """
    global _skills_manager
    
    if _skills_manager is None:
        _skills_manager = SkillsManager(skills_file)
    
    return _skills_manager


def enhance_user_prompt(user_message: str, skills_file: str = "src/skills/skills.md", 
                        skills_to_apply: Optional[List[str]] = None) -> str:
    """
    Convenience function to enhance a user prompt with skills.
    
    Args:
        user_message: The original user message
        skills_file: Path to the skills.md file
        skills_to_apply: Optional list of skill IDs to apply
        
    Returns:
        Enhanced prompt
    """
    manager = get_skills_manager(skills_file)
    return manager.enhance_prompt(user_message, skills_to_apply)


# Example usage
if __name__ == "__main__":
    # Test the skills system
    manager = SkillsManager()
    
    print("\n" + "="*60)
    print(manager.get_skills_summary())
    print("="*60 + "\n")
    
    # Test prompt enhancement
    test_message = "How do I improve my code quality?"
    enhanced = manager.enhance_prompt(test_message)
    
    print("Original Message:")
    print(test_message)
    print("\n" + "-"*60 + "\n")
    print("Enhanced Prompt:")
    print(enhanced)
