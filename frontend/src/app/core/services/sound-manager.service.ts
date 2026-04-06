import { Injectable } from '@angular/core';

export type SoundType = 'success' | 'error' | 'warning' | 'info' | 'notification' | 'delete';

@Injectable({ providedIn: 'root' })
export class SoundManagerService {
  private ctx: AudioContext | null = null;
  private _enabled = true;
  private _volume = 0.3;
  private readonly COOLDOWN_MS = 80;
  private lastPlayedAt = new Map<SoundType, number>();

  get enabled(): boolean { return this._enabled; }
  set enabled(v: boolean) { this._enabled = v; }
  get volume(): number { return this._volume; }
  set volume(v: number) { this._volume = Math.max(0, Math.min(1, v)); }

  play(type: SoundType): void {
    if (!this._enabled) return;
    const now = performance.now();
    const last = this.lastPlayedAt.get(type) ?? 0;
    if (now - last < this.COOLDOWN_MS) return;
    this.lastPlayedAt.set(type, now);
    this.ensureContext();
    if (!this.ctx) return;
    switch (type) {
      case 'success': this.playSuccess(); break;
      case 'error': this.playError(); break;
      case 'warning': this.playWarning(); break;
      case 'info': this.playInfo(); break;
      case 'notification': this.playNotification(); break;
      case 'delete': this.playDelete(); break;
    }
  }

  private playSuccess(): void { this.tone(880, 0.08, 'sine'); this.tone(1100, 0.08, 'sine', 0.09); }
  private playError(): void { this.tone(330, 0.1, 'square', 0, 0.5); this.tone(260, 0.15, 'square', 0.12, 0.5); }
  private playWarning(): void { this.tone(600, 0.12, 'triangle'); this.tone(450, 0.12, 'triangle', 0.13); }
  private playInfo(): void { this.tone(700, 0.08, 'sine', 0, 0.6); }
  private playNotification(): void { this.tone(830, 0.1, 'sine', 0, 0.7); this.tone(1050, 0.12, 'sine', 0.12, 0.5); }
  private playDelete(): void { this.tone(500, 0.07, 'sine'); this.tone(370, 0.1, 'sine', 0.08); }

  private tone(freq: number, duration: number, waveform: OscillatorType, delay = 0, volScale = 1): void {
    const ctx = this.ctx!;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = waveform;
    osc.frequency.value = freq;
    const effectiveVol = this._volume * volScale;
    const startTime = ctx.currentTime + delay;
    gain.gain.setValueAtTime(effectiveVol, startTime);
    gain.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(startTime);
    osc.stop(startTime + duration + 0.01);
  }

  private ensureContext(): void {
    if (!this.ctx) {
      try { this.ctx = new AudioContext(); } catch { this._enabled = false; return; }
    }
    if (this.ctx.state === 'suspended') { this.ctx.resume(); }
  }
}
