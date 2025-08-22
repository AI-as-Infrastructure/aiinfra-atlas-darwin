<template>
  <section class="section">
    <div class="container">
      <h1 class="title faq-title-black">FAQ</h1>
      
      <div class="faq-list">
        <div 
          v-for="(faq, index) in faqs" 
          :key="index" 
          class="faq-item"
        >
          <button 
            class="faq-question" 
            :class="{ 'open': openItems[index] }"
            @click="toggleItem(index)"
          >
            <span>{{ faq.question }}</span>
            <span class="faq-toggle">{{ openItems[index] ? '−' : '+' }}</span>
          </button>
          <div v-if="openItems[index]" class="faq-answer">
            <div v-html="faq.answer"></div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue';

const faqs = [
  {
    question: "What is ATLAS and what is its purpose?",
    answer: `
      <p>
        ATLAS (Analysis and Testing of Language Models for Archival Systems) is a research platform designed to explore how large language models and AI can enhance historical research using archival collections. This instance provides AI-assisted access to historical correspondence and documents.
      </p>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Core Purpose</h4>

      <ul style="color: black;">
        <li style="color: black;"><strong style="color: black;">Research Tool:</strong> <span style="color: black;">Providing scholars with AI-assisted access to historical archives for research</span></li>
        <li style="color: black;"><strong style="color: black;">Educational Framework:</strong> <span style="color: black;">Helping researchers understand the nature of LLM technology and AI product development through direct experience with historical texts</span></li>
        <li style="color: black;"><strong style="color: black;">Experimental Platform:</strong> <span style="color: black;">Creating a controlled environment to evaluate different AI approaches to historical text analysis</span></li>
        <li style="color: black;"><strong style="color: black;">Methodological Investigation:</strong> <span style="color: black;">Studying how researchers interact with AI systems when conducting historical research</span></li>
        <li style="color: black;"><strong style="color: black;">Technical Framework:</strong> <span style="color: black;">Developing best practices for hybrid search (dense + sparse) RAG systems in humanities computing</span></li>
        <li style="color: black;"><strong style="color: black;">Open Source Continuation:</strong> <span style="color: black;">Exploring the feasibility of continuing traditions of open source software development in digital humanities</span></li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Key Features</h4>
      <ul style="color: black;">
        <li style="color: black;"><strong style="color: black;">Historical Document Access:</strong> <span style="color: black;">Hybrid search across archival collections with rich metadata and structured content</span></li>
        <li style="color: black;"><strong style="color: black;">Historical Language Models:</strong> <span style="color: black;">Using models trained on period-appropriate text for optimal historical language understanding</span></li>
        <li style="color: black;"><strong style="color: black;">Rich Metadata:</strong> <span style="color: black;">Structured encoding of person names, places, organizations, and subject-specific terms with canonical URLs</span></li>
        <li style="color: black;"><strong style="color: black;">Scholarly Citations:</strong> <span style="color: black;">Automatic generation of proper scholarly citations with archival locations and permanent identifiers</span></li>
        <li style="color: black;"><strong style="color: black;">Hybrid Search:</strong> <span style="color: black;">Combines dense vector search (semantic similarity) with BM25 lexical search (exact term matching) for optimal recall</span></li>
      </ul>
    `
  },
  {
    question: "What is Hybrid Search RAG and how does it work in ATLAS?",
    answer: `
      <p>
        ATLAS uses a Hybrid Search RAG (Retrieval Augmented Generation) architecture that combines multiple search methods to find the most relevant passages from historical sources before generating answers:
      </p>
      <ul>
        <li><strong>Dense Vector Search:</strong> Uses semantic embeddings to find conceptually related content, even when different words are used</li>
        <li><strong>Sparse BM25 Search:</strong> Performs exact term matching to ensure precise terminology, names, and phrases are captured</li>
        <li><strong>Reciprocal Rank Fusion:</strong> Combines results from both methods using advanced scoring to balance semantic similarity with lexical precision</li>
        <li><strong>Context Enhancement:</strong> The fused results provide the LLM with the most relevant historical sources as context for generating historically grounded responses</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Why Hybrid Search for Historical Sources?</h4>
      <p>
        Historical documents present unique challenges that hybrid search addresses:
      </p>
      <ul>
        <li><strong>Subject Terminology:</strong> Dense vectors capture semantic relationships while BM25 ensures exact technical terms and names are found</li>
        <li><strong>Historical Language:</strong> Vector search handles language evolution while lexical search preserves period-specific terminology</li>
        <li><strong>Person Names:</strong> Semantic search finds name variations while BM25 matches exact spellings</li>
        <li><strong>Geographic References:</strong> Dense search connects related locations while sparse search finds precise place names</li>
        <li><strong>Document Networks:</strong> Vector embeddings reveal conceptual connections while BM25 matches specific names and terms</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Limitations and Challenges</h4>
      <p>
        Despite its benefits, hybrid search RAG has important limitations:
      </p>
      <ul>
        <li><strong>Context Window Constraints:</strong> The amount of retrieved information is limited by the LLM's context window</li>
        <li><strong>Retrieval Quality Dependency:</strong> Both search methods must find relevant content; poor retrieval affects answer quality</li>
        <li><strong>Hallucination Risk:</strong> LLMs may generate information not found in the historical sources when context is insufficient</li>
        <li><strong>Historical Terminology Gaps:</strong> Some historical terms may not be well-represented in modern training data</li>
        <li><strong>Complex Reasoning:</strong> Multi-hop reasoning across multiple documents remains challenging</li>
        <li><strong>Citation Boundaries:</strong> The system may struggle with conflicting information across different sources or time periods</li>
      </ul>
      
      <p>
        ATLAS uses hybrid search RAG to provide scholars with AI-assisted access to historical archives, generating historically grounded responses with proper scholarly citations while maintaining computational efficiency compared to alternatives.
      </p>
    `
  },
  {
    question: "How does ATLAS manage data privacy?",
    answer: `
      <p>
        ATLAS is designed with privacy considerations at its core, using a stateless architecture that minimizes data retention:
      </p>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Authentication System</h4>
      <ul>
        <li><strong>AWS Cognito Integration:</strong> ATLAS uses AWS Cognito for secure authentication, which handles user credentials without exposing them to the application</li>
        <li><strong>No Stored Login Data:</strong> User login information is validated through Cognito but not stored persistently in ATLAS systems</li>
        <li><strong>Session-Based Access:</strong> Authentication generates temporary session tokens rather than storing persistent user identifiers</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Telemetry and Analytics</h4>
      <ul>
        <li><strong>Anonymous Usage Data:</strong> Interaction telemetry is collected without personally identifiable information</li>
        <li><strong>Arize Phoenix Integration:</strong> Data is sent to Arize Phoenix for monitoring system performance, not user behavior</li>
        <li><strong>Observation Identifiers:</strong> Random identifiers are generated for each session without being linked to user accounts</li>
        <li><strong>Limited Retention:</strong> Only minimal data necessary for system improvement is retained</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Stateless Architecture</h4>
      <ul>
        <li><strong>No Chat History Storage:</strong> Conversations exist only within the current session and are not persisted after the session ends</li>
        <li><strong>Ephemeral Processing:</strong> Queries and results are processed in memory and not written to permanent storage</li>
        <li><strong>Cache Expiration:</strong> Any temporary caching of responses uses short expiration times</li>
        <li><strong>No User Profiles:</strong> The system does not build or maintain profiles of users or their query patterns</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Limitations and Considerations</h4>
      <p>
        While ATLAS prioritizes privacy, users should be aware of certain limitations:
      </p>
      <ul>
        <li><strong>Small User Base:</strong> The limited number of users means that complete anonymization is challenging—specific query patterns could potentially be identifiable in a small group</li>
        <li><strong>Research Context:</strong> As a research platform, some aggregated data about system performance and query types is necessary for research publications</li>
        <li><strong>Third-Party Dependencies:</strong> The system relies on external services (AWS, Arize) that have their own privacy policies and data handling practices</li>
        <li><strong>Administrative Access:</strong> System administrators may have access to logs for troubleshooting purposes, though these are kept to a minimum</li>
      </ul>
      
      <p>
        This privacy-centric approach aligns with ATLAS's research goals while respecting user confidentiality—allowing researchers to interact with historical parliamentary materials without concerns about persistent tracking or data retention.
      </p>
    `
  },
  {
    question: "Why do some questions seem ineffective while others produce high quality results?",
    answer: `
      <p>
        This is probably the biggest limitation of the current LLM RAG (Retrieval Augmented Generation) architecture, which uses HNSW vector search for document retrieval and LLM inferencing for question answering.
      </p>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">The Core Issue</h4>
      <p>
        There's a disconnect between what the LLM understands semantically and what the HNSW search system can find. For example:
      </p>
      <br>
      <ul>
        <li><strong>Query that might produce poor results:</strong> "What parliamentary discussions addressed Aboriginal affairs in 1901?" → No or few results found</li>
        <li><strong>Query that is more liklely to succeed:</strong> "Describe the debates related to Maori and the Treaty of Waitangi in New Zealand" → Rich, detailed results</li>
      </ul>
      <br>
      <p>
        Both queries ask about Indigenous peoples, but the search system performs literal matching rather than leveraging the LLM's semantic understanding that these are related topics. Depending on the specific terms used, the search may fail to retrieve relevant documents, leading to poor or no results. This is similar to the problem of 'prompt engineering', where the way a question is phrased can significantly impact the quality of the answer when quering LLMs, but is compounded by the fact that the LLM cannot communicate back to the search system to suggest alternative terms.
      </p>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Why This Happens</h4>
      <ul>
        <li><strong>Historical Terminology:</strong> Documents use period-specific language that may not match modern search terms</li>
        <li><strong>One-Way Communication:</strong> The LLM cannot communicate back to the search system to suggest alternative terms</li>
        <li><strong>Lexical vs Semantic Search:</strong> The current system relies more on exact word matching than conceptual understanding</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Current Status & Roadmap</h4>
      <p>
        While this isn't a major issue for the current phase of the project (which focuses on developing our understanding of testing and evaluation), it is on our roadmap for future improvement. We're tracking this issue and potential solutions on <a href="https://github.com/AI-as-Infrastructure/aiinfra-atlas/issues/35" target="_blank" rel="noopener noreferrer">GitHub #35</a>.
      </p>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Tips for Better Results</h4>
      <ul>
        <li><strong>Try historical terminology:</strong> "Aboriginal affairs" → "Native affairs" or "Māori"</li>
        <li><strong>Be specific about countries:</strong> "Australian Parliament" or "New Zealand Parliament"</li>
        <li><strong>Use multiple approaches:</strong> If one query fails, try rephrasing with different terms</li>
        <li><strong>Browse different time periods:</strong> Terminology evolved over time</li>
      </ul>
    `
  },
  {
    question: "How do multi-turn conversations work in ATLAS?",
    answer: `
      <p>
        In ATLAS, each new question in a multi-turn conversation:
      </p>
      <ul>
        <li><strong>Gets Fresh Context:</strong> The system retrieves new document context for each query independently, rather than reusing context from previous turns. This is standard RAG behavior that prioritizes accuracy for each question.</li>
        <li><strong>Maintains Conversation History:</strong> While document context is refreshed, the chat history (previous Q&A pairs) is preserved and sent to the LLM with each new query, allowing it to understand the conversation flow.</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Relationship Between Multi-turn Answers, Context, and Citations</h4>
      <p>
        The relationship works like this:
      </p>
      <ul>
        <li><strong>Context Retrieval Per Question:</strong> Each new user question triggers a fresh vector search, retrieving documents relevant to the current question only.</li>
        <li><strong>Citations Follow Current Context:</strong> The citations shown to users directly reflect the documents retrieved for the current question, not previous questions.</li>
        <li><strong>LLM Creates Coherent Narrative:</strong> The LLM receives:
          <ul>
            <li>The current question</li>
            <li>The newly retrieved context</li>
            <li>The full conversation history</li>
          </ul>
        </li>
        <li><strong>Contextual Understanding:</strong> The LLM can refer to previous answers when forming responses, but its citations are limited to documents retrieved for the current question.</li>
      </ul>
    `
  },
  {
    question: "What data sources does ATLAS use?",
    answer: `
      <p>
        ATLAS provides access to historical document collections that have been processed into vector embeddings to enable semantic search. The specific content depends on the ATLAS instance configuration.
      </p>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Archival Collections</h4>
      <ul>
        <li><strong>Historical Documents:</strong> Letters, manuscripts, and other archival materials from established research collections</li>
        <li><strong>Structured Encoding:</strong> XML markup with metadata for persons, places, organizations, and subject-specific terms</li>
        <li><strong>Scholarly Standards:</strong> Professionally edited content with archival locations and canonical URLs for citation</li>
        <li><strong>Temporal Coverage:</strong> Collections spanning specific historical periods relevant to the research focus</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Rich Metadata</h4>
      <ul>
        <li><strong>Network Analysis:</strong> Information about relationships between historical figures and institutions</li>
        <li><strong>Geographic Data:</strong> Locations mentioned in sources with historical context</li>
        <li><strong>Subject Terms:</strong> Domain-specific terminology and concepts with structured encoding</li>
        <li><strong>Chronological Context:</strong> Precise dates linking documents to historical developments</li>
      </ul>
      
      <p>
        All content is processed using hybrid search to enable both semantic exploration of concepts and precise retrieval of specific names, places, and technical terms.
      </p>
    `
  },
  {
    question: "How does corpus filtering work in ATLAS?",
    answer: `
      <p>
        ATLAS instances can be configured as either single-corpus or multi-corpus systems depending on the research needs:
      </p>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Single Corpus Systems</h4>
      <ul>
        <li><strong>Unified Collections:</strong> All documents treated as one cohesive archive</li>
        <li><strong>Comprehensive Search:</strong> Every query searches across the entire collection without need for filtering</li>
        <li><strong>Simplified Interface:</strong> Users don't need to choose between different document types or sources</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Multi-Corpus Systems</h4>
      <ul>
        <li><strong>Collection Filtering:</strong> Dropdown selector allows users to focus on specific document collections</li>
        <li><strong>Balanced Retrieval:</strong> When searching "All" sources, system retrieves equal numbers from each corpus</li>
        <li><strong>Metadata-Based:</strong> Filtering applied at the vector database level using corpus metadata tags</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Alternative Filtering Approaches</h4>
      <p>
        In single-corpus systems, you can still focus your searches using natural language:
      </p>
      <ul>
        <li><strong>Temporal Filtering:</strong> Specify time periods in your queries ("documents from the 1860s", "after major publication")</li>
        <li><strong>Person Filtering:</strong> Search for documents to/from specific people or involving particular individuals</li>
        <li><strong>Topic Filtering:</strong> Focus on specific subject areas relevant to the collection</li>
        <li><strong>Hybrid Search Benefits:</strong> The system automatically finds both semantic matches and exact name/date matches</li>
      </ul>
      
      <p>
        This approach provides natural, research-oriented ways to explore historical collections without artificial corpus boundaries.
      </p>
    `
  },
  {
    question: "How does ATLAS's hybrid search work technically?",
    answer: `
      <p>
        ATLAS combines two complementary search technologies to provide optimal retrieval from historical sources:
      </p>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Dense Vector Search (HNSW)</h4>
      <ul>
        <li><strong>Algorithm:</strong> HNSW (Hierarchical Navigable Small World) provides extremely fast approximate nearest neighbor search in high-dimensional vector spaces</li>
        <li><strong>Historical Embeddings:</strong> Uses embedding models trained on period-appropriate text for optimal historical language understanding</li>
        <li><strong>Semantic Matching:</strong> Finds conceptually related content even when different terminology is used</li>
        <li><strong>Chroma Storage:</strong> Vector database with HNSW indexing for sub-millisecond search performance</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Sparse Lexical Search (BM25)</h4>
      <ul>
        <li><strong>Algorithm:</strong> Best Matching 25 (BM25) for precise term frequency analysis and exact matching</li>
        <li><strong>Lexical Precision:</strong> Captures specific names, scientific terms, and exact phrases that embeddings might miss</li>
        <li><strong>Complement to Vectors:</strong> Ensures retrieval of documents with exact terminology matches</li>
        <li><strong>Pre-computed Index:</strong> BM25 corpus stored as <code>bm25_corpus.jsonl</code> for fast lookup</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Reciprocal Rank Fusion (RRF)</h4>
      <p>
        The fusion process combines results from both search methods:
      </p>
      <ul>
        <li><strong>RRF Scoring:</strong> Uses formula <code>score = 1/(rank + k)</code> where k=60 balances rank position importance</li>
        <li><strong>Result Merging:</strong> Combines unique documents from both searches, summing RRF scores for duplicates</li>
        <li><strong>Balanced Weighting:</strong> Equal importance given to semantic similarity and lexical precision</li>
        <li><strong>Final Ranking:</strong> Top results sent to LLM ensure both conceptual relevance and exact term matches</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Configurable Parameters</h4>
      <ul>
        <li><strong>Search K Value:</strong> Number of final documents sent to LLM (configurable per instance)</li>
        <li><strong>Vector Candidates:</strong> Initial candidates from dense search (typically 100-200)</li>
        <li><strong>BM25 Candidates:</strong> Similar number from lexical search for balance</li>
        <li><strong>Chunking Strategy:</strong> Document segmentation optimized for the specific document types</li>
        <li><strong>Rich Metadata:</strong> Structured entities and canonical URLs included in context</li>
      </ul>
      
      <p>
        This hybrid approach ensures researchers receive both conceptually related passages and exact terminological matches, with proper scholarly citations from authoritative sources.
      </p>
    `
  },
  {
    question: "How do historical language models improve ATLAS searches?",
    answer: `
      <p>
        ATLAS can use historical language models specifically trained on period-appropriate text to improve search quality for historical documents:
      </p>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Historical Language Training</h4>
      <ul>
        <li><strong>Period-Specific Models:</strong> BERT models pre-trained on text from relevant historical periods</li>
        <li><strong>Contextual Understanding:</strong> Better comprehension of historical terminology, social conventions, and period-specific language</li>
        <li><strong>Language Evolution:</strong> Captures how terminology and usage changed over time</li>
      </ul>

      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Search Benefits</h4>
      <ul>
        <li><strong>Domain Terminology:</strong> Better understanding of subject-specific terms from the historical period</li>
        <li><strong>Document Conventions:</strong> Improved comprehension of historical writing conventions and formalities</li>
        <li><strong>Name Recognition:</strong> Better handling of historical person names and their various forms</li>
        <li><strong>Context Sensitivity:</strong> Understanding of how concepts were discussed before modern standardization</li>
      </ul>

      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Technical Implementation</h4>
      <ul>
        <li><strong>Advanced Pooling:</strong> Pooling strategies optimized for historical language models</li>
        <li><strong>High-Dimensional Vectors:</strong> Dense embeddings capturing nuanced semantic relationships</li>
        <li><strong>Hybrid Compatibility:</strong> Works seamlessly with BM25 lexical search for comprehensive retrieval</li>
        <li><strong>Hardware Optimization:</strong> Includes fallback mechanisms for different hardware configurations</li>
      </ul>
      
      <p>
        These historically-trained models ensure that searches for period concepts find semantically related discussions even when historical sources used different terminology or phrasing conventions of their era.
      </p>
    `
  },
  {
    question: "How can I get the best search results in ATLAS?",
    answer: `
      <p>
        To get the most relevant results when searching historical sources in ATLAS:
      </p>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Query Formulation</h4>
      <ul>
        <li><strong>Use Historical Terminology:</strong> Consider period-appropriate language and terminology when possible</li>
        <li><strong>Include Context:</strong> Reference specific works, events, or periods relevant to your research</li>
        <li><strong>Be Specific:</strong> Use precise terms when available rather than general categories</li>
        <li><strong>Include Names:</strong> Mention specific people or places for focused results</li>
      </ul>

      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Leveraging Hybrid Search</h4>
      <ul>
        <li><strong>Conceptual Queries:</strong> Ask about broad concepts - the dense vector search will find semantically related discussions</li>
        <li><strong>Specific Names/Terms:</strong> The BM25 component ensures exact matches for person names, place names, and technical terms</li>
        <li><strong>Multiple Approaches:</strong> Try both broad conceptual queries and specific terminology-focused searches</li>
        <li><strong>Temporal Context:</strong> Include years or decades to focus on specific historical periods</li>
      </ul>

      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Interpreting Results</h4>
      <ul>
        <li><strong>Check Document Dates:</strong> Note chronology to understand historical development over time</li>
        <li><strong>Verify Metadata:</strong> Review structured information about people, places, and concepts</li>
        <li><strong>Use Canonical URLs:</strong> Citations include authoritative links for scholarly verification</li>
        <li><strong>Cross-Reference Topics:</strong> Look for patterns across multiple documents and sources</li>
      </ul>

      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Example Effective Query Patterns</h4>
      <ul>
        <li><strong>"[Concept] in correspondence with [Person]"</strong> - Combines topic with specific individuals</li>
        <li><strong>"[Subject area] work [decade]"</strong> - Historical context with temporal focus</li>
        <li><strong>"[Specific process/event] experiments"</strong> - Targeted research activities</li>
        <li><strong>"Personal letters about [topic]"</strong> - Informal discussions of subjects</li>
      </ul>

      <p>
        The hybrid search architecture means you'll get both conceptually related content (even with different terminology) and exact matches for names and specific terms, providing comprehensive coverage of the historical sources.
      </p>
    `
  },
  {
    question: "How do citations work in ATLAS?",
    answer: `
      <p>
        ATLAS provides rich, scholarly citations that link directly to authoritative sources:
      </p>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Scholarly Citation Format</h4>
      <ul>
        <li><strong>Source Integration:</strong> Citations include proper formatting with authoritative project identifiers</li>
        <li><strong>Canonical URLs:</strong> Each citation links to the official source collection page</li>
        <li><strong>Complete Metadata:</strong> Dates, participants, archival locations, and document IDs for scholarly verification</li>
        <li><strong>Structured Enhancement:</strong> Person names, places, organizations, and subject terms are properly formatted</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Interactive Citation Features</h4>
      <ul>
        <li><strong>Hover Previews:</strong> Mouse over citation numbers to see document content and metadata</li>
        <li><strong>Full Text Modal:</strong> Click citations to open complete document text with archival details</li>
        <li><strong>Truncation Notices:</strong> Longer documents show truncation indicators with full content available</li>
        <li><strong>Direct Links:</strong> Every citation includes a link to the authoritative source page</li>
      </ul>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Research-Quality Citations</h4>
      <ul>
        <li><strong>Archival Standards:</strong> Include repository information and institutional affiliations</li>
        <li><strong>Chronological Context:</strong> Clear dating to understand historical development</li>
        <li><strong>Participant Information:</strong> Full names and relationships relevant to the documents</li>
        <li><strong>Publication Details:</strong> Volume and page numbers where applicable</li>
      </ul>
      
      <p>
        Citations follow established scholarly formats appropriate to the source collection, ensuring proper attribution and verification paths for research use.
      </p>
      
      <p>
        ATLAS shows a configurable number of citations per answer (typically 10-20), prioritizing the most relevant sources identified through hybrid search.
      </p>
    `
  },
  {
    question: "What is the feedback system for?",
    answer: `
      <p>
        The feedback system in ATLAS serves multiple important purposes:
      </p>
      <ul>
        <li><strong>Research Value:</strong> Collecting user assessments of answer quality to study how scholars evaluate AI-generated historical analysis</li>
        <li><strong>System Improvement:</strong> Identifying patterns in low-rated answers to improve retrieval and prompting strategies</li>
        <li><strong>Model Comparison:</strong> Gathering comparative data between different LLM configurations and settings</li>
        <li><strong>Educational Tool:</strong> Helping users reflect on the strengths and limitations of AI assistance in historical research</li>
      </ul>
      <p>
        After each answer, you can rate its quality and provide optional written feedback. This data is anonymized and used purely for research and system improvement purposes.
      </p>
    `
  },
  {
    question: "How do embeddings and pooling work in ATLAS?",
    answer: `
      <p>
        ATLAS uses word embeddings and pooling techniques to convert text into numerical vectors that capture semantic meaning:
      </p>
      
      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Word Embeddings</h4>
      <ul>
        <li><strong>Living with Machines Model:</strong> ATLAS defaults to using a BERT model pre-trained on 19th-century text, providing a strong foundation for historical language understanding. You can use a different model by changing the <code>EMBEDDING_MODEL</code> in the Test Target configuration.</li>
        <li><strong>Vector Representation:</strong> Each word or token is converted into a high-dimensional vector that captures its meaning and relationships with other words</li>
        <li><strong>Contextual Understanding:</strong> The model considers the surrounding words to generate context-aware embeddings</li>
      </ul>

      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Pooling Strategies</h4>
      <ul>
        <li><strong>Mean Pooling:</strong> The default strategy that averages all word embeddings in a document to create a single document vector</li>
        <li><strong>Fine-tuned Pooling:</strong> An enhanced approach where the model is fine-tuned on parliamentary records to better capture domain-specific language patterns</li>
        <li><strong>Fallback Mechanism:</strong> If fine-tuned model files aren't available, the system automatically uses mean pooling</li>
      </ul>

      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Role in RAG Chain</h4>
      <ul>
        <li><strong>Document Indexing:</strong> All parliamentary records are converted into embeddings and stored in the vector database</li>
        <li><strong>Query Processing:</strong> User queries are converted into embeddings using the same model</li>
        <li><strong>Semantic Search:</strong> The system finds documents with similar embeddings to the query</li>
        <li><strong>Context Retrieval:</strong> The most semantically similar documents are retrieved and passed to the LLM</li>
      </ul>

      <h4 style="color: black; font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1.2rem;">Fine-tuning Benefits</h4>
      <ul>
        <li><strong>Historical Language:</strong> Better understanding of historical terminology</li>
        <li><strong>Domain Adaptation:</strong> Improved ability to capture the specific context of parliamentary debates</li>
        <li><strong>Enhanced Retrieval:</strong> More accurate matching of queries to relevant historical documents</li>
      </ul>

      <p>
        The combination of historical language models, effective pooling strategies, and fine-tuning creates a robust foundation for semantic search in ATLAS, enabling accurate retrieval of relevant parliamentary records.
      </p>
    `
  }
];

