import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-hr-layout',
  imports: [RouterOutlet],
  template: `<router-outlet />`,
})
export class HrLayoutComponent {}
