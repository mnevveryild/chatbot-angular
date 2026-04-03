import { Routes } from '@angular/router';
import { authGuard } from './auth-guard';

export const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  {
    path: 'login',
    loadComponent: () => import('./login/login').then(m => m.LoginComponent)
  },
  {
    path: 'chat',
    loadComponent: () => import('./chat/chat').then(m => m.ChatComponent),
    canActivate: [authGuard]
  },
  { path: '**', redirectTo: '/login' }
];