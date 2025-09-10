"""
Defines tasks that orchestrate the multi-agent workflow
"""

from crewai import Task, Agent
from typing import List, Dict, Any


class RegulatoryTaskFactory:
    """Factory for creating regulatory compliance tasks"""
    
    def __init__(self, agents: Dict[str, Agent]):
        self.agents = agents
    
    def create_query_routing_task(self, user_query: str) -> Task:
        """Create task for routing and initial analysis"""
        return Task(
            description=(
                f"Analyze this regulatory query and route it to appropriate specialists:\n"
                f"Query: {user_query}\n\n"
                "Your responsibilities:\n"
                "1. Determine the primary regulatory domain(s) involved\n"
                "2. Use the RAG tool to search for relevant documents\n"
                "3. If multiple domains are involved, identify ALL relevant areas\n"
                "4. Provide initial context and route to appropriate specialist(s)\n"
                "5. Ensure you have gathered sufficient regulatory context\n"
                "6. NEVER proceed without proper citations from official sources\n\n"
                "Available domains:\n"
                "- RBI/FEMA: Banking regulations, foreign exchange, FDI\n"
                "- Companies Act: Corporate governance, compliance, filings\n"
                "- SEBI: Securities law, capital markets, disclosure\n"
                "- Customs/Trade: Import/export, trade policy, tariffs\n"
                "- Document Analysis: Contract review, compliance analysis\n\n"
                "Your output should include:\n"
                "- Domain classification\n"
                "- Relevant regulatory context found\n"
                "- Routing decision with justification\n"
                "- Initial citations from the database"
            ),
            expected_output=(
                "A comprehensive routing analysis including:\n"
                "1. Domain classification (primary and secondary)\n"
                "2. Relevant regulatory context with citations\n"
                "3. Routing decision and specialist assignment\n"
                "4. Initial assessment of query complexity\n"
                "5. All findings must include proper citations"
            ),
            agent=self.agents['router'],
            output_file=None
        )
    
    def create_specialist_analysis_task(self, domain: str, context: str) -> Task:
        """Create task for specialist analysis"""
        agent_map = {
            'rbi_fema': self.agents['rbi_fema'],
            'companies_act': self.agents['companies_act'],
            'sebi': self.agents['sebi'],
            'customs_trade': self.agents['customs_trade'],
            'document_analyzer': self.agents['document_analyzer']
        }
        
        specialist_agent = agent_map.get(domain, self.agents[domain])
        
        return Task(
            description=(
                f"Provide expert analysis for this {domain} regulatory query:\n"
                f"Context: {context}\n\n"
                "Your responsibilities:\n"
                "1. Use the RAG tool to search for domain-specific regulations\n"
                "2. Analyze the query against current regulatory requirements\n"
                "3. Provide specific, actionable guidance\n"
                "4. Include all relevant citations (act/regulation, section, date)\n"
                "5. Mention compliance deadlines and requirements\n"
                "6. Highlight any penalties for non-compliance\n"
                "7. Flag any recent regulatory changes\n"
                "8. NEVER provide advice without proper citations\n\n"
                "Required output elements:\n"
                "- Regulatory analysis with specific citations\n"
                "- Compliance requirements and timelines\n"
                "- Risk assessment and mitigation strategies\n"
                "- Practical implementation guidance\n"
                "- All recommendations must be cited"
            ),
            expected_output=(
                f"Expert {domain} analysis including:\n"
                "1. Detailed regulatory assessment with citations\n"
                "2. Specific compliance requirements\n"
                "3. Risk analysis and mitigation strategies\n"
                "4. Implementation roadmap with timelines\n"
                "5. All advice backed by proper citations\n"
                "6. Penalty implications for non-compliance"
            ),
            agent=specialist_agent,
            output_file=None
        )
    
    def create_document_analysis_task(self, document_content: str, 
                                    analysis_type: str = "general") -> Task:
        """Create task for document compliance analysis"""
        return Task(
            description=(
                f"Analyze this legal document for regulatory compliance:\n"
                f"Document Content: {document_content[:1000]}...\n"
                f"Analysis Type: {analysis_type}\n\n"
                "Your responsibilities:\n"
                "1. Use the document analyzer tool to assess compliance\n"
                "2. Identify clauses that may violate regulations\n"
                "3. Search for relevant regulatory provisions using RAG tool\n"
                "4. Provide specific amendment recommendations\n"
                "5. Cite specific regulations that apply to each clause\n"
                "6. Prioritize issues by severity (critical, moderate, minor)\n"
                "7. Suggest alternative language for problematic clauses\n"
                "8. NEVER flag issues without regulatory citations\n\n"
                "Analysis framework:\n"
                "- Clause-by-clause compliance review\n"
                "- Regulatory violation identification\n"
                "- Amendment recommendations with citations\n"
                "- Risk assessment and prioritization\n"
                "- Implementation guidance"
            ),
            expected_output=(
                "Comprehensive document compliance analysis including:\n"
                "1. Executive summary of compliance status\n"
                "2. Detailed clause-by-clause analysis\n"
                "3. Specific regulatory violations identified\n"
                "4. Amendment recommendations with citations\n"
                "5. Risk prioritization matrix\n"
                "6. Implementation timeline for corrections\n"
                "7. All findings backed by proper citations"
            ),
            agent=self.agents['document_analyzer'],
            output_file=None
        )
    
    def create_synthesis_task(self, analysis_results: List[str]) -> Task:
        """Create task for final synthesis and reporting"""
        return Task(
            description=(
                "Synthesize all specialist analyses into a final comprehensive report:\n"
                f"Analysis Results: {analysis_results}\n\n"
                "Your responsibilities:\n"
                "1. Consolidate all specialist inputs into a coherent response\n"
                "2. Validate all citations using the citation validator tool\n"
                "3. Resolve any conflicting recommendations\n"
                "4. Provide clear, actionable recommendations\n"
                "5. Create a compliance checklist for implementation\n"
                "6. Highlight urgent vs. non-urgent requirements\n"
                "7. Include practical implementation guidance\n"
                "8. NEVER include uncited recommendations\n\n"
                "Report structure:\n"
                "- Executive summary\n"
                "- Detailed analysis with citations\n"
                "- Actionable recommendations\n"
                "- Compliance checklist\n"
                "- Implementation timeline\n"
                "- Risk assessment\n"
                "- Limitations and disclaimers"
            ),
            expected_output=(
                "Final comprehensive advisory report including:\n"
                "1. Executive summary with key findings\n"
                "2. Detailed regulatory analysis with all citations\n"
                "3. Prioritized action items with timelines\n"
                "4. Compliance checklist for implementation\n"
                "5. Risk assessment and mitigation strategies\n"
                "6. Clear disclaimers about analysis limitations\n"
                "7. Next steps and recommended follow-up actions\n"
                "8. All recommendations properly cited and validated"
            ),
            agent=self.agents['synthesis'],
            output_file=None
        )
    
    def create_multi_domain_task(self, user_query: str, domains: List[str]) -> List[Task]:
        """Create tasks for multi-domain queries"""
        tasks = []
        
        # Create routing task
        routing_task = self.create_query_routing_task(user_query)
        tasks.append(routing_task)
        
        # Create specialist tasks for each domain
        for domain in domains:
            specialist_task = self.create_specialist_analysis_task(domain, user_query)
            tasks.append(specialist_task)
        
        # Create synthesis task
        synthesis_task = self.create_synthesis_task([])
        tasks.append(synthesis_task)
        
        return tasks
    
    def create_workflow_for_query(self, user_query: str, query_type: str = "general") -> List[Task]:
        """Create appropriate workflow based on query type"""
        
        if query_type == "document_analysis":
            return [
                self.create_document_analysis_task(user_query),
                self.create_synthesis_task([])
            ]
        
        elif query_type == "multi_domain":
            return self.create_multi_domain_task(user_query, ["rbi_fema", "companies_act"])
        
        else:
            # single domain
            return [
                self.create_query_routing_task(user_query),
                self.create_specialist_analysis_task("rbi_fema", user_query),
                self.create_synthesis_task([])
            ]


class TaskOrchestrator:
    def __init__(self, task_factory: RegulatoryTaskFactory):
        self.task_factory = task_factory
    
    def determine_query_type(self, user_query: str) -> str:
        """Determine the type of query to create appropriate workflow"""
        query_lower = user_query.lower()
        
        if any(term in query_lower for term in ["analyze", "review", "document", "agreement", "contract"]):
            return "document_analysis"
        
        domain_count = 0
        domains = ["rbi", "fema", "companies", "sebi", "customs", "trade"]
        for domain in domains:
            if domain in query_lower:
                domain_count += 1
        
        if domain_count > 1:
            return "multi_domain"
        
        return "general"
    
    def create_workflow(self, user_query: str) -> List[Task]:
        query_type = self.determine_query_type(user_query)
        return self.task_factory.create_workflow_for_query(user_query, query_type)
    
    def add_task_dependencies(self, tasks: List[Task]) -> List[Task]:
        """Add context dependencies between tasks"""
        for i in range(1, len(tasks)):
            tasks[i].context = tasks[:i]  # Each task depends on previous tasks
        
        return tasks
