import { Component, Input, Output, EventEmitter, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-modal',
  imports: [CommonModule],
  templateUrl: './modal.component.html',
})
export class ModalComponent {
  @Input() isOpen = false;
  @Output() close = new EventEmitter<void>();
  @Input() className = '';
  @Input() showCloseButton = true;
  @Input() isFullscreen = false;

  ngOnChanges() {
    document.body.style.overflow = this.isOpen ? 'hidden' : 'unset';
  }

  ngOnDestroy() {
    document.body.style.overflow = 'unset';
  }

  onBackdropClick(event: MouseEvent) {
    if (!this.isFullscreen) this.close.emit();
  }

  onContentClick(event: MouseEvent) {
    event.stopPropagation();
  }

  @HostListener('document:keydown.escape')
  onEscape() {
    if (this.isOpen) this.close.emit();
  }
}
