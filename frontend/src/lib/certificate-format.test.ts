import { describe, expect, it } from 'vitest';
import { formatCertificateFolio, formatCertificateName } from './certificate-format';

describe('certificate display formatting', () => {
  it('removes only the FEDE year prefix from displayed folios', () => {
    expect(formatCertificateFolio('FEDE-2026-0123456789ABCDEFFEDCBA9876543210'))
      .toBe('0123456789ABCDEFFEDCBA9876543210');
    expect(formatCertificateFolio('OTRO-2026-FOLIO')).toBe('OTRO-2026-FOLIO');
  });

  it('uppercases names with Spanish accents', () => {
    expect(formatCertificateName('Jhovan Rodríguez Moreno'))
      .toBe('JHOVAN RODRÍGUEZ MORENO');
  });
});
