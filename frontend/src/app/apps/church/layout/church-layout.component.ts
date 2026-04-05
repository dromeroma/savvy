import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-church-layout',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './church-layout.component.html',
})
export class ChurchLayoutComponent {}
