import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Pipe({ name: 'markdownLink', standalone: true })
export class MarkdownLinkPipe implements PipeTransform {
  constructor(private sanitizer: DomSanitizer) {}

  transform(text: string): SafeHtml {
    if (!text) return '';

    // 1) Markdown linkleri HTML <a> etiketine çevir: [metin](url)
    //    Hem http/https ile başlayanları hem de www. ile başlayan protokolsüz URL'leri destekle
    let html = text.replace(
      /\[([^\]]+)\]\(((?:https?:\/\/|www\.)[^\)]+)\)/g,
      (_, label, url) => {
        const href = url.startsWith('http') ? url : 'https://' + url;
        return `<a href="${href}" target="_blank" rel="noopener noreferrer" class="chat-link">${label}</a>`;
      }
    );

    // 2) **kalın** metni <strong> ile işaretle
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // 3) Satır sonlarını <br> ile değiştir
    html = html.replace(/\n/g, '<br>');

    return this.sanitizer.bypassSecurityTrustHtml(html);
  }
}

