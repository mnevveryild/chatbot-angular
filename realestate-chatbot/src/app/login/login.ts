import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../auth';
import { ChatService } from '../chat'; // ← ekle (kendi path'ine göre düzenle)
import { CommonModule } from '@angular/common';

type Mode = 'login' | 'register' | 'forgot';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class LoginComponent {
  mode = signal<Mode>('login');
  loading = signal(false);
  error = signal('');
  success = signal('');

  email = '';
  password = '';
  name = '';
  confirmPassword = '';
  forgotEmail = '';

  constructor(
    private auth: AuthService,
    private router: Router,
    private chatService: ChatService // ← ekle
  ) {}

  setMode(m: Mode) {
    this.mode.set(m);
    this.error.set('');
    this.success.set('');
  }

  async onLogin() {
    this.error.set('');

    if (!this.email || !this.password) {
      this.error.set('Lütfen e-posta ve şifrenizi girin.');
      return;
    }

    this.loading.set(true);

    try {
      const result = await this.auth.login(this.email, this.password);

      if (result.success) {
        // ← Login sonrası gerçek user ID'yi ChatService'e aktar
        const userId = Number(this.auth.currentUser()?.id);
        if (userId) {
          this.chatService.setUserId(userId);
        }
        this.router.navigate(['/chat']);
      } else {
        this.error.set(result.error || 'Giriş yapılamadı.');
      }
    } finally {
      this.loading.set(false);
    }
  }

  async onRegister() {
    this.error.set('');

    if (this.password !== this.confirmPassword) {
      this.error.set('Şifreler birbiriyle eşleşmiyor.');
      return;
    }

    if (!this.name || !this.email || !this.password) {
      this.error.set('Lütfen tüm alanları doldurun.');
      return;
    }

    this.loading.set(true);

    try {
      const result = await this.auth.register(this.name, this.email, this.password);

      if (result.success) {
        // ← Kayıt sonrası da aynı şekilde ID'yi aktar
        const userId = Number(this.auth.currentUser()?.id);
        if (userId) {
          this.chatService.setUserId(userId);
        }
        this.router.navigate(['/chat']);
      } else {
        this.error.set(result.error || 'Kayıt işlemi başarısız oldu.');
      }
    } finally {
      this.loading.set(false);
    }
  }

  async onForgotPassword() {
    this.error.set('');
    this.success.set('');

    if (!this.forgotEmail) {
      this.error.set('Lütfen e-posta adresinizi girin.');
      return;
    }

    this.loading.set(true);

    try {
      await new Promise(resolve => setTimeout(resolve, 800));
      this.success.set(
        'Eğer bu e-posta ile kayıtlı bir hesap varsa, şifre sıfırlama bağlantısı gönderilecektir.'
      );
    } finally {
      this.loading.set(false);
    }
  }
}