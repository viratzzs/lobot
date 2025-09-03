"""
Legal Reasoning Engine for Enhanced Compliance Analysis
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import networkx as nx
from datetime import datetime

class RegulatoryHierarchy(Enum):
    ACT = 1
    RULES = 2
    REGULATIONS = 3
    CIRCULARS = 4
    NOTIFICATIONS = 5

@dataclass
class LegalRule:
    """Represents a legal rule with formal structure"""
    id: str
    hierarchy: RegulatoryHierarchy
    conditions: List[str]
    consequences: List[str]
    exceptions: List[str]
    authority: str
    effective_date: datetime
    superseded_by: Optional[str] = None
    
class LegalReasoningEngine:
    """Formal reasoning engine for legal compliance"""
    
    def __init__(self):
        self.rule_graph = nx.DiGraph()
        self.rules_db = {}
        self.conflict_resolver = ConflictResolver()
        self.precedent_tracker = PrecedentTracker()
    
    def analyze_compliance(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Perform formal legal analysis of a scenario"""
        
        # 1. Extract relevant facts
        facts = self._extract_facts(scenario)
        
        # 2. Find applicable rules
        applicable_rules = self._find_applicable_rules(facts)
        
        # 3. Check for conflicts
        conflicts = self._detect_conflicts(applicable_rules)
        
        # 4. Resolve conflicts using hierarchy
        resolved_rules = self._resolve_conflicts(conflicts)
        
        # 5. Apply reasoning
        conclusions = self._apply_reasoning(facts, resolved_rules)
        
        # 6. Generate recommendations
        recommendations = self._generate_recommendations(conclusions)
        
        return {
            'facts': facts,
            'applicable_rules': applicable_rules,
            'conflicts': conflicts,
            'conclusions': conclusions,
            'recommendations': recommendations,
            'confidence_score': self._calculate_confidence(conclusions)
        }
    
    def _extract_facts(self, scenario: Dict[str, Any]) -> List[str]:
        """Extract legally relevant facts from scenario"""
        # NLP-based fact extraction
        facts = []
        
        # Example fact patterns
        fact_patterns = {
            'foreign_investment': ['FDI', 'foreign direct investment', 'overseas investor'],
            'company_formation': ['incorporate', 'company formation', 'new company'],
            'securities_offering': ['IPO', 'public offering', 'securities issue'],
            'import_export': ['import', 'export', 'customs', 'trade']
        }
        
        scenario_text = str(scenario).lower()
        for fact_type, patterns in fact_patterns.items():
            if any(pattern in scenario_text for pattern in patterns):
                facts.append(fact_type)
        
        return facts
    
    def _find_applicable_rules(self, facts: List[str]) -> List[LegalRule]:
        """Find rules applicable to given facts"""
        applicable_rules = []
        
        for rule_id, rule in self.rules_db.items():
            if self._rule_applies(rule, facts):
                applicable_rules.append(rule)
        
        # Sort by hierarchy (Acts > Rules > Circulars)
        applicable_rules.sort(key=lambda r: r.hierarchy.value)
        
        return applicable_rules
    
    def _rule_applies(self, rule: LegalRule, facts: List[str]) -> bool:
        """Check if a rule applies to given facts"""
        # Simple implementation - check if any rule conditions match facts
        rule_text = ' '.join(rule.conditions).lower()
        return any(fact.lower() in rule_text for fact in facts)
    
    def _rules_conflict(self, rule1: LegalRule, rule2: LegalRule) -> bool:
        """Check if two rules conflict"""
        # Simple implementation - rules conflict if they have contradictory consequences
        consequences1 = set(c.lower() for c in rule1.consequences)
        consequences2 = set(c.lower() for c in rule2.consequences)
        
        # Look for direct contradictions (e.g., "allowed" vs "prohibited")
        contradictions = [
            ("allowed", "prohibited"),
            ("required", "forbidden"),
            ("mandatory", "optional")
        ]
        
        for pos, neg in contradictions:
            if any(pos in c for c in consequences1) and any(neg in c for c in consequences2):
                return True
            if any(neg in c for c in consequences1) and any(pos in c for c in consequences2):
                return True
        
        return False
    
    def _classify_conflict(self, rule1: LegalRule, rule2: LegalRule) -> str:
        """Classify the type of conflict between rules"""
        if rule1.hierarchy != rule2.hierarchy:
            return "hierarchy_conflict"
        elif rule1.effective_date != rule2.effective_date:
            return "temporal_conflict"
        else:
            return "substantive_conflict"
    
    def _conditions_satisfied(self, conditions: List[str], facts: List[str]) -> bool:
        """Check if rule conditions are satisfied by facts"""
        if not conditions:
            return True
        
        # Simple implementation - check if any condition matches any fact
        facts_lower = [f.lower() for f in facts]
        return any(any(fact in condition.lower() for fact in facts_lower) for condition in conditions)
    
    def _calculate_rule_confidence(self, rule: LegalRule, facts: List[str]) -> float:
        """Calculate confidence score for rule application"""
        base_confidence = 0.7  # Base confidence
        
        # Increase confidence for higher hierarchy rules
        hierarchy_bonus = (6 - rule.hierarchy.value) * 0.05
        
        # Increase confidence for more specific rules
        specificity_bonus = min(len(rule.conditions) * 0.02, 0.2)
        
        return min(base_confidence + hierarchy_bonus + specificity_bonus, 1.0)
    
    def _resolve_conflicts(self, conflicts: List[Dict[str, Any]]) -> List[LegalRule]:
        """Resolve conflicts using conflict resolver"""
        return self.conflict_resolver.resolve(conflicts)
    
    def _generate_recommendations(self, conclusions: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations from conclusions"""
        recommendations = []
        
        for conclusion in conclusions:
            if conclusion['confidence'] > 0.7:
                recommendations.append(f"High priority: {conclusion['conclusion']}")
            elif conclusion['confidence'] > 0.5:
                recommendations.append(f"Medium priority: {conclusion['conclusion']}")
            else:
                recommendations.append(f"Low priority: {conclusion['conclusion']}")
        
        return recommendations
    
    def _calculate_confidence(self, conclusions: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score"""
        if not conclusions:
            return 0.0
        
        total_confidence = sum(c['confidence'] for c in conclusions)
        return total_confidence / len(conclusions)
    
    def _detect_conflicts(self, rules: List[LegalRule]) -> List[Dict[str, Any]]:
        """Detect conflicts between applicable rules"""
        conflicts = []
        
        for i, rule1 in enumerate(rules):
            for j, rule2 in enumerate(rules[i+1:], i+1):
                if self._rules_conflict(rule1, rule2):
                    conflicts.append({
                        'rule1': rule1,
                        'rule2': rule2,
                        'conflict_type': self._classify_conflict(rule1, rule2)
                    })
        
        return conflicts
    
    def _apply_reasoning(self, facts: List[str], rules: List[LegalRule]) -> List[Dict[str, Any]]:
        """Apply formal logical reasoning"""
        conclusions = []
        
        for rule in rules:
            if self._conditions_satisfied(rule.conditions, facts):
                for consequence in rule.consequences:
                    conclusions.append({
                        'conclusion': consequence,
                        'basis': rule.id,
                        'confidence': self._calculate_rule_confidence(rule, facts)
                    })
        
        return conclusions

class ConflictResolver:
    """Resolves conflicts between regulatory provisions"""
    
    def resolve(self, conflicts: List[Dict[str, Any]]) -> List[LegalRule]:
        """Resolve conflicts using legal principles"""
        resolution_principles = [
            self._later_in_time_principle,
            self._specific_over_general_principle,
            self._higher_hierarchy_principle
        ]
        
        resolved_rules = []
        for conflict in conflicts:
            for principle in resolution_principles:
                if principle(conflict):
                    resolved_rules.append(principle(conflict))
                    break
        
        return resolved_rules
    
    def _later_in_time_principle(self, conflict: Dict[str, Any]) -> Optional[LegalRule]:
        """Later law prevails over earlier law"""
        rule1, rule2 = conflict['rule1'], conflict['rule2']
        if rule1.effective_date > rule2.effective_date:
            return rule1
        elif rule2.effective_date > rule1.effective_date:
            return rule2
        return None
    
    def _specific_over_general_principle(self, conflict: Dict[str, Any]) -> Optional[LegalRule]:
        """Specific provision prevails over general provision"""
        rule1, rule2 = conflict['rule1'], conflict['rule2']
        
        # Count specificity indicators
        specificity1 = len(rule1.conditions) + len(rule1.exceptions)
        specificity2 = len(rule2.conditions) + len(rule2.exceptions)
        
        if specificity1 > specificity2:
            return rule1
        elif specificity2 > specificity1:
            return rule2
        return None
    
    def _higher_hierarchy_principle(self, conflict: Dict[str, Any]) -> Optional[LegalRule]:
        """Higher hierarchy law prevails"""
        rule1, rule2 = conflict['rule1'], conflict['rule2']
        if rule1.hierarchy.value < rule2.hierarchy.value:
            return rule1
        elif rule2.hierarchy.value < rule1.hierarchy.value:
            return rule2
        return None

class PrecedentTracker:
    """Tracks and applies legal precedents"""
    
    def __init__(self):
        self.precedents = {}
        self.case_law_db = {}
    
    def find_relevant_precedents(self, facts: List[str]) -> List[Dict[str, Any]]:
        """Find relevant case law and precedents"""
        relevant_precedents = []
        
        # Search case law database
        for case_id, case_data in self.case_law_db.items():
            similarity = self._calculate_factual_similarity(facts, case_data['facts'])
            if similarity > 0.7:  # Threshold for relevance
                relevant_precedents.append({
                    'case_id': case_id,
                    'similarity': similarity,
                    'holding': case_data['holding'],
                    'reasoning': case_data['reasoning']
                })
        
        return sorted(relevant_precedents, key=lambda x: x['similarity'], reverse=True)
    
    def _calculate_factual_similarity(self, facts1: List[str], facts2: List[str]) -> float:
        """Calculate similarity between two sets of facts"""
        if not facts1 or not facts2:
            return 0.0
        
        facts1_set = set(f.lower() for f in facts1)
        facts2_set = set(f.lower() for f in facts2)
        
        intersection = len(facts1_set.intersection(facts2_set))
        union = len(facts1_set.union(facts2_set))
        
        return intersection / union if union > 0 else 0.0

class ComplianceWorkflowEngine:
    """Orchestrates compliance checking workflow"""
    
    def __init__(self):
        self.reasoning_engine = LegalReasoningEngine()
        self.document_analyzer = AdvancedDocumentAnalyzer()
        self.risk_assessor = RiskAssessmentEngine()
    
    def comprehensive_compliance_check(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive compliance analysis"""
        
        # 1. Legal reasoning analysis
        legal_analysis = self.reasoning_engine.analyze_compliance(scenario)
        
        # 2. Document analysis (if documents provided)
        document_analysis = None
        if 'documents' in scenario:
            document_analysis = self.document_analyzer.analyze_documents(scenario['documents'])
        
        # 3. Risk assessment
        risk_assessment = self.risk_assessor.assess_risks(legal_analysis, document_analysis)
        
        # 4. Generate comprehensive report
        return {
            'legal_analysis': legal_analysis,
            'document_analysis': document_analysis,
            'risk_assessment': risk_assessment,
            'recommendations': self._generate_integrated_recommendations(
                legal_analysis, document_analysis, risk_assessment
            ),
            'compliance_score': self._calculate_overall_compliance_score(
                legal_analysis, risk_assessment
            )
        }
    
    def _generate_integrated_recommendations(self, legal_analysis: Dict[str, Any], 
                                           document_analysis: Optional[Dict[str, Any]], 
                                           risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate integrated recommendations from all analyses"""
        recommendations = []
        
        # Add legal recommendations
        recommendations.extend(legal_analysis.get('recommendations', []))
        
        # Add document-based recommendations
        if document_analysis:
            recommendations.append("Review document compliance based on analysis")
        
        # Add risk-based recommendations
        for risk in risk_assessment.get('risks', []):
            if risk.get('severity', 'low') == 'high':
                recommendations.append(f"High priority: Address {risk.get('description', 'identified risk')}")
        
        return recommendations
    
    def _calculate_overall_compliance_score(self, legal_analysis: Dict[str, Any], 
                                          risk_assessment: Dict[str, Any]) -> float:
        """Calculate overall compliance score"""
        base_score = legal_analysis.get('confidence_score', 0.5)
        
        # Adjust based on risk assessment
        high_risks = sum(1 for risk in risk_assessment.get('risks', []) 
                        if risk.get('severity', 'low') == 'high')
        
        risk_penalty = min(high_risks * 0.1, 0.3)  # Max 30% penalty
        
        return max(base_score - risk_penalty, 0.0)

class AdvancedDocumentAnalyzer:
    """Advanced document analysis with legal pattern recognition"""
    
    def analyze_documents(self, documents: List[str]) -> Dict[str, Any]:
        """Analyze documents for legal patterns and issues"""
        
        analysis_results = []
        
        for doc in documents:
            # 1. Extract legal entities and clauses
            entities = self._extract_legal_entities(doc)
            
            # 2. Identify problematic clauses
            problematic_clauses = self._identify_problematic_clauses(doc)
            
            # 3. Check compliance patterns
            compliance_patterns = self._check_compliance_patterns(doc)
            
            analysis_results.append({
                'document': doc[:100] + "...",
                'entities': entities,
                'problematic_clauses': problematic_clauses,
                'compliance_patterns': compliance_patterns
            })
        
        return {
            'document_analyses': analysis_results,
            'overall_compliance': self._assess_overall_document_compliance(analysis_results)
        }
    
    def _extract_legal_entities(self, document: str) -> List[str]:
        """Extract legal entities from document"""
        # Simple pattern matching for legal entities
        import re
        
        entities = []
        
        # Company patterns
        company_patterns = [
            r'\b\w+\s+(?:Ltd|Limited|Inc|Corporation|Corp|Pvt)\b',
            r'\b\w+\s+(?:Private|Public)\s+Limited\b'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, document, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))
    
    def _identify_problematic_clauses(self, document: str) -> List[Dict[str, str]]:
        """Identify potentially problematic clauses"""
        problematic = []
        
        # Simple keyword-based detection
        problematic_keywords = [
            ("unlimited liability", "Unlimited liability clause detected"),
            ("no warranties", "Disclaimer of warranties may be problematic"),
            ("penalty", "Penalty clause requires review"),
            ("termination without cause", "Termination clause may be unfair")
        ]
        
        doc_lower = document.lower()
        for keyword, issue in problematic_keywords:
            if keyword in doc_lower:
                problematic.append({
                    'keyword': keyword,
                    'issue': issue,
                    'severity': 'medium'
                })
        
        return problematic
    
    def _check_compliance_patterns(self, document: str) -> List[str]:
        """Check for compliance patterns in document"""
        patterns = []
        
        compliance_indicators = [
            "in accordance with",
            "as per regulations",
            "subject to approval",
            "regulatory compliance"
        ]
        
        doc_lower = document.lower()
        for indicator in compliance_indicators:
            if indicator in doc_lower:
                patterns.append(f"Found compliance reference: {indicator}")
        
        return patterns
    
    def _assess_overall_document_compliance(self, analysis_results: List[Dict[str, Any]]) -> str:
        """Assess overall document compliance"""
        total_issues = sum(len(result['problematic_clauses']) for result in analysis_results)
        
        if total_issues == 0:
            return "Good compliance"
        elif total_issues <= 2:
            return "Minor issues detected"
        else:
            return "Significant compliance issues"

class RiskAssessmentEngine:
    """Assesses compliance risks and their impact"""
    
    def assess_risks(self, legal_analysis: Dict[str, Any], 
                    document_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Assess various compliance risks"""
        
        risks = []
        
        # 1. Legal compliance risks
        legal_risks = self._assess_legal_risks(legal_analysis)
        risks.extend(legal_risks)
        
        # 2. Document risks (if available)
        if document_analysis:
            document_risks = self._assess_document_risks(document_analysis)
            risks.extend(document_risks)
        
        # 3. Operational risks
        operational_risks = self._assess_operational_risks(legal_analysis)
        risks.extend(operational_risks)
        
        return {
            'risks': risks,
            'risk_matrix': self._create_risk_matrix(risks),
            'mitigation_strategies': self._suggest_mitigation_strategies(risks)
        }
    
    def _assess_legal_risks(self, legal_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess legal compliance risks"""
        risks = []
        
        # Risk based on confidence scores
        confidence = legal_analysis.get('confidence_score', 1.0)
        if confidence < 0.7:
            risks.append({
                'type': 'legal_uncertainty',
                'description': 'Low confidence in legal analysis',
                'severity': 'high' if confidence < 0.5 else 'medium',
                'probability': 0.8
            })
        
        # Risk based on conflicts
        conflicts = legal_analysis.get('conflicts', [])
        if conflicts:
            risks.append({
                'type': 'regulatory_conflict',
                'description': f'Found {len(conflicts)} regulatory conflicts',
                'severity': 'high',
                'probability': 0.9
            })
        
        return risks
    
    def _assess_document_risks(self, document_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess document-related risks"""
        risks = []
        
        # Risk based on problematic clauses
        for doc_result in document_analysis.get('document_analyses', []):
            problematic_clauses = doc_result.get('problematic_clauses', [])
            for clause in problematic_clauses:
                risks.append({
                    'type': 'document_clause',
                    'description': clause.get('issue', 'Problematic clause'),
                    'severity': clause.get('severity', 'medium'),
                    'probability': 0.7
                })
        
        return risks
    
    def _assess_operational_risks(self, legal_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess operational compliance risks"""
        risks = []
        
        # Risk based on number of applicable rules
        applicable_rules = legal_analysis.get('applicable_rules', [])
        if len(applicable_rules) > 5:
            risks.append({
                'type': 'complexity',
                'description': 'High regulatory complexity',
                'severity': 'medium',
                'probability': 0.6
            })
        
        return risks
    
    def _create_risk_matrix(self, risks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Create risk matrix categorized by severity"""
        matrix = {
            'high': [],
            'medium': [],
            'low': []
        }
        
        for risk in risks:
            severity = risk.get('severity', 'low')
            matrix[severity].append(risk['description'])
        
        return matrix
    
    def _suggest_mitigation_strategies(self, risks: List[Dict[str, Any]]) -> List[str]:
        """Suggest mitigation strategies for identified risks"""
        strategies = []
        
        risk_types = set(risk['type'] for risk in risks)
        
        mitigation_map = {
            'legal_uncertainty': 'Seek additional legal consultation',
            'regulatory_conflict': 'Resolve conflicts through hierarchy analysis',
            'document_clause': 'Review and revise problematic clauses',
            'complexity': 'Implement compliance management system'
        }
        
        for risk_type in risk_types:
            if risk_type in mitigation_map:
                strategies.append(mitigation_map[risk_type])
        
        return strategies
