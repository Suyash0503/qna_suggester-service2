from typing import List, Dict
import time
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# =====================================================
# ✅ Load and Initialize Model
# =====================================================
MODEL_NAME = "MBZUAI/LaMini-Flan-T5-783M"  # Tuned for technical QnA
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
hf_pipeline = pipeline("text2text-generation", model=model, tokenizer=tokenizer)

# =====================================================
# ✅ Predefined Base QnA (fallback)
# =====================================================
QNA_DATA: Dict[str, List[str]] = {
    "python": [
        "What is the difference between a list and a tuple in Python?",
        "Explain the concept of decorators in Python.",
        "How does Python manage memory and garbage collection?",
        "What are Python generators and how are they different from iterators?",
        "Explain the Global Interpreter Lock (GIL) and its implications for multithreading."
    ],
    "fastapi": [
        "How does FastAPI handle async requests internally?",
        "What is dependency injection in FastAPI and how is it implemented?",
        "How can you validate request bodies and query parameters in FastAPI?",
        "Explain how background tasks work in FastAPI.",
        "How would you implement JWT authentication in a FastAPI application?"
    ],
    "docker": [
        "What is the difference between a Docker image and a container?",
        "What is a Docker volume and when would you use one?",
        "Explain the purpose of Dockerfile instructions like FROM, RUN, CMD, and ENTRYPOINT.",
        "How do you reduce the size of a Docker image?",
        "What is the difference between Docker Compose and Docker Swarm?"
    ],
    "data structures": [
        "Explain stack vs queue with examples.",
        "What is the difference between an array and a linked list?",
        "How do you detect a cycle in a linked list?",
        "Explain tree traversal methods (inorder, preorder, postorder).",
        "What is a hash table and how do collisions occur?",
        "How do you find the shortest path in a graph?",
        "What is the difference between BFS and DFS?"
    ],
    "algorithms": [
        "Explain the time and space complexity of merge sort.",
        "What is the difference between quicksort and heapsort?",
        "How would you detect a cycle in a directed graph?",
        "Explain dynamic programming with a real-world example.",
        "What is the difference between greedy and divide-and-conquer algorithms?"
    ],
    "kd tree": [
        "How does a KD-Tree partition multidimensional space?",
        "Explain nearest-neighbor search using KD-Tree.",
        "What is the complexity of KD-Tree construction and search?",
        "Compare KD-Tree and R-Tree for spatial queries.",
        "What are some real-world use cases of KD-Tree in ML or robotics?"
    ],
    "machine learning": [
        "What is the bias-variance trade-off in machine learning?",
        "How do you prevent overfitting in neural networks?",
        "What is gradient descent and how does it work?",
        "Explain the difference between bagging and boosting.",
        "How would you deploy a machine learning model to production?"
    ],
    "optimization": [
        "How would you optimize a slow SQL query?",
        "Explain the difference between time complexity and space complexity.",
        "What strategies can you use to reduce memory consumption in large-scale systems?",
        "How do caching mechanisms improve system performance?",
        "How would you identify and remove performance bottlenecks in an API?"
    ],
    "system design": [
        "How would you design a scalable URL shortener like Bitly?",
        "Explain how load balancing works and why it’s important.",
        "How would you handle database sharding in distributed systems?",
        "What are the trade-offs between consistency and availability in the CAP theorem?",
        "Design a high-throughput messaging system similar to Kafka."
    ],
    "cloud": [
        "What is the difference between IaaS, PaaS, and SaaS?",
        "Explain how auto-scaling works in AWS EC2.",
        "What is Infrastructure as Code (IaC) and how is it implemented using Terraform?",
        "How do you secure credentials and secrets in cloud environments?",
        "What are the benefits of using containers in cloud deployment?"
    ],
    "testing": [
        "What is the difference between unit testing and integration testing?",
        "How do you mock external APIs in automated tests?",
        "What is test-driven development (TDD) and what are its benefits?",
        "How do you ensure good code coverage in your tests?",
        "Explain how to structure CI/CD pipelines for automated testing."
    ]
}

# =====================================================
# ✅ Helper: Clean and Normalize Model Output
# =====================================================
def clean_output(text: str) -> List[str]:
    lines = [ln.strip("•-0123456789. \t") for ln in text.split("\n")]
    valid = []
    for ln in lines:
        if not ln:
            continue
        if "?" in ln or ln.lower().startswith(("how", "why", "when", "where", "explain", "what")):
            valid.append(ln.strip())
    seen = set()
    final = []
    for q in valid:
        s = q.lower()[:60]
        if s not in seen:
            final.append(q)
            seen.add(s)
    return final[:5]

# =====================================================
# ✅ Query Model (with Debug Logging)
# =====================================================
def query_huggingface(prompt: str) -> List[str]:
    try:
        output = hf_pipeline(
            prompt,
            max_new_tokens=200,
            temperature=0.6,
            top_p=0.9,
            do_sample=True
        )[0]["generated_text"].strip()

        cleaned = clean_output(output)
        if len(cleaned) < 2:
            retry_prompt = f"List 5 technical interview questions about {prompt.split()[-1]}"
            retry = hf_pipeline(retry_prompt, max_new_tokens=100)[0]["generated_text"]
            cleaned = clean_output(retry)
        return cleaned or ["⚠️ No strong questions generated."]
    except Exception as e:
        return [f"❌ Local inference failed: {e}"]

