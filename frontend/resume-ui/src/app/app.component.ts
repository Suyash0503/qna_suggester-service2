import { Component } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { ResumeUploadComponent } from './components/resume-upload/resume-upload.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ResumeUploadComponent, HttpClientModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'resume-ui';
}
