import { Routes } from '@angular/router';
import { LoginComponent } from './login/login';
import { ChatComponent } from './chat/chat';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'chat', component: ChatComponent },
];