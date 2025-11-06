import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';
import { importProvidersFrom } from '@angular/core';
import { bootstrapApplication } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import { ResumeUploadComponent } from './components/resume-upload/resume-upload.component';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
  ],
};

// Bootstrapping the app with your standalone component
bootstrapApplication(AppComponent, {
  providers: [],
}).catch(err => console.error(err));
