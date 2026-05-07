import { Component, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../auth';
import { ChatService } from '../chat';
import { CommonModule } from '@angular/common';

type Mode = 'login' | 'register' | 'forgot';

const ALLOWED_DOMAINS = [
  'gmail.com', 'icloud.com', 'yandex.com',
  'yahoo.com', 'outlook.com', 'hotmail.com'
];

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
  newPassword = '';
  confirmNewPassword = ''

  constructor(
    private auth: AuthService,
    private router: Router,
    private chatService: ChatService
  ) {}

  setMode(m: Mode) {
    this.mode.set(m);
    this.error.set('');
    this.success.set('');
  }

  // ── Validasyon yardımcıları ──────────────────────────────────────────────

  isEmailDomainValid(emailVal: string): boolean {
    const parts = emailVal.toLowerCase().split('@');
    if (parts.length !== 2) return false;
    return ALLOWED_DOMAINS.includes(parts[1]);
  }

  get emailDomainHint(): string {
    if (!this.email || !this.email.includes('@')) return '';
    if (this.isEmailDomainValid(this.email)) return '';
    return `Yalnızca şu uzantılar kabul edilir: ${ALLOWED_DOMAINS.map(d => '@' + d).join(', ')}`;
  }

  get passwordHasUpper(): boolean {
    return /[A-Z]/.test(this.password);
  }

  get passwordHasLower(): boolean {
    return /[a-z]/.test(this.password);
  }

  get passwordHasDigit(): boolean {
    return /\d/.test(this.password);
  }

  get passwordHint(): string {
    if (!this.password) return '';
    const hints: string[] = [];
    if (!this.passwordHasUpper) hints.push('büyük harf');
    if (!this.passwordHasLower) hints.push('küçük harf');
    if (!this.passwordHasDigit) hints.push('rakam');
    if (this.password.length < 6) hints.push('en az 6 karakter');
    if (hints.length === 0) return '';
    return `Şifre ${hints.join(', ')} içermelidir.`;
  }

  // Şifre sıfırlama için aynı kontroller
  get newPasswordHint(): string {
    if (!this.newPassword) return '';
    const hints: string[] = [];
    if (!/[A-Z]/.test(this.newPassword)) hints.push('büyük harf');
    if (!/[a-z]/.test(this.newPassword)) hints.push('küçük harf');
    if (!/\d/.test(this.newPassword)) hints.push('rakam');
    if (this.newPassword.length < 6) hints.push('en az 6 karakter');
    if (hints.length === 0) return '';
    return `Şifre ${hints.join(', ')} içermelidir.`;
  }

  get forgotEmailHint(): string {
    if (!this.forgotEmail || !this.forgotEmail.includes('@')) return '';
    if (this.isEmailDomainValid(this.forgotEmail)) return '';
    return `Yalnızca şu uzantılar kabul edilir: ${ALLOWED_DOMAINS.map(d => '@' + d).join(', ')}`;
  }

  // ── Actions ──────────────────────────────────────────────────────────────

  async onLogin() {
    this.error.set('');

    if (!this.email || !this.password) {
      this.error.set('Lütfen e-posta ve şifrenizi girin.');
      return;
    }

    if (!this.isEmailDomainValid(this.email)) {
      this.error.set(`Geçersiz e-posta uzantısı. Kabul edilenler: ${ALLOWED_DOMAINS.map(d => '@' + d).join(', ')}`);
      return;
    }

    this.loading.set(true);

    try {
      const result = await this.auth.login(this.email, this.password);

      if (result.success) {
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

    if (!this.name || !this.email || !this.password) {
      this.error.set('Lütfen tüm alanları doldurun.');
      return;
    }

    if (!this.isEmailDomainValid(this.email)) {
      this.error.set(`Geçersiz e-posta uzantısı. Kabul edilenler: ${ALLOWED_DOMAINS.map(d => '@' + d).join(', ')}`);
      return;
    }

    if (this.passwordHint) {
      this.error.set(this.passwordHint);
      return;
    }

    if (this.password !== this.confirmPassword) {
      this.error.set('Şifreler birbiriyle eşleşmiyor.');
      return;
    }

    this.loading.set(true);

    try {
      const result = await this.auth.register(this.name, this.email, this.password);

      if (result.success) {
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

    if (!this.isEmailDomainValid(this.forgotEmail)) {
      this.error.set(`Geçersiz e-posta uzantısı. Kabul edilenler: ${ALLOWED_DOMAINS.map(d => '@' + d).join(', ')}`);
      return;
    }

    if (!this.newPassword || !this.confirmNewPassword) {
      this.error.set('Lütfen yeni şifrenizi iki kez girin.');
      return;
    }

    if (this.newPasswordHint) {
      this.error.set(this.newPasswordHint);
      return;
    }

    if (this.newPassword !== this.confirmNewPassword) {
      this.error.set('Yeni şifreler birbiriyle eşleşmiyor.');
      return;
    }

    this.loading.set(true);

    try {
      const result = await this.auth.resetPassword(this.forgotEmail, this.newPassword);
      if (result.success) {
        this.success.set(result.message || 'Şifreniz başarıyla güncellendi.');
        this.email = this.forgotEmail;
        this.password = '';
        this.newPassword = '';
        this.confirmNewPassword = '';
      } else {
        this.error.set(result.error || 'Şifre güncellenemedi.');
      }
    } finally {
      this.loading.set(false);
    }
  }
}
