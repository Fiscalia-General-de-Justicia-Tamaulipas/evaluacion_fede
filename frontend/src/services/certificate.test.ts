// @vitest-environment node
import { readFileSync } from 'node:fs';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PDFDict, PDFDocument, PDFName, PDFPage } from 'pdf-lib';
import { generateCourseCertificate } from './certificate';

const templateBytes = readFileSync(new URL('../../public/constancia-template.pdf', import.meta.url));
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

  it('preserves the PDF template while adding the name, QR and unlabeled folio without a printed date', async () => {
    const textDraws = vi.spyOn(PDFPage.prototype, 'drawText');
    const imageDraws = vi.spyOn(PDFPage.prototype, 'drawImage');
    await generateCourseCertificate({
      folio: 'FEDE-2026-0123456789ABCDEF',
      user_name: 'Ada López Pérez',
      course_name: 'Delitos Electorales y su investigación en el Sistema Electoral Mexicano',
      issued_at: '2026-11-19T17:00:00Z',
    });

    expect(fetch).toHaveBeenCalledWith('/constancia-template.pdf');
    expect(anchor.download).toBe('constancia-FEDE-2026-0123456789ABCDEF.pdf');
    expect(anchor.href).toBe('blob:constancia');
    expect(anchor.click).toHaveBeenCalledOnce();
    expect(anchor.remove).toHaveBeenCalledOnce();
    expect(generatedBlob).not.toBeNull();

    const pdf = await PDFDocument.load(new Uint8Array(await generatedBlob!.arrayBuffer()));
    expect(pdf.getPageCount()).toBe(1);
    expect(pdf.getPages()[0].getSize()).toEqual({ width: 792, height: 612 });
    const xObjects = pdf.getPages()[0].node.Resources().lookup(PDFName.of('XObject'), PDFDict);
    expect(xObjects.keys()).toHaveLength(6);
    expect(textDraws.mock.calls.map(([text]) => text)).toEqual([
      'Ada López Pérez',
      'FEDE-2026-0123456789ABCDEF',
    ]);
    const [nameText, nameOptions] = textDraws.mock.calls[0];
    expect(nameOptions.size).toBeCloseTo(32 * (612 / 768));
    expect(nameOptions.y).toBeCloseTo(350 * (612 / 768));
    if (!nameOptions.font || nameOptions.x === undefined || nameOptions.size === undefined) {
      throw new Error('The rendered name must include its font, position, and size.');
    }
    const nameWidth = nameOptions.font.widthOfTextAtSize(nameText, nameOptions.size);
    expect(nameOptions.x + nameWidth / 2).toBeCloseTo(792 / 2);
    expect(textDraws.mock.calls[1][1].y).toBeCloseTo(57 * (612 / 768));
    expect(textDraws.mock.calls[1][1].size).toBeCloseTo(7 * (612 / 768));
    expect(imageDraws).toHaveBeenCalledOnce();
    expect(imageDraws.mock.calls[0][1].x).toBeCloseTo(932 * (792 / 1024));
    expect(imageDraws.mock.calls[0][1].y).toBeCloseTo(70 * (612 / 768));
    expect(imageDraws.mock.calls[0][1].width).toBeCloseTo(60 * (612 / 768));
    expect(imageDraws.mock.calls[0][1].height).toBeCloseTo(60 * (612 / 768));
  });
});
