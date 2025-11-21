from typing import List, Optional
from datetime import datetime
from loguru import logger
from models import (
    QuestionRequest, QuestionResponse, Citation
)
from services import (
    chroma_service, ollama_service
)
from config import settings

class QATutorAgent:
    """
    Q&A Tutor Agent - Answers course questions with citations.
    Retrieves relevant context from local database and optionally from web.
    """
    """
    Q&A Tutor Agent - Answers course questions with citations.
    Retrieves relevant context from local database and optionally from web.
    """
    
    def __init__(self):
        """
        Initialize QATutorAgent with ChromaDB and Ollama services.
        """
        self.chroma = chroma_service
        self.ollama = ollama_service
    
    def _create_citation(
        self,
        source: str,
        content: str,
        distance: float,
        metadata: dict
    ) -> Citation:
        """
        Create a citation object from search results.
        """
        """Create a citation object from search results."""
        return Citation(
            source=source,
            content=content[:500] + "..." if len(content) > 500 else content,
            page=metadata.get('page'),
            url=metadata.get('url'),
            confidence=1.0 - distance  # Convert distance to confidence
        )
    
    def _check_relevance_to_network_security(self, question: str) -> tuple[bool, float]:
        """
        Check if the question is related to network security.
        Returns (is_relevant, confidence_score)
        """
        """
        Check if the question is related to network security.
        Returns (is_relevant, confidence_score)
        """
        network_security_keywords = [
            'network', 'security', 'firewall', 'encryption', 'vpn', 'attack', 'malware',
            'virus', 'threat', 'vulnerability', 'authentication', 'authorization', 'ssl',
            'tls', 'https', 'intrusion', 'ddos', 'phishing', 'cryptography', 'cipher',
            'protocol', 'tcp', 'ip', 'dns', 'router', 'switch', 'packet', 'port',
            'password', 'hash', 'certificate', 'penetration', 'exploit', 'backdoor',
            'ransomware', 'trojan', 'worm', 'botnet', 'ipsec', 'nmap', 'wireshark',
            'ids', 'ips', 'siem', 'zero-day', 'mitm', 'man-in-the-middle', 'access control',
            'firewall', 'proxy', 'gateway', 'dmz', 'vlan', 'subnet', 'wifi', 'wireless',
            'bluetooth', 'key', 'public key', 'private key', 'digital signature', 'pki',
            'aes', 'rsa', 'des', '3des', 'sha', 'md5', 'diffie-hellman'
        ]
        
        question_lower = question.lower()
        keyword_count = sum(1 for keyword in network_security_keywords if keyword in question_lower)
        
        # Consider it relevant if it contains network security keywords
        is_relevant = keyword_count > 0
        confidence = min(keyword_count * 0.2, 1.0)  # Each keyword adds 20% confidence
        
        return is_relevant, confidence

    def answer_question(
        self,
        request: QuestionRequest
    ) -> QuestionResponse:
        """
        Answer a user question using RAG approach.
        
        Args:
            request: QuestionRequest containing the question and options
            
        Returns:
            QuestionResponse with answer and citations
        """
        question = request.question
        logger.info(f"Processing question: {question}")
        
        # Check if question is related to network security
        is_relevant, relevance_confidence = self._check_relevance_to_network_security(question)
        
        # Step 1: Retrieve relevant context from local database
        # Reduce the number of retrieved contexts and truncate them to lower
        # latency and prompt size.
        local_results = self.chroma.query_similar(
            query_text=question,
            n_results=2
        )
        
        citations = []
        context_texts = []
        
        # Process local results
        if local_results['documents'] and local_results['documents'][0]:
            for idx, (doc, metadata, distance) in enumerate(zip(
                local_results['documents'][0],
                local_results['metadatas'][0],
                local_results['distances'][0]
            )):
                # Truncate long document chunks to 512 characters to keep
                # the LLM prompt small and fast.
                truncated = doc if len(doc) <= 512 else doc[:512] + '...'
                context_texts.append(truncated)
                citations.append(
                    self._create_citation(
                        source=metadata.get('source', f'Document {idx+1}'),
                        content=doc,
                        distance=distance,
                        metadata=metadata
                    )
                )
        
        # Step 2: Generate answer using LLM with context
        if not context_texts:
            # No relevant context found
            if not is_relevant:
                # Question is not related to network security
                system_prompt = """You are a knowledgeable AI assistant. 
Answer the question briefly and accurately.
At the end of your answer, add a disclaimer noting that this question is not related to network security."""
                
                try:
                    general_answer = ollama_service.generate(
                        prompt=question,
                        system_prompt=system_prompt,
                        temperature=0.5
                    )
                    answer = f"{general_answer}\n\n⚠️ **Note:** This question appears to be outside the scope of network security. This system is primarily designed to answer network security-related questions. For best results, please ask questions related to network security topics."
                    confidence_score = 0.3
                    # Clear citations for out-of-context questions
                    citations = []
                except Exception as e:
                    logger.error(f"Error generating answer: {e}")
                    answer = "I encountered an error while generating the answer. Please try again."
                    confidence_score = 0.0
                    citations = []
            else:
                answer = "I don't have enough information in my knowledge base to answer this question accurately. Please try rephrasing your question."
                confidence_score = 0.0
        else:
            # Check relevance of retrieved context
            avg_distance = sum(local_results['distances'][0]) / len(local_results['distances'][0]) if local_results['distances'][0] else 1.0
            context_is_relevant = avg_distance < 0.7  # Lower distance means more relevant
            
            if not is_relevant and not context_is_relevant:
                # Question is clearly off-topic and context doesn't help
                system_prompt = """You are a knowledgeable AI assistant. 
Answer the question briefly based on general knowledge.
Keep your answer concise."""
                
                try:
                    general_answer = ollama_service.generate(
                        prompt=question,
                        system_prompt=system_prompt,
                        temperature=0.5
                    )
                    answer = f"{general_answer}\n\n⚠️ **Note:** This question is not related to network security. This system is specialized in network security topics. For more accurate and detailed answers on network security, please ask questions within that domain."
                    confidence_score = 0.4
                    # Clear citations for out-of-context questions
                    citations = []
                except Exception as e:
                    logger.error(f"Error generating answer: {e}")
                    answer = "I encountered an error while generating the answer. Please try again."
                    confidence_score = 0.0
                    citations = []
            else:
                # Question is relevant or we have good context
                system_prompt = """You are a knowledgeable Network Security tutor. 
Answer questions accurately based on the provided context. 
If the context doesn't contain the answer, say so clearly.
Be concise but thorough in your explanations.
Include technical details when relevant. Always give the answers within a 150-200 token range and complete the answer."""
                
                try:
                    answer = ollama_service.generate_with_context(
                        query=question,
                        context=context_texts,
                        system_prompt=system_prompt,
                        temperature=0.3  # Lower temperature for more factual answers
                    )
                    
                    
                    confidence_score = min(citations[0].confidence if citations else 0.5, 1.0)
                except Exception as e:
                    logger.error(f"Error generating answer: {e}")
                    answer = "I encountered an error while generating the answer. Please try again."
                    confidence_score = 0.0
        
        return QuestionResponse(
            question=question,
            answer=answer,
            citations=citations,
            confidence_score=confidence_score,
            timestamp=datetime.now()
        )

# Singleton instance
qa_tutor_agent = QATutorAgent()
