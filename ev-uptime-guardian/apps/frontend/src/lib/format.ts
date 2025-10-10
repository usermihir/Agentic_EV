import type { ColorBand } from './types';

export function fmtMin(n: number): string {
  return `${Math.round(n)} min`;
}

export function badgeClass(band: ColorBand): string {
  switch (band) {
    case 'green':
      return 'text-green-600';
    case 'amber':
      return 'text-amber-600';
    case 'red':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
}