import re
import csv
import json
import os

def extract_job_postings(file_path):
    """Extract job postings data from the TypeScript file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract the entire jobPostings array
    match = re.search(r'export const jobPostings = \[([\s\S]*?)\];', content)
    if not match:
        raise ValueError("Could not find jobPostings array in the file")
    
    jobs_text = match.group(1)
    
    # Parse each job posting object
    job_postings = []
    job_pattern = re.compile(r'\{\s*(.*?)\},', re.DOTALL)
    
    for job_match in job_pattern.finditer(jobs_text + "},"):
        job_text = job_match.group(1)
        job = {}
        
        # Extract properties
        job['job_title'] = extract_property(job_text, 'job_title')
        job['salary_min'] = extract_property(job_text, 'salary_min')
        job['salary_max'] = extract_property(job_text, 'salary_max')
        job['company_id'] = extract_property(job_text, 'company_id')
        job['job_description'] = extract_property(job_text, 'job_description')
        job['position'] = extract_property(job_text, 'position')
        job['yof'] = extract_property(job_text, 'yof')
        
        # Extract date
        date_match = re.search(r'date_posted: new Date\("([^"]+)"\)', job_text)
        if date_match:
            job['date_posted'] = date_match.group(1)
        else:
            job['date_posted'] = ""
        
        # Extract skills array
        skills_match = re.search(r'skills: \[(.*?)\]', job_text, re.DOTALL)
        if skills_match:
            skills_text = skills_match.group(1)
            # Extract individual skills
            skills = re.findall(r'"([^"]+)"', skills_text)
            job['skills'] = ";".join(skills)
        else:
            job['skills'] = ""
        
        job_postings.append(job)
    
    return job_postings

def extract_property(text, property_name):
    """Extract a property value from job text."""
    match = re.search(rf'{property_name}: ["\'"]?([^,"\'"]+)["\'"]?,', text)
    if match:
        return match.group(1)
    
    # Try multi-line string pattern
    match = re.search(rf'{property_name}:\s*"([^"]*)"', text)
    if match:
        return match.group(1)
    
    return ""

def save_to_csv(job_postings, output_file):
    """Save job postings to a CSV file."""
    fieldnames = [
        'job_title', 'salary_min', 'salary_max', 'company_id', 
        'job_description', 'position', 'yof', 'date_posted', 'skills'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(job_postings)

# Main execution
if __name__ == "__main__":
    input_file = "IT_Job.ts"
    output_file = "job_postings.csv"
    
    try:
        job_postings = extract_job_postings(input_file)
        save_to_csv(job_postings, output_file)
        print(f"Successfully converted {len(job_postings)} job postings to {output_file}")
    except Exception as e:
        print(f"Error: {e}") 