import { Injectable, signal } from '@angular/core';

/**
 * SavvyVoice — dictado por voz usando la Web Speech API del navegador.
 * No requiere backend ni API key: la transcripción ocurre en el dispositivo.
 * Funciona en Chrome/Edge (y la mayoría de navegadores modernos).
 */
@Injectable({ providedIn: 'root' })
export class VoiceService {
  readonly supported = signal(this.detectSupport());
  readonly listening = signal(false);

  private recognition: any = null;

  private detectSupport(): boolean {
    const w = window as any;
    return !!(w.SpeechRecognition || w.webkitSpeechRecognition);
  }

  /**
   * Empieza a escuchar. Llama onResult con el texto (parcial + final).
   * Devuelve una función para detener.
   */
  start(
    onResult: (text: string, isFinal: boolean) => void,
    opts: { lang?: string } = {},
  ): () => void {
    if (!this.supported()) {
      return () => {};
    }
    const w = window as any;
    const Rec = w.SpeechRecognition || w.webkitSpeechRecognition;
    const rec = new Rec();
    this.recognition = rec;
    rec.lang = opts.lang || 'es-CO';
    rec.continuous = false;
    rec.interimResults = true;
    rec.maxAlternatives = 1;

    rec.onresult = (event: any) => {
      let text = '';
      let isFinal = false;
      for (let i = event.resultIndex; i < event.results.length; i++) {
        text += event.results[i][0].transcript;
        if (event.results[i].isFinal) isFinal = true;
      }
      onResult(text, isFinal);
    };
    rec.onstart = () => this.listening.set(true);
    rec.onend = () => this.listening.set(false);
    rec.onerror = () => this.listening.set(false);

    try { rec.start(); } catch { /* already started */ }
    return () => this.stop();
  }

  stop(): void {
    try { this.recognition?.stop(); } catch { /* noop */ }
    this.listening.set(false);
  }
}
