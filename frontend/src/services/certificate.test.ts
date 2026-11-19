// @vitest-environment node
import { readFileSync } from 'node:fs';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PDFDict, PDFDocument, PDFName, PDFPage } from 'pdf-lib';
import { generateCourseCertificate } from './certificate';

const templateBytes = readFileSync(new URL('../../public/constancia-template.jpg', import.meta.url));
const anchor = { href: '', download: '', click: vi.fn(), remove: vi.fn() };
let generatedBlob: Blob | null = null;

describe('generateCourseCertificate', () => {
  beforeEach(() => {
    generatedBlob = null;
    anchor.href = '';
    anchor.download = '';
    anchor.click.mockClear();
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(templateBytes)));
    vi.stubGlobal('window', {
      location: { origin: 'https://fede.example' },
      setTimeout: vi.fn(),
    });
    vi.stubGlobal('document', {
      createElement: vi.fn(() => anchor),
      body: { appendChild: vi.fn() },
    });
    vi.spyOn(URL, 'createObjectURL').mockImplementation(blob => {
      generatedBlob = blob;
      return 'blob:constancia';
    });
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('creates a single-page PDF with template, QR and an unlabeled folio below it, without a printed date', async () => {
    const textDraws = vi.spyOn(PDFPage.prototype, 'drawText');
    const imageDraws = vi.spyOn(PDFPage.prototype, 'drawImage');
    await generateCourseCertificate({
      folio: 'FEDE-2026-0123456789ABCDEF',
      user_name: 'Ada López Pérez',
      course_name: 'Delitos Electorales y su investigación en el Sistema Electoral Mexicano',
      issued_at: '2026-11-19T17:00:00Z',
    });

    expect(fetch).toHaveBeenCalledWith('/constancia-template.jpg');
    expect(anchor.download).toBe('constancia-FEDE-2026-0123456789ABCDEF.pdf');
    expect(anchor.href).toBe('blob:constancia');
    expect(anchor.click).toHaveBeenCalledOnce();
    expect(anchor.remove).toHaveBeenCalledOnce();
    expect(generatedBlob).not.toBeNull();

    const pdf = await PDFDocument.load(new Uint8Array(await generatedBlob!.arrayBuffer()));
    expect(pdf.getPageCount()).toBe(1);
    const xObjects = pdf.getPages()[0].node.Resources().lookup(PDFName.of('XObject'), PDFDict);
    expect(xObjects.keys()).toHaveLength(2);
    expect(textDraws.mock.calls.map(([text]) => text)).toEqual([
      'Ada López Pérez',
      'FEDE-2026-0123456789ABCDEF',
    ]);
    expect(textDraws.mock.calls[1][1]).toMatchObject({ y: 57, size: 7 });
    expect(imageDraws.mock.calls[1][1]).toMatchObject({ x: 932, y: 70, width: 60, height: 60 });
  });
});
