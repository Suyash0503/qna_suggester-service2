import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-resume-upload',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './resume-upload.component.html',
  styleUrl: './resume-upload.component.css'
})
export class ResumeUploadComponent {
  selectedFile: File | null = null;
  uploadResult: any = null;
  constructor(private api: ApiService){}
  onFileSelected(event:any):void{
    this.selectedFile = event.target.files[0];
  }

  onUpload(): void{
    if(!this.selectedFile){
      alert('Please upload a file first! ');
      return;
    }
    this.api.UploadResume(this.selectedFile).subscribe({
      next: res =>{
      console.log('Your file has been uploaded successfully!', res);
      this.uploadResult = res;
      },
      error: err => {
        console.log('Upload Failed:', err);
        alert('upload failed. check again!')
      }
    });
  }
}
