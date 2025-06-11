import re
import math
from typing import Dict, List, Tuple

class TechnicalEvaluator:
    """Technical evaluator for physical design content"""
    
    def __init__(self):
        self.technical_terms = {
            'floorplanning': {
                'macro': 3, 'placement': 4, 'area': 3, 'utilization': 4, 'power': 4,
                'thermal': 5, 'congestion': 5, 'hierarchy': 3, 'DFT': 4, 'scan': 4,
                'voltage': 4, 'domain': 3, 'ring': 3, 'grid': 4, 'IR drop': 5,
                'package': 3, 'BGA': 4, 'pin': 3, 'constraint': 3, 'timing': 4,
                'analog': 4, 'mixed-signal': 5, 'hard macro': 4, 'soft macro': 4
            },
            'placement': {
                'timing': 4, 'setup': 4, 'hold': 4, 'slack': 4, 'clock': 3,
                'delay': 4, 'optimization': 3, 'crosstalk': 5, 'skew': 5,
                'fanout': 4, 'load': 3, 'PVT': 5, 'corner': 4, 'synthesis': 4,
                'leakage': 4, 'dynamic power': 5, 'voltage island': 5, 'global': 3,
                'detailed': 3, 'legalization': 4, 'netlist': 3, 'ECO': 4
            },
            'routing': {
                'DRC': 4, 'via': 3, 'layer': 4, 'resistance': 3, 'capacitance': 4,
                'crosstalk': 5, 'integrity': 5, 'manufacturing': 5, 'maze': 5,
                'line search': 5, 'A*': 6, 'differential': 4, 'impedance': 4,
                'current density': 5, 'electromigration': 6, 'double patterning': 6,
                'coloring': 5, 'yield': 4, 'lithography': 5, 'process': 3
            }
        }
        
        self.key_concepts = {
            'floorplanning': {
                'area_optimization': ['area', 'utilization', 'density', 'compaction'],
                'power_planning': ['power grid', 'IR drop', 'power ring', 'strapping'],
                'thermal_management': ['thermal', 'heat', 'temperature', 'cooling'],
                'timing_consideration': ['timing', 'delay', 'path', 'critical'],
                'routing_congestion': ['congestion', 'routing', 'channel', 'blockage']
            },
            'placement': {
                'timing_optimization': ['timing', 'setup', 'hold', 'slack'],
                'congestion_management': ['congestion', 'routing', 'density'],
                'power_optimization': ['power', 'leakage', 'dynamic', 'switching'],
                'clock_considerations': ['clock', 'skew', 'tree', 'distribution'],
                'signal_integrity': ['crosstalk', 'noise', 'coupling', 'shielding']
            },
            'routing': {
                'layer_assignment': ['layer', 'metal', 'assignment', 'stack'],
                'via_optimization': ['via', 'contact', 'minimization', 'stacking'],
                'timing_optimization': ['timing', 'delay', 'RC', 'buffer'],
                'signal_integrity': ['crosstalk', 'noise', 'shielding', 'spacing'],
                'manufacturability': ['DRC', 'yield', 'litho', 'process', 'margin']
            }
        }
    
    def evaluate_technical_answer(self, answer: str, topic: str, question_index: int):
        """Evaluate a single technical answer"""
        if not answer or len(answer.strip()) < 20:
            return {
                'overall_score': 0.0,
                'grade_letter': 'F',
                'detailed_feedback': 'Answer too short or empty',
                'technical_terms_found': [],
                'missing_concepts': []
            }
        
        answer_lower = answer.lower()
        
        # Technical terms evaluation (40%)
        terms = self.technical_terms.get(topic, {})
        found_terms = []
        term_score = 0
        max_term_score = sum(terms.values()) if terms else 1
        
        for term, weight in terms.items():
            if term in answer_lower:
                found_terms.append(term)
                term_score += weight
        
        tech_score = min(100, (term_score / max_term_score) * 100) if max_term_score > 0 else 0
        
        # Concept coverage evaluation (30%)
        concepts = self.key_concepts.get(topic, {})
        covered_concepts = 0
        missing_concepts = []
        
        for concept_name, keywords in concepts.items():
            if any(keyword in answer_lower for keyword in keywords):
                covered_concepts += 1
            else:
                missing_concepts.append(concept_name.replace('_', ' ').title())
        
        concept_score = (covered_concepts / len(concepts)) * 100 if concepts else 0
        
        # Methodology evaluation (20%)
        methodology_keywords = ['analyze', 'approach', 'strategy', 'method', 'implement', 'optimize']
        methodology_count = sum(1 for keyword in methodology_keywords if keyword in answer_lower)
        methodology_score = min(100, (methodology_count / 3) * 100)
        
        # Practical application evaluation (10%)
        word_count = len(answer.split())
        length_score = min(100, (word_count / 150) * 100)
        
        # Tools and numerical values
        tools = ['innovus', 'icc', 'primetime', 'virtuoso', 'calibre', 'encounter']
        tool_mentions = sum(1 for tool in tools if tool in answer_lower)
        numerical_pattern = r'\b\d+(?:\.\d+)?\s*(?:mm|nm|ps|ns|mA|MHz|GHz|%)\b'
        numerical_values = len(re.findall(numerical_pattern, answer))
        
        practical_score = min(100, (tool_mentions * 20 + numerical_values * 15 + length_score * 0.5))
        
        # Calculate weighted overall score
        overall_score = (
            tech_score * 0.40 +
            concept_score * 0.30 +
            methodology_score * 0.20 +
            practical_score * 0.10
        )
        
        # Generate feedback
        feedback_parts = []
        
        if tech_score >= 70:
            feedback_parts.append(f"✅ Strong technical vocabulary ({len(found_terms)} terms)")
        else:
            feedback_parts.append(f"⚠️ Limited technical terms. Use more {topic}-specific vocabulary")
        
        if concept_score >= 70:
            feedback_parts.append("✅ Good concept coverage")
        else:
            feedback_parts.append("⚠️ Missing key concepts")
        
        if methodology_score >= 60:
            feedback_parts.append("✅ Clear methodology")
        else:
            feedback_parts.append("⚠️ Describe your approach more systematically")
        
        if practical_score >= 60:
            feedback_parts.append("✅ Good practical examples")
        else:
            feedback_parts.append("⚠️ Add specific examples and tool references")
        
        feedback = " ".join(feedback_parts)
        
        return {
            'overall_score': overall_score,
            'grade_letter': self._calculate_grade(overall_score),
            'detailed_feedback': feedback,
            'technical_terms_found': found_terms,
            'missing_concepts': missing_concepts
        }
    
    def _calculate_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 95: return "A+"
        elif score >= 90: return "A"
        elif score >= 85: return "A-"
        elif score >= 80: return "B+"
        elif score >= 75: return "B"
        elif score >= 70: return "B-"
        elif score >= 65: return "C+"
        elif score >= 60: return "C"
        elif score >= 55: return "C-"
        elif score >= 50: return "D"
        else: return "F"

