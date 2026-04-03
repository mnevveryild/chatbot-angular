import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../auth';
import { CommonModule } from '@angular/common';

// Görünüm modları: Giriş, Kayıt, Şifremi Unuttum
type Mode = 'login' | 'register' | 'forgot';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class LoginComponent {
  mode = signal<Mode>('login'); // Mevcut form modu
  loading = signal(false);      // İşlem devam ediyor mu?
  error = signal('');           // Hata mesajı
  success = signal('');         // Başarı mesajı
  
  email = '';
  password = '';
  name = '';
  confirmPassword = '';
  forgotEmail = '';

  constructor(private auth: AuthService, private router: Router) {}

  // Form modları arasında geçiş yap (Giriş <-> Kayıt vb.)
  setMode(m: Mode) {
    this.mode.set(m);
    this.error.set('');
    this.success.set('');
  }

  // Giriş yapma işlemi
  async onLogin() {
    this.error.set('');
    this.loading.set(true);
    const result = await this.auth.login(this.email, this.password);
    this.loading.set(false);
    
    if (result.success) {
      this.router.navigate(['/chat']);
    } else {
      this.error.set(result.error || 'Giriş yapılamadı. Bilgilerinizi kontrol edin.');
    }
  }

  // Yeni hesap oluşturma işlemi
  async onRegister() {
    this.error.set('');
    
    // Şifre eşleşme kontrolü
    if (this.password !== this.confirmPassword) {
      this.error.set('Şifreler birbiriyle eşleşmiyor.');
      return;
    }
    
    this.loading.set(true);
    const result = await this.auth.register(this.name, this.email, this.password);
    this.loading.set(false);
    
    if (result.success) {
      this.router.navigate(['/chat']);
    } else {
      this.error.set(result.error || 'Kayıt işlemi başarısız oldu.');
    }
  }

  // Şifre sıfırlama işlemi
  async onForgotPassword() {
    this.error.set('');
    
    if (!this.forgotEmail) { 
      this.error.set('Lütfen e-posta adresinizi girin.'); 
      return; 
    }
    
    this.loading.set(true);
    // Gerçek bir API olmadığı için kısa bir gecikme simülasyonu
    await new Promise(r => setTimeout(r, 800));
    this.loading.set(false);
    
    this.success.set('Eğer bu e-posta ile kayıtlı bir hesap varsa, şifre sıfırlama bağlantısı gönderilecektir.');
  }
}