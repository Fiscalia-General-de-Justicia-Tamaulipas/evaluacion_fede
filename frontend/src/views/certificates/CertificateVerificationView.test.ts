import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import CertificateVerificationView from './CertificateVerificationView.vue';

const folio = 'FEDE-2026-6195656D09A246F882365FA5FB62F99D';
const clipboardWrite = vi.fn().mockResolvedValue(undefined);

describe('CertificateVerificationView', () => {
  beforeEach(() => {
    clipboardWrite.mockClear();
    vi.stubGlobal('navigator', { clipboard: { writeText: clipboardWrite } });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      valid: true,
      message: 'La constancia es válida.',
      folio,
      issued_at: '2026-11-19T17:00:00Z',
      user: {
        full_name: 'Jhovan Rodriguez Moreno',
        municipality: 'Victoria',
        sector: 'Fiscalías',
      },
      course: {
        name: 'Delitos Electorales y su investigación en el Sistema Electoral Mexicano',
      },
    }), { status: 200 })));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('presents the verified record and confirms copying its folio', async () => {
    const wrapper = mount(CertificateVerificationView, { props: { folio } });
    await flushPromises();

    expect(wrapper.text()).toContain('Constancia válida');
    expect(wrapper.text()).toContain('Jhovan Rodriguez Moreno');
    expect(wrapper.text()).toContain(folio);

    await wrapper.get('button[aria-label="Copiar folio de constancia"]').trigger('click');
    await flushPromises();

    expect(clipboardWrite).toHaveBeenCalledWith(folio);
    expect(wrapper.text()).toContain('Folio copiado.');
  });
});
