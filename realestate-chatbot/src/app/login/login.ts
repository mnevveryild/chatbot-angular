import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../auth';
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
    private router: Router
  ) {}

  setMode(m: Mode) {
    this.mode.set(m);
    this.error.set('');
    this.success.set('');
  }

  async onLogin() {
    this.error.set('');

    // Basit boşluk kontrolü
    if (!this.email || !this.password) {
      this.error.set('Lütfen e-posta ve şifrenizi girin.');
      return;
    }

    this.loading.set(true);

    try {
      const result = await this.auth.login(this.email, this.password);

      if (result.success) {
        this.router.navigate(['/chat']);
      } else {
        this.error.set(result.error || 'Giriş yapılamadı.');
      }
    } finally {
      // Başarılı da olsa hatalı da olsa spinner durur
      this.loading.set(false);
    }
  }

  async onRegister() {
    this.error.set('');

    // Şifre eşleşme kontrolü — loading başlamadan önce
    if (this.password !== this.confirmPassword) {
      this.error.set('Şifreler birbiriyle eşleşmiyor.');
      return; // loading hiç başlamadı, sorun yok
    }

    // Boşluk kontrolü
    if (!this.name || !this.email || !this.password) {
      this.error.set('Lütfen tüm alanları doldurun.');
      return;
    }

    this.loading.set(true);

    try {
      const result = await this.auth.register(this.name, this.email, this.password);

      if (result.success) {
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
      return; // loading başlamadan çıktık, sorun yok
    }

    this.loading.set(true);

    try {
      // Şimdilik simüle ediliyor
      // İleride: await this.auth.sendPasswordReset(this.forgotEmail);
      await new Promise(resolve => setTimeout(resolve, 800));

      this.success.set(
        'Eğer bu e-posta ile kayıtlı bir hesap varsa, şifre sıfırlama bağlantısı gönderilecektir.'
      );
    } finally {
      this.loading.set(false);
    }
  }
}