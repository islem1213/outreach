import os
from orchestrator import PipelineOrchestrator

def main():
    api_key = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6I2So0Wt16RxhOV6IC2O-AQqj4mGmesz70Xm1Dy2jXFVQ")
    if not api_key:
        print("API Key not found!")
        return

    print("Initializing Orchestrator...")
    orchestrator = PipelineOrchestrator(api_key=api_key)
    
    mock_resume = """
    Jane Doe
    jane.doe@example.com | (555) 019-2834 | Paris, France
    
    Professional Summary:
    Experienced Python Software Engineer with 6 years of expertise building scalable backend systems, APIs, and microservices. Well-versed in FastAPI, Django, PostgreSQL, Docker, and AWS. Proven track record of optimizing database performance and leading small developer teams.
    
    Skills:
    - Programming: Python, SQL, Bash
    - Frameworks: FastAPI, Django, Flask, Streamlit
    - Databases: PostgreSQL, Redis, MongoDB
    - DevOps: Docker, Git, AWS (S3, EC2, RDS), CI/CD
    
    Work Experience:
    Senior Software Engineer | TechSolutions SAS (2022 - Present)
    - Designed and implemented high-throughput APIs using FastAPI, reducing response latency by 35%.
    - Migrated legacy microservices to a Dockerized infrastructure, streamlining development and deployment.
    - Mentored 3 junior developers and established code review guidelines.
    
    Software Engineer | WebApp Corp (2020 - 2022)
    - Developed backend features for e-commerce platforms using Django and PostgreSQL.
    - Designed database schemas and optimized complex SQL queries, improving page load speeds by 20%.
    
    Education:
    M.S. in Computer Science | Université de Paris (2018 - 2020)
    B.S. in Software Engineering | Université de Paris (2015 - 2018)
    """

    desired_role = "Senior Python Developer"
    
    print("\nRunning multi-agent pipeline...")
    
    def progress_cb(step, status, details):
        msg = details.get("message", "") if details else ""
        print(f"[{step.upper()} - {status.upper()}] {msg}")
        
    try:
        results = orchestrator.run(
            resume_text=mock_resume,
            desired_role=desired_role,
            progress_cb=progress_cb
        )
        
        print("\n=== PIPELINE SUCCESS ===")
        print(f"Name: {results['profile'].name}")
        print(f"Email: {results['profile'].email}")
        print(f"Query generated: {results['search_query']}")
        print(f"Jobs evaluated: {len(results['evaluations'])}")
        
        for idx, job in enumerate(results['evaluations']):
            print(f"  {idx+1}. {job.title} at {job.company} - Match: {job.match_score}% - Recommendation: {job.recommendation}")
            
        print("\n=== BEST MATCH ===")
        best = results['best_job']
        print(f"Title: {best.title}")
        print(f"Company: {best.company}")
        
        print("\n=== COVER LETTER ===")
        print(f"Subject: {results['cover_letter'].subject}")
        print("Body preview:")
        print("\n".join(results['cover_letter'].body.splitlines()[:5]) + "\n...")
        
    except Exception as e:
        print(f"\nPipeline failed: {e}")

if __name__ == "__main__":
    main()
