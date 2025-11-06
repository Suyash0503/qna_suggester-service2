import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  // Change this to your FastAPI backend URL
  private readonly API_BASE = 'http://127.0.0.1:8000/api/v1';

  constructor(private http: HttpClient) {}

  /**
   * Upload a resume file (PDF or DOCX)
   */
  UploadResume(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post(`${this.API_BASE}/resume/upload/resume`, formData);
  }

  /**
   * Upload a job description (if needed later)
   */
  UploadJob(title: string, description: string): Observable<any> {
    const body = { title, description };
    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    return this.http.post(`${this.API_BASE}/job/upload`, body, { headers });
  }

  /**
   * Analyze resume + job description
   */
  AnalyzeResume(resumeKey: string, jdKey: string): Observable<any> {
    const body = { resume_key: resumeKey, jd_key: jdKey };
    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    return this.http.post(`${this.API_BASE}/analyze/analyze`, body, { headers });
  }
}
