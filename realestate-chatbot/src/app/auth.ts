import { Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private _currentUser = signal<User | null>(null);
  currentUser = this._currentUser.asReadonly();
  isLoggedIn = signal(false);

  constructor(private router: Router) {
    const stored = sessionStorage.getItem('re_user');
    if (stored) {
      const user = JSON.parse(stored);
      this._currentUser.set(user);
      this.isLoggedIn.set(true);
    }
  }

  login(email: string, password: string): Promise<{ success: boolean; error?: string }> {
    return new Promise(resolve => {
      setTimeout(() => {
        if (email && password.length >= 6) {
          const user: User = {
            id: crypto.randomUUID(),
            email,
            name: email.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
          };
          this._currentUser.set(user);
          this.isLoggedIn.set(true);
          sessionStorage.setItem('re_user', JSON.stringify(user));
          resolve({ success: true });
        } else {
          resolve({ success: false, error: 'Invalid credentials. Please try again.' });
        }
      }, 900);
    });
  }

  register(name: string, email: string, password: string): Promise<{ success: boolean; error?: string }> {
    return new Promise(resolve => {
      setTimeout(() => {
        if (name && email && password.length >= 6) {
          const user: User = { id: crypto.randomUUID(), email, name };
          this._currentUser.set(user);
          this.isLoggedIn.set(true);
          sessionStorage.setItem('re_user', JSON.stringify(user));
          resolve({ success: true });
        } else {
          resolve({ success: false, error: 'Please fill all fields. Password must be 6+ characters.' });
        }
      }, 900);
    });
  }

  logout(): void {
    this._currentUser.set(null);
    this.isLoggedIn.set(false);
    sessionStorage.removeItem('re_user');
    this.router.navigate(['/login']);
  }
}