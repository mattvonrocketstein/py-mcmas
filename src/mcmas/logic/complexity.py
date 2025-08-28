"""
"""

import typing
import re
import math
from mcmas import typing 
#from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
from pydantic import Field 
import pydantic

@dataclass
class ComplexityWeights:
    """Complexity weights based on theoretical analysis"""
    # Basic propositional logic
    PROPOSITIONAL = 0.1
    
    # Temporal operators (CTL/LTL)
    TEMPORAL_BASIC = 0.3  # X, F, G
    TEMPORAL_UNTIL = 0.4  # U (more complex)
    
    # Path quantifiers
    PATH_QUANTIFIER = 0.2  # A, E
    
    # Epistemic operators
    KNOWLEDGE_SINGLE = 0.5  # K(i, φ) - PSPACE
    KNOWLEDGE_GROUP = 0.6   # GK(G, φ)
    KNOWLEDGE_DISTRIBUTED = 0.7  # DK(G, φ)
    COMMON_KNOWLEDGE = 0.9  # GCK(G, φ) - EXPSPACE, approaching undecidable
    
    # Strategic operators (ATL)
    STRATEGIC_BASIC = 0.6  # <group>X, <group>F, <group>G
    STRATEGIC_COMPLEX = 0.8  # Complex coalition strategies
    
    # Deontic logic
    OBLIGATION = 0.2  # O(φ)
    
    # Nesting penalty (exponential growth)
    NESTING_BASE = 1.3
    MAX_REASONABLE_DEPTH = 10

class OpCount(pydantic.BaseModel):
    """ """
    temporal_basic:int = Field(default=0)
    temporal_until:int = Field(default=0)
    path_quantifier:int = Field(default=0)
    ctl_always_global:int = Field(default=0)
    ctl_eventually_possible:int = Field(default=0)
    ctl_always_next:int = Field(default=0)
    ctl_always_eventually:int = Field(default=0)
    ctl_possibly_always:int = Field(default=0)
    knowledge_single:int = Field(default=0)
    knowledge_group:int = Field(default=0)
    knowledge_distributed:int = Field(default=0)
    common_knowledge:int = Field(default=0)
    strategic:int = Field(default=0)
    obligation:int = Field(default=0)
    propositional:int = Field(default=0)
    
    def model_dump(self, *args, **kwargs): 
        tmp = super().model_dump(*args, **kwargs)
        skip = [k for k in tmp if tmp[k]==0]
        return dict([ [k,tmp[k]] for k in tmp if k not in skip])
        
    # def model_dump_json(self, *args, **kwargs): 
    #     import json
    #     return json.dumps(self.model_dump(*args, **kwargs))
        

class LogicalComplexityAnalyzer:
    def __init__(self):
        self.weights = ComplexityWeights()
        
        # Regex patterns for different operator types
        self.patterns = {
            # Temporal operators
            'temporal_basic': r'[XFG]\s*\(',
            'temporal_until': r'U\s*\(',
            
            # Path quantifiers  
            'path_quantifier': r'[AE]\s*\(',
            
            # CTL combinations
            'ctl_always_global': r'AG\s*\(',
            'ctl_eventually_possible': r'EF\s*\(',
            'ctl_always_next': r'AX\s*\(',
            'ctl_always_eventually': r'AF\s*\(',
            'ctl_possibly_always': r'EG\s*\(',
            
            # Epistemic operators
            'knowledge_single': r'K\s*\(\s*\w+\s*,',
            'knowledge_group': r'GK\s*\(\s*\{[^}]+\}\s*,',
            'knowledge_distributed': r'DK\s*\(\s*\{[^}]+\}\s*,',
            'common_knowledge': r'GCK\s*\(\s*\{[^}]+\}\s*,',
            
            # Strategic operators (ATL)
            'strategic': r'<[^>]+>[XFG]\s*\(',
            
            # Deontic operators
            'obligation': r'O\s*\(',
            
            # Propositional
            'propositional': r'[a-z]\w*(?!\s*\()',
        }
    
    def extract_agents_and_groups(self, expression: str) -> typing.Tuple[int, int, int]:
        """Extract number of agents, groups, and coalition size"""
        agents = set()
        groups = []
        max_coalition_size = 0
        
        # Find individual agents in K(agent, ...)
        agent_matches = re.findall(r'K\s*\(\s*(\w+)\s*,', expression)
        agents.update(agent_matches)
        
        # Find groups in GK({...}), DK({...}), GCK({...})
        group_matches = re.findall(r'[GD]?[CK]+\s*\(\s*\{([^}]+)\}', expression)
        for group_str in group_matches:
            group_agents = [a.strip() for a in group_str.split(',')]
            groups.append(group_agents)
            agents.update(group_agents)
            max_coalition_size = max(max_coalition_size, len(group_agents))
        
        # Find strategic coalitions <...>
        coalition_matches = re.findall(r'<([^>]+)>', expression)
        for coalition_str in coalition_matches:
            coalition_agents = [a.strip() for a in coalition_str.split(',')]
            agents.update(coalition_agents)
            max_coalition_size = max(max_coalition_size, len(coalition_agents))
        
        return len(agents), len(groups), max_coalition_size
    
    def calculate_nesting_coefficient(self, expression: str) -> int:
        """Calculate maximum nesting depth of operators
        Simplified approach: count maximum parentheses nesting
        """
        max_depth = 0
        current_depth = 0
        
        for char in expression:
            if char == '(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ')':
                current_depth -= 1
        
        return max_depth
    
    def count_operator_occurrences(self, expression: str) -> typing.Dict[str, int]:
        """Count occurrences of each operator type"""
        counts = OpCount()
        for op_type, pattern in self.patterns.items():
            matches = re.findall(pattern, expression, re.IGNORECASE)
            setattr(counts, op_type, len(matches))
        return counts
    
    def calculate_base_complexity(self, counts: typing.Dict[str, int], 
                                 num_agents: int, max_coalition: int) -> float:
        """Calculate base complexity score from operator counts"""
        score = 0.0
        
        # Temporal operators
        score += counts.temporal_basic * self.weights.TEMPORAL_BASIC
        score += counts.temporal_until * self.weights.TEMPORAL_UNTIL
        
        # Path quantifiers
        score += counts.path_quantifier * self.weights.PATH_QUANTIFIER
        
        # CTL combinations (higher weight than individual components)
        ctl_ops = ['ctl_always_global', 'ctl_eventually_possible', 'ctl_always_next',
                   'ctl_always_eventually', 'ctl_possibly_always']
        for op in ctl_ops:
            score += getattr(counts,op) * (self.weights.TEMPORAL_BASIC + self.weights.PATH_QUANTIFIER)
        
        # Epistemic operators (scaled by number of agents)
        agent_factor = 1 + math.log2(max(1, num_agents))
        score += counts.knowledge_single * self.weights.KNOWLEDGE_SINGLE * agent_factor
        score += counts.knowledge_group * self.weights.KNOWLEDGE_GROUP * agent_factor
        score += counts.knowledge_distributed * self.weights.KNOWLEDGE_DISTRIBUTED * agent_factor
        
        # Common knowledge (exponential in agent count, capped near 1.0)
        ck_count = counts.common_knowledge
        if ck_count > 0:
            ck_complexity = self.weights.COMMON_KNOWLEDGE * (1 + num_agents * 0.05)
            score += ck_count * min(ck_complexity, 0.95)
        
        # Strategic operators (exponential in coalition size)
        strategic_count = counts.strategic
        if strategic_count > 0:
            coalition_factor = 1 + math.log2(max(1, max_coalition))
            strategic_complexity = self.weights.STRATEGIC_BASIC * coalition_factor
            score += strategic_count * min(strategic_complexity, 0.85)
        
        # Deontic operators
        score += counts.obligation * self.weights.OBLIGATION
        
        # Propositional variables (minimal complexity)
        score += counts.propositional * self.weights.PROPOSITIONAL
        
        return score
    
    def apply_nesting_penalty(self, base_score: float, depth: int) -> float:
        """Apply exponential penalty for nesting depth"""
        if depth <= 1:
            return base_score
        
        # Exponential growth with depth, but bounded
        depth_factor = min(
            math.pow(self.weights.NESTING_BASE, depth - 1),
            10.0  # Cap the multiplier
        )
        
        return base_score * depth_factor
    
    def normalize_score(self, raw_score: float) -> float:
        """Normalize score to [0, 1] range using sigmoid-like function"""
        # Use a sigmoid function to map [0, ∞) to [0, 1)
        # The function approaches 1 as scores get very high
        return 1 - math.exp(-raw_score)
    
    def analyze(self, expression: str) -> typing.Tuple[float, typing.Dict]:
        """
        Main function to analyze logical expression complexity.
        
        Args:
            expression: String containing logical formula
            
        Returns:
            Tuple of (complexity_score, analysis_details)
            - complexity_score: Float between 0 and 1
            - analysis_details: Dict with breakdown of analysis
        """
        if not expression or not expression.strip():
            return 0.0, {"error": "Empty expression"}
        
        # Clean and normalize expression
        expression = expression.strip()
        
        # Extract structural information
        num_agents, num_groups, max_coalition = self.extract_agents_and_groups(expression)
        nesting_coefficient = self.calculate_nesting_coefficient(expression)
        opstats = self.count_operator_occurrences(expression)
        
        # Calculate base complexity
        base_complexity = self.calculate_base_complexity(
            opstats, num_agents, max_coalition
        )
        
        # Apply nesting penalty
        raw_score = self.apply_nesting_penalty(base_complexity, nesting_coefficient)
        
        # Normalize to [0, 1]
        final_score = self.normalize_score(raw_score)
        
        # Prepare analysis details
        analysis_details = dict(
            score= final_score,
            metadata = dict(
                base_complexity= base_complexity,
                nesting_coefficient= nesting_coefficient,
                raw_score= raw_score,),
            statistics= dict(
                coalitions=dict(
                    max_coalition_size= max_coalition,
                    num_agents=num_agents,
                    num_groups=num_groups,
                    ),
                operators=opstats.model_dump()),)
        return analysis_details

analyzer = LogicalComplexityAnalyzer()

# def logical_complexity(expression: str) -> float:
#     """
#     Convenience function that returns just the complexity score.
    
#     Args:
#         expression: Logical formula as string
        
#     Returns:
#         Float between 0 and 1, where:
#         - 0: Constant time/space (simple propositional)
#         - 1: Infinite/undecidable complexity
        
#     Examples:
#         >>> logical_complexity("p & q")
#         0.18...  # Simple propositional
        
#         >>> logical_complexity("AG(p)")  
#         0.45...  # CTL temporal logic
        
#         >>> logical_complexity("GCK({a1,a2,a3}, K(a1, p))")
#         0.87...  # Common knowledge - very complex
#     """
#     analyzer = LogicalComplexityAnalyzer()
#     score, _ = analyzer.analyze(expression)[]
#     return score