// Initialize all items as closed
const openItems = ref(faqs.map(() => false));

// Toggle function to open/close FAQ items
const toggleItem = (index) => {
  openItems.value[index] = !openItems.value[index];
};
</script>

<style scoped>
.title, .faq-title-black {
  color: black !important;
}

.faq-list {
  margin-top: 2rem;
}

.faq-item {
  margin-bottom: 1rem;
  background: white;
  border-radius: 0.5rem;
  border: 1px solid #e0e0e0;
  overflow: hidden;
}

.faq-question {
  width: 100%;
  padding: 1.5rem;
  background: white !important;
  border: none;
  color: black !important;
  font-size: 1.25rem;
  font-weight: 600;
  text-align: left;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s;
}

.faq-question:hover {
  background: rgba(0, 0, 0, 0.05);
}


.faq-question.open {
  background: white;
  border-bottom: 1px solid #cbd5e1;
}

.faq-toggle {
  font-size: 1.5rem;
  color: black;
  transition: transform 0.2s;
}

.faq-answer {
  padding: 1.5rem;
  color: black !important;
  background-color: white;
}

.faq-answer * {
  color: black !important;
}

.faq-answer h4 {
  color: black !important;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  font-size: 1.25rem;
  font-weight: 600;
}

.faq-answer p {
  margin-bottom: 1rem;
}

.faq-answer ul, .faq-answer ol {
  margin-bottom: 1rem;
  padding-left: 1.5rem;
}

.faq-answer li {
  margin-bottom: 0.5rem;
}

.faq-answer strong {
  color: black !important;
  font-weight: bold;
}

.faq-answer code {
  background-color: #f8f8f8;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-family: monospace;
  font-size: 0.9em;
  color: black;
}
</style> 