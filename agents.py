from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import json
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Define Pydantic structures for agent outputs

class CandidateProfile(BaseModel):
    name: str = Field(description="Full name of the candidate")
    email: str = Field(description="Email address of the candidate")
    phone: str = Field(description="Phone number of the candidate")
    skills: List[str] = Field(description="List of core technical and soft skills")
    experience_summary: str = Field(description="A brief summary of candidate's professional experience")
    education: List[str] = Field(description="Degrees, certifications, and educational history")
    projects: List[str] = Field(description="Key projects or professional accomplishments")
    target_roles: List[str] = Field(description="Potential job titles the candidate is qualified for")

class JobMatch(BaseModel):
    title: str = Field(description="Job title of the posting")
    company: str = Field(description="Company offering the job (estimate if not explicitly in text)")
    href: str = Field(description="URL link to the job posting")
    body: str = Field(description="Original job description snippet")
    match_score: int = Field(description="Evaluation score from 0 to 100 representing how well candidate matches the requirements")
    strengths: List[str] = Field(description="Key skills/experiences the candidate has that match this job")
    gaps: List[str] = Field(description="Requirements from the job description that the candidate is missing")
    recommendation: str = Field(description="Recommendation, one of: 'Strong Match', 'Good Match', 'Stretch Role', 'Not Recommended'")

class JobEvaluationResult(BaseModel):
    evaluations: List[JobMatch] = Field(description="Evaluation of all searched job postings")

class CoverLetterResult(BaseModel):
    subject: str = Field(description="Subject line for the cover letter / email")
    body: str = Field(description="The complete, tailored cover letter body text")
    tailored_skills_highlighted: List[str] = Field(description="List of specific skills highlighted in this cover letter to match the job requirements")


# Agent Classes

class ResumeProfilerAgent:
    def __init__(self, client: genai.Client, model: str = "gemini-2.5-flash"):
        self.client = client
        self.model = model

    def profile(self, resume_text: str) -> CandidateProfile:
        prompt = f"""
        You are an expert Resume Profiler Agent. Your task is to analyze the candidate's resume text 
        and extract structured information about their profile.
        
        Resume text:
        ---
        {resume_text}
        ---
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CandidateProfile,
                system_instruction="You are a meticulous ATS (Applicant Tracking System) parser and talent acquisition specialist. Extract candidate details precisely.",
                temperature=0.1
            )
        )
        # Parse output as candidate profile
        return CandidateProfile.model_validate_json(response.text)


class JobSearcherAgent:
    def __init__(self, client: genai.Client, model: str = "gemini-2.5-flash"):
        self.client = client
        self.model = model

    def generate_search_query(self, profile: CandidateProfile, desired_role: str) -> str:
        prompt = f"""
        Based on the candidate's profile and desired role, generate a single optimized web search query 
        to find relevant job postings (e.g. 'Python developer backend job hiring'). 
        Keep the query concise, under 6 words, focusing on the core keywords.
        
        Desired Role: {desired_role}
        Skills: {', '.join(profile.skills[:5])}
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are a Job Search Expert. Generate a single highly focused search query. Output only the query text without quotes or explanation.",
                temperature=0.2
            )
        )
        return response.text.strip().replace('"', '')


class JobMatcherAgent:
    def __init__(self, client: genai.Client, model: str = "gemini-2.5-flash"):
        self.client = client
        self.model = model

    def evaluate_matches(self, profile: CandidateProfile, jobs: List[dict]) -> JobEvaluationResult:
        jobs_json = json.dumps(jobs, indent=2)
        profile_json = profile.model_dump_json(indent=2)
        
        prompt = f"""
        You are a Job Matcher Agent. Evaluate the candidate's profile against each of the following job postings.
        For each job posting, calculate a match score (0-100), identify the candidate's strengths relative to it, 
        list any key skill gaps, and provide a recommendation.
        
        Candidate Profile:
        {profile_json}
        
        Job Postings:
        {jobs_json}
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=JobEvaluationResult,
                system_instruction="You are a professional Tech Recruiter. Objectively assess matches between candidates and job postings, pointing out exact gaps and alignments.",
                temperature=0.2
            )
        )
        return JobEvaluationResult.model_validate_json(response.text)


class CoverLetterWriterAgent:
    def __init__(self, client: genai.Client, model: str = "gemini-2.5-flash"):
        self.client = client
        self.model = model

    def write_cover_letter(self, profile: CandidateProfile, job: JobMatch) -> CoverLetterResult:
        profile_json = profile.model_dump_json(indent=2)
        job_json = job.model_dump_json(indent=2)
        
        prompt = f"""
        You are a Cover Letter Writer Agent. Write a highly tailored, professional, and compelling cover letter 
        on behalf of the candidate for the following job posting. Highlight the candidate's key strengths 
        that directly match the job requirements, and write in a confident, professional, and natural tone (avoiding overly flowery AI cliches).
        
        Candidate Profile:
        {profile_json}
        
        Target Job:
        {job_json}
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CoverLetterResult,
                system_instruction="You are an expert Career Coach and Copywriter. Create personalized, persuasive cover letters that get candidates interviews.",
                temperature=0.3
            )
        )
        return CoverLetterResult.model_validate_json(response.text)
