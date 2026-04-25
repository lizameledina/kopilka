export function kopecksToRubles(kopecks: number): string {
  const rubles = kopecks / 100;
  return rubles.toLocaleString("ru-RU", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
}

export function rublesToKopecks(rubles: number): number {
  return Math.round(rubles * 100);
}