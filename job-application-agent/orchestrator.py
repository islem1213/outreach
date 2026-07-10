from google import genai
import logging
from typing import Callable, Optional, Dict, Any, List
from agents import (
    ResumeProfilerAgent, 
    JobSearcherAgent, 
    JobMatcherAgent, 
    CoverLetterWriterAgent, 
    CandidateProfile, 
    JobEvaluationResult, 
    CoverLetterResult
)
from utils import search_jobs

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=api_key)
        
        # Instantiate agents
        self.profiler = ResumeProfilerAgent(self.client, self.model)
        self.searcher = JobSearcherAgent(self.client, self.model)
        self.matcher = JobMatcherAgent(self.client, self.model)
        self.writer = CoverLetterWriterAgent(self.client, self.model)

    def run(
        self, 
        resume_text: str, 
        desired_role: str, 
        progress_cb: Optional[Callable[[str, str, Optional[Dict[str, Any]]], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes the entire job application pipeline.
        
        progress_cb: callback function with signature (step_name, status, details_dict)
                     status is typically 'start', 'success', or 'error'
        """
        results = {}

        def update_progress(step: str, status: str, details: Optional[Dict[str, Any]] = None):
            if progress_cb:
                progress_cb(step, status, details)

        # Step 1: Resume Profiling
        try:
            update_progress("profiler", "start", {"message": "Extracting candidate profile from resume..."})
            profile: CandidateProfile = self.profiler.profile(resume_text)
            results["profile"] = profile
            update_progress("profiler", "success", {
                "message": "Candidate profile successfully extracted.",
                "profile": profile.model_dump()
            })
        except Exception as e:
            logger.error(f"Error in ResumeProfilerAgent: {e}")
            update_progress("profiler", "error", {"message": f"Failed to profile resume: {str(e)}"})
            raise e

        # Step 2: Job Searching
        try:
            update_progress("searcher", "start", {"message": "Generating optimized search query..."})
            search_query = self.searcher.generate_search_query(profile, desired_role)
            results["search_query"] = search_query
            
            update_progress("searcher", "start", {"message": f"Searching jobs for query: '{search_query}'..."})
            raw_jobs = search_jobs(search_query)
            results["raw_jobs"] = raw_jobs
            update_progress("searcher", "success", {
                "message": f"Found {len(raw_jobs)} relevant job postings.",
                "query": search_query,
                "jobs": raw_jobs
            })
        except Exception as e:
            logger.error(f"Error in JobSearcherAgent: {e}")
            update_progress("searcher", "error", {"message": f"Failed to search jobs: {str(e)}"})
            raise e

        # Step 3: Job Evaluation & Matching
        try:
            update_progress("matcher", "start", {"message": "Matching profile against found job postings..."})
            match_results: JobEvaluationResult = self.matcher.evaluate_matches(profile, raw_jobs)
            results["evaluations"] = match_results.evaluations
            
            # Sort evaluations by match score descending
            sorted_evals = sorted(match_results.evaluations, key=lambda x: x.match_score, reverse=True)
            results["evaluations"] = sorted_evals
            
            update_progress("matcher", "success", {
                "message": "Job matching complete.",
                "evaluations": [e.model_dump() for e in sorted_evals]
            })
        except Exception as e:
            logger.error(f"Error in JobMatcherAgent: {e}")
            update_progress("matcher", "error", {"message": f"Failed to evaluate jobs: {str(e)}"})
            raise e

        # Step 4: Cover Letter Generation (for best matching job)
        if not results.get("evaluations"):
            update_progress("writer", "error", {"message": "No jobs found to write a cover letter for."})
            results["cover_letter"] = None
            return results

        best_job = results["evaluations"][0]
        results["best_job"] = best_job
        
        try:
            update_progress("writer", "start", {"message": f"Writing cover letter for best match: '{best_job.title}' at {best_job.company}..."})
            cover_letter: CoverLetterResult = self.writer.write_cover_letter(profile, best_job)
            results["cover_letter"] = cover_letter
            update_progress("writer", "success", {
                "message": "Cover letter generated successfully.",
                "cover_letter": cover_letter.model_dump()
            })
        except Exception as e:
            logger.error(f"Error in CoverLetterWriterAgent: {e}")
            update_progress("writer", "error", {"message": f"Failed to write cover letter: {str(e)}"})
            raise e

        return results
