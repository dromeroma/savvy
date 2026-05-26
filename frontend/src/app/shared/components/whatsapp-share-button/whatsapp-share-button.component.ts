import { Component, computed, input } from '@angular/core';

/**
 * Botón verde de WhatsApp que abre wa.me con un texto prearmado.
 *
 * Uso (recipient opcional — sin él abre el selector de contacto):
 *   <app-whatsapp-share text="Hola, mira mi factura..." />
 *   <app-whatsapp-share text="..." phone="573001234567" label="Enviar al cobrador" />
 *
 * No depende de la API de WhatsApp; solo enlaces wa.me. El usuario
 * elige a quién enviárselo desde su propio WhatsApp.
 */
@Component({
  selector: 'app-whatsapp-share',
  imports: [],
  template: `
    <a [href]="href()" target="_blank" rel="noopener"
      class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#25D366] hover:bg-[#1DA851] text-white text-xs font-medium transition"
      [title]="label() || 'Compartir por WhatsApp'">
      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20.52 3.48A11.78 11.78 0 0012.04 0C5.5 0 .19 5.31.19 11.85c0 2.09.55 4.13 1.6 5.93L0 24l6.39-1.67a11.84 11.84 0 005.65 1.44h.01c6.54 0 11.85-5.31 11.85-11.85 0-3.17-1.23-6.15-3.48-8.43zM12.05 21.79h-.01a9.94 9.94 0 01-5.07-1.39l-.36-.22-3.79.99 1.01-3.69-.23-.38a9.91 9.91 0 01-1.52-5.25c0-5.47 4.45-9.92 9.93-9.92 2.65 0 5.14 1.03 7.01 2.91a9.84 9.84 0 012.9 7.02c0 5.47-4.45 9.93-9.92 9.93zm5.45-7.43c-.3-.15-1.77-.87-2.04-.97-.27-.1-.47-.15-.67.15-.2.3-.77.97-.94 1.17-.17.2-.34.22-.64.07-.3-.15-1.26-.46-2.4-1.48-.89-.79-1.49-1.77-1.66-2.07-.17-.3-.02-.46.13-.61.13-.13.3-.34.45-.5.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.07-.15-.67-1.62-.92-2.22-.24-.58-.49-.5-.67-.51-.17-.01-.37-.01-.57-.01-.2 0-.52.07-.79.37-.27.3-1.04 1.02-1.04 2.48 0 1.46 1.07 2.88 1.22 3.07.15.2 2.1 3.21 5.08 4.5.71.31 1.26.49 1.69.63.71.23 1.35.19 1.86.12.57-.09 1.77-.72 2.02-1.42.25-.7.25-1.3.17-1.42-.07-.12-.27-.2-.57-.35z"/>
      </svg>
      {{ label() || 'WhatsApp' }}
    </a>
  `,
})
export class WhatsappShareButtonComponent {
  text = input.required<string>();
  phone = input<string>('');
  label = input<string>('');

  href = computed(() => {
    const t = encodeURIComponent(this.text());
    const p = this.phone().replace(/[^\d]/g, '');
    return p
      ? `https://wa.me/${p}?text=${t}`
      : `https://wa.me/?text=${t}`;
  });
}
