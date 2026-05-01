const krwFormatter = new Intl.NumberFormat("ko-KR", {
  style: "currency",
  currency: "KRW",
  maximumFractionDigits: 0,
});

const integerFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 0,
});

export function formatKrw(amount: number): string {
  return krwFormatter.format(amount);
}

export function formatPoints(points: number): string {
  return `${integerFormatter.format(points)} P`;
}
