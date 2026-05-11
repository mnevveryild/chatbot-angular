import { bootstrapApplication } from '@angular/platform-browser';
import 'zone.js'; // Bu satırın en üstte olduğundan emin ol
import { appConfig } from './app/app.config';
import { App } from './app/app';

bootstrapApplication(App, appConfig)
  .catch((err) => console.error(err));