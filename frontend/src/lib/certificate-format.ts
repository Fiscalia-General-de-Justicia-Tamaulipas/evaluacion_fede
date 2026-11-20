export function formatCertificateFolio(folio: string): string {
  return folio.replace(/^FEDE-\d{4}-/, '');
}

export function formatCertificateName(name: string): string {
  return name.toLocaleUpperCase('es-MX');
}