def evaluate_technical_submission(answers: List[str], topic: str) -> Dict:
    """Evaluate complete submission"""
    evaluator = TechnicalEvaluator()
    question_analyses = []
    total_score = 0
    
    for i, answer in enumerate(answers):
        analysis = evaluator.evaluate_technical_answer(answer, topic, i)
        question_analyses.append({
            'question': i + 1,
            'score': analysis['overall_score'],
            'grade': analysis['grade_letter'],
            'feedback': analysis['detailed_feedback'],
            'technical_terms': analysis['technical_terms_found'],
            'missing_concepts': analysis['missing_concepts']
        })
        total_score += analysis['overall_score']
    
    avg_score = total_score / len(answers) if answers else 0
    
    # Collect strengths and weaknesses
    all_terms = []
    all_missing = []
    for analysis in question_analyses:
        all_terms.extend(analysis['technical_terms'])
        all_missing.extend(analysis['missing_concepts'])
    
    # Count frequency
    term_counts = {}
    for term in all_terms:
        term_counts[term] = term_counts.get(term, 0) + 1
    
    missing_counts = {}
    for missing in all_missing:
        missing_counts[missing] = missing_counts.get(missing, 0) + 1
    
    # Top strengths and weaknesses
    top_strengths = []
    if term_counts:
        top_strengths.append("Strong technical vocabulary")
    if avg_score >= 70:
        top_strengths.append("Good problem-solving approach")
    if any(len(answer.split()) >= 100 for answer in answers):
        top_strengths.append("Detailed explanations")
    
    top_weaknesses = []
    if avg_score < 60:
        top_weaknesses.append("Needs more technical depth")
    if missing_counts:
        top_weaknesses.append("Missing key concepts")
    if any(len(answer.split()) < 50 for answer in answers):
        top_weaknesses.append("Some answers too brief")
    
    # Grade distribution
    grade_distribution = {}
    for analysis in question_analyses:
        grade = analysis['grade']
        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
    
    return {
        'overall_score': avg_score,
        'grade_letter': evaluator._calculate_grade(avg_score),
        'question_analyses': question_analyses,
        'grade_distribution': grade_distribution,
        'top_strengths': top_strengths[:3],
        'top_weaknesses': top_weaknesses[:3],
        'detailed_breakdown': {
            'avg_technical_terms': min(100, len(set(all_terms)) / max(1, len(answers) * 3) * 100),
            'avg_concept_coverage': max(0, 100 - len(set(all_missing)) / max(1, len(answers)) * 20),
            'avg_methodology': 70 if any('approach' in answer.lower() for answer in answers) else 50,
            'avg_practical': min(100, sum(len(answer.split()) for answer in answers) / (len(answers) * 150) * 100)
        },
        'recommendations': _generate_recommendations(top_weaknesses, topic)
    }

def _generate_recommendations(weaknesses: List[str], topic: str) -> List[str]:
    """Generate study recommendations"""
    recommendations = []
    
    for weakness in weaknesses:
        if 'technical depth' in weakness:
            recommendations.append(f'Study advanced {topic} terminology and concepts')
        elif 'key concepts' in weakness:
            recommendations.append(f'Review fundamental {topic} principles')
        elif 'brief' in weakness:
            recommendations.append('Provide more detailed explanations with examples')
    
    # Default recommendations
    if not recommendations:
        recommendations = [
            f'Continue studying {topic} best practices',
            'Practice explaining complex concepts clearly',
            'Include more real-world examples'
        ]
    
    return recommendations[:3]