# =====================================================
# ✅ Core Logic: Generate Interview Questions (Hybrid)
# =====================================================
def generate_interview_questions(resume_skills: List[str], jd_keywords: List[str], include_suggestions: bool = False) -> Dict:
    all_topics = set(resume_skills + jd_keywords)
    questions = {}

    for topic in all_topics:
        lower = topic.lower()
        topic_questions = []

        # --- Include static QnA if available ---
        if lower in QNA_DATA:
            topic_questions.extend(QNA_DATA[lower])

        # --- Dynamic AI prompts (Hybrid: Technical + Situational Style) ---
        if any(k in lower for k in ["data structure", "algorithm", "complexity", "graph", "tree", "stack", "queue", "sorting"]):
            prompt = (
                f"You are a Google interviewer conducting a Data Structures & Algorithms round. "
                f"Write 5 interview questions about '{topic}' that mix practical coding and situational reasoning. "
                f"Some should start with 'How would you implement...', others with 'What would you do if...', "
                f"and one should involve analyzing trade-offs or debugging logic errors. "
                f"Ensure variety — include one scenario-style question like 'Describe how you'd optimize data lookup in real-time systems'. "
                f"Avoid repetitive HR phrasing like 'Can you describe a time...'."
            )

        elif any(k in lower for k in ["kd tree", "k-d tree", "spatial indexing", "nearest neighbor", "r-tree", "ball tree", "topology"]):
            prompt = (
                f"You are an applied scientist at Amazon conducting a robotics/ML systems interview. "
                f"Write 5 questions about '{topic}', combining 3 technical (partitioning, nearest-neighbor search, high-dimensional optimization) "
                f"and 2 situational ('Describe how you'd handle performance degradation in KD-Tree lookups', 'Explain how you'd redesign it for dynamic data'). "
                f"Each question must reflect real-world applications in ML, GIS, or robotics."
            )

        elif any(k in lower for k in ["system design", "architecture", "distributed", "scalability", "consistency"]):
            prompt = (
                f"You are a Meta system design interviewer. "
                f"Write 5 deep, scenario-based questions about '{topic}'. "
                f"Include realistic trade-offs ('What would you change if traffic increased 100x?'), failure scenarios ('How would you recover from partial outages?'), "
                f"and at least one situational question ('Describe how you'd convince your team to refactor an unscalable component')."
            )

        elif any(k in lower for k in ["ml", "machine learning", "ai", "neural network", "deep learning"]):
            prompt = (
                f"You are an OpenAI ML interviewer assessing technical depth and experience reflection. "
                f"Write 5 questions about '{topic}' that include both analytical and situational context. "
                f"Ask things like 'How would you identify overfitting?', 'What would you do if model drift occurred?', "
                f"and 'Describe how you improved a model deployment under time constraints'. "
                f"Avoid generic HR phrasing, keep questions grounded in ML workflows."
            )

        elif any(k in lower for k in ["optimization", "performance", "throughput", "latency", "efficiency"]):
            prompt = (
                f"You are a performance engineer at Netflix. "
                f"Write 5 technical interview questions about '{topic}' — "
                f"mixing 3 analytical questions ('How would you profile a slow API?', 'What causes latency spikes?') "
                f"and 2 situational ones ('Describe how you'd handle unexpected performance regression before release')."
            )

        elif any(k in lower for k in ["backend", "api", "microservice", "database", "server", "cloud"]):
            prompt = (
                f"You are a senior backend engineer at AWS interviewing for a cloud systems role. "
                f"Write 5 questions about '{topic}' — "
                f"include 3 design or debugging ones ('How would you ensure fault tolerance?', 'What happens if one microservice fails?'), "
                f"and 2 situational leadership-style ones ('Describe a time you scaled a service under tight deadlines', 'How would you handle a deployment rollback in production?')."
            )

        elif any(k in lower for k in ["oauth", "security", "data type", "serialization"]):
            prompt = (
                f"You are a Microsoft security engineer conducting an interview. "
                f"Write 5 questions about '{topic}', combining direct technical ('How would you secure JWT tokens?', 'What encryption algorithms would you use?') "
                f"and scenario-based ('Describe how you'd react if access keys were leaked', 'How would you audit security in a distributed system?')."
            )

        else:
            prompt = (
                f"You are a technical interviewer at a top IT company. "
                f"Write 5 balanced questions about '{topic}', combining technical and situational judgment. "
                f"Use phrasing like 'How would you handle...', 'What steps would you take...', 'Describe your approach when...'. "
                f"All questions should sound like they’re asked by an experienced engineer evaluating both skill and mindset."
            )

        # --- Query Hugging Face Model ---
        ai_questions = query_huggingface(prompt)

        # --- Filter out unwanted HR-style questions ---
        ai_questions = [
            q for q in ai_questions
            if not q.lower().startswith(("can you describe", "tell me about", "give an example"))
        ]

        # --- Merge both (static + AI generated) ---
        merged = list(dict.fromkeys(topic_questions + ai_questions))
        questions[topic] = merged[:6]
        time.sleep(1.0)

    # =====================================================
    # 🧭 General Interview Tips
    # =====================================================
    if include_suggestions:
        questions["general_tips"] = [
            "Always explain your thought process clearly.",
            "Talk through trade-offs before coding — reasoning matters more than speed.",
            "If stuck, verbalize how you'd debug or optimize.",
            "Write clean, readable code — clarity beats cleverness.",
            "Relate your answers to real-world systems or projects."
        ]

    # ✅ RETURN STATEMENT (previously missing)
    return {
        "status": "success",
        "questions": questions
    }
