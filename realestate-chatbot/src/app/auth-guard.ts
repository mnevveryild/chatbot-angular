import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth';

export const authGuard: CanActivateFn = () => {

  // auth servisi istek
  const auth = inject(AuthService);
  const router = inject(Router);
  // kullanıcı giriş yapmış mı kontrolü
  if (auth.isLoggedIn()) return true;
  // giriş yapmamışsa login sayfasına yönlendir
  return router.createUrlTree(['/login']);
};