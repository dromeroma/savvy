import { Component, inject, signal, OnInit, afterNextRender, ElementRef, viewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import * as d3 from 'd3';

interface GenogramNode {
  id: string;
  person_id: string;
  first_name: string;
  last_name: string;
  gender: string | null;
  date_of_birth: string | null;
  is_deceased: boolean;
  role: string;
  generation: number;
  annotations: any[];
  x?: number;
  y?: number;
}

interface GenogramEdge {
  source_person_id: string;
  target_person_id: string;
  relationship_type: string;
  status: string;
}

const NODE_SIZE = 50;
const H_SPACING = 120;
const V_SPACING = 140;
const COUPLE_GAP = 80;

@Component({
  selector: 'app-genogram',
  imports: [CommonModule, RouterLink],
  template: `
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">
            Genograma: {{ familyName() }}
          </h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Diagrama familiar clínico</p>
        </div>
        <a [routerLink]="['/family', unitId]"
          class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">
          Volver al detalle
        </a>
      </div>

      <!-- Legend -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 mb-4">
        <div class="flex flex-wrap gap-4 text-xs text-gray-600 dark:text-gray-400">
          <div class="flex items-center gap-1.5">
            <div class="w-4 h-4 border-2 border-blue-500 bg-blue-50 dark:bg-blue-900/20"></div>
            <span>Hombre</span>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-4 h-4 rounded-full border-2 border-pink-500 bg-pink-50 dark:bg-pink-900/20"></div>
            <span>Mujer</span>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-4 h-4 border-2 border-gray-400 bg-gray-200 dark:bg-gray-600 relative">
              <div class="absolute inset-0 flex items-center justify-center text-[8px] font-bold text-gray-600 dark:text-gray-300">✕</div>
            </div>
            <span>Fallecido</span>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-6 h-0 border-t-2 border-gray-800 dark:border-gray-300"></div>
            <span>Matrimonio</span>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-6 h-0 border-t-2 border-dashed border-gray-400"></div>
            <span>Separación/Divorcio</span>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-3 h-3 rounded-full bg-red-500"></div>
            <span>Anotación severa</span>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span>Anotación moderada</span>
          </div>
        </div>
      </div>

      <!-- Genogram Canvas -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div #genogramContainer class="w-full overflow-auto custom-scrollbar" style="min-height: 500px;">
          <svg #genogramSvg></svg>
        </div>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      }
    </div>
  `,
})
export class GenogramComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);

  svgRef = viewChild<ElementRef<SVGSVGElement>>('genogramSvg');
  containerRef = viewChild<ElementRef<HTMLDivElement>>('genogramContainer');

  unitId = '';
  familyName = signal('');
  loading = signal(true);

  private nodes: GenogramNode[] = [];
  private edges: GenogramEdge[] = [];
  private isDarkMode = false;

  constructor() {
    afterNextRender(() => {
      this.isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
      this.loadGenogram();
    });
  }

  ngOnInit(): void {
    this.unitId = this.route.snapshot.paramMap.get('id') || '';
  }

  private loadGenogram(): void {
    this.loading.set(true);
    this.api.get<any>(`/family/units/${this.unitId}/genogram`).subscribe({
      next: (data) => {
        this.familyName.set(data.family_unit.name);
        this.nodes = data.nodes;
        this.edges = data.edges;
        this.loading.set(false);
        this.renderGenogram();
      },
      error: () => this.loading.set(false),
    });
  }

  private renderGenogram(): void {
    const svgEl = this.svgRef()?.nativeElement;
    if (!svgEl || this.nodes.length === 0) return;

    // Layout: group by generation
    const generations = new Map<number, GenogramNode[]>();
    for (const node of this.nodes) {
      const gen = node.generation;
      if (!generations.has(gen)) generations.set(gen, []);
      generations.get(gen)!.push(node);
    }

    const sortedGens = [...generations.keys()].sort((a, b) => a - b);
    const padding = 60;

    // Position nodes
    let maxWidth = 0;
    for (const gen of sortedGens) {
      const genNodes = generations.get(gen)!;
      const genIndex = sortedGens.indexOf(gen);
      const y = padding + genIndex * V_SPACING;
      const totalWidth = genNodes.length * H_SPACING;
      const startX = padding;

      for (let i = 0; i < genNodes.length; i++) {
        genNodes[i].x = startX + i * H_SPACING + H_SPACING / 2;
        genNodes[i].y = y;
      }
      maxWidth = Math.max(maxWidth, startX + totalWidth + padding);
    }

    const totalHeight = padding + sortedGens.length * V_SPACING + padding;
    const svgWidth = Math.max(maxWidth + padding, 600);

    const dark = this.isDarkMode;
    const textColor = dark ? '#e5e7eb' : '#1f2937';
    const lineColor = dark ? '#9ca3af' : '#374151';
    const bgMale = dark ? 'rgba(59,130,246,0.15)' : '#eff6ff';
    const bgFemale = dark ? 'rgba(236,72,153,0.15)' : '#fdf2f8';
    const borderMale = '#3b82f6';
    const borderFemale = '#ec4899';

    // Clear and setup SVG
    d3.select(svgEl).selectAll('*').remove();
    const svg = d3.select(svgEl)
      .attr('width', svgWidth)
      .attr('height', totalHeight);

    // Draw edges
    const edgesGroup = svg.append('g').attr('class', 'edges');
    const nodeMap = new Map(this.nodes.map(n => [n.person_id, n]));

    for (const edge of this.edges) {
      const source = nodeMap.get(edge.source_person_id);
      const target = nodeMap.get(edge.target_person_id);
      if (!source?.x || !target?.x || !source?.y || !target?.y) continue;

      const isCouple = ['married', 'divorced', 'separated', 'engaged', 'cohabiting', 'widowed'].includes(edge.relationship_type);
      const isDissolved = ['divorced', 'separated'].includes(edge.relationship_type);

      if (isCouple) {
        // Horizontal line between couple
        edgesGroup.append('line')
          .attr('x1', source.x).attr('y1', source.y)
          .attr('x2', target.x).attr('y2', target.y)
          .attr('stroke', lineColor)
          .attr('stroke-width', isDissolved ? 1.5 : 2.5)
          .attr('stroke-dasharray', isDissolved ? '6,4' : 'none');

        if (isDissolved) {
          const midX = (source.x + target.x) / 2;
          const midY = (source.y + target.y) / 2;
          edgesGroup.append('line')
            .attr('x1', midX - 6).attr('y1', midY - 8)
            .attr('x2', midX + 6).attr('y2', midY + 8)
            .attr('stroke', '#ef4444').attr('stroke-width', 2);
        }
      } else {
        // Parent-child: vertical connector
        const midY = (source.y + target.y) / 2;
        const path = `M ${source.x} ${source.y + NODE_SIZE / 2} V ${midY} H ${target.x} V ${target.y - NODE_SIZE / 2}`;
        edgesGroup.append('path')
          .attr('d', path)
          .attr('fill', 'none')
          .attr('stroke', lineColor)
          .attr('stroke-width', 1.5);
      }
    }

    // Draw nodes
    const nodesGroup = svg.append('g').attr('class', 'nodes');

    for (const node of this.nodes) {
      if (!node.x || !node.y) continue;

      const g = nodesGroup.append('g')
        .attr('transform', `translate(${node.x}, ${node.y})`);

      const isMale = node.gender === 'male';
      const isFemale = node.gender === 'female';
      const halfSize = NODE_SIZE / 2;

      // Shape: square for male, circle for female, diamond for unknown
      if (isMale) {
        g.append('rect')
          .attr('x', -halfSize).attr('y', -halfSize)
          .attr('width', NODE_SIZE).attr('height', NODE_SIZE)
          .attr('rx', 4)
          .attr('fill', bgMale)
          .attr('stroke', borderMale)
          .attr('stroke-width', 2.5);
      } else if (isFemale) {
        g.append('circle')
          .attr('r', halfSize)
          .attr('fill', bgFemale)
          .attr('stroke', borderFemale)
          .attr('stroke-width', 2.5);
      } else {
        // Diamond for unknown gender
        g.append('polygon')
          .attr('points', `0,${-halfSize} ${halfSize},0 0,${halfSize} ${-halfSize},0`)
          .attr('fill', dark ? 'rgba(156,163,175,0.15)' : '#f3f4f6')
          .attr('stroke', '#6b7280')
          .attr('stroke-width', 2.5);
      }

      // Deceased X
      if (node.is_deceased) {
        g.append('line')
          .attr('x1', -halfSize + 6).attr('y1', -halfSize + 6)
          .attr('x2', halfSize - 6).attr('y2', halfSize - 6)
          .attr('stroke', '#ef4444').attr('stroke-width', 2.5);
        g.append('line')
          .attr('x1', halfSize - 6).attr('y1', -halfSize + 6)
          .attr('x2', -halfSize + 6).attr('y2', halfSize - 6)
          .attr('stroke', '#ef4444').attr('stroke-width', 2.5);
      }

      // Annotation markers (dots)
      if (node.annotations && node.annotations.length > 0) {
        const hasSevere = node.annotations.some((a: any) => a.severity === 'severe');
        const dotColor = hasSevere ? '#ef4444' : '#f59e0b';
        g.append('circle')
          .attr('cx', halfSize - 2).attr('cy', -halfSize + 2)
          .attr('r', 5)
          .attr('fill', dotColor);
      }

      // Name label
      g.append('text')
        .attr('y', halfSize + 16)
        .attr('text-anchor', 'middle')
        .attr('font-size', '11px')
        .attr('font-weight', '600')
        .attr('fill', textColor)
        .text(node.first_name);

      g.append('text')
        .attr('y', halfSize + 28)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('fill', dark ? '#9ca3af' : '#6b7280')
        .text(node.last_name);

      // Role label
      g.append('text')
        .attr('y', halfSize + 40)
        .attr('text-anchor', 'middle')
        .attr('font-size', '9px')
        .attr('fill', dark ? '#6b7280' : '#9ca3af')
        .text(this.roleLabel(node.role));
    }
  }

  private roleLabel(r: string): string {
    return {
      head: 'Cabeza', spouse: 'Cónyuge', child: 'Hijo/a',
      grandchild: 'Nieto/a', grandparent: 'Abuelo/a',
      uncle_aunt: 'Tío/a', cousin: 'Primo/a', member: '',
    }[r] || '';
  }
}
