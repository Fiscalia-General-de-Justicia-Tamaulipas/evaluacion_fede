import type { PDFFont } from 'pdf-lib';
import { formatCertificateFolio, formatCertificateName } from '../lib/certificate-format';

export type CertificateIssueData = {
  folio: string;
  user_name: string;
  course_name: string;
  issued_at: string;
};

const LAYOUT_WIDTH = 1024;
const LAYOUT_HEIGHT = 768;
const NAME_BASE_SIZE = 32;
const NAME_CENTER_Y = 350;

function centeredTextX(text: string, font: PDFFont, size: number, pageWidth: number, minMargin: number) {
  return Math.max(minMargin, (pageWidth - font.widthOfTextAtSize(text, size)) / 2);
}

function wrapName(name: string, font: PDFFont, size: number, maxWidth: number) {
  const lines: string[] = [];
  let line = '';
  for (const word of name.trim().split(/\s+/).filter(Boolean)) {
    const candidate = line ? `${line} ${word}` : word;
    if (line && font.widthOfTextAtSize(candidate, size) > maxWidth) {
      lines.push(line);
      line = word;
    } else {
      line = candidate;
    }
  }
  if (line) lines.push(line);
  return lines;
}

export async function generateCourseCertificate(data: CertificateIssueData): Promise<void> {
  const templateResponse = await fetch('/constancia-template.pdf');
  if (!templateResponse.ok) throw new Error('No se pudo cargar la plantilla institucional de la constancia.');

  const [{ PDFDocument, rgb, StandardFonts }, { default: QRCode }] = await Promise.all([
    import('pdf-lib'),
    import('qrcode'),
  ]);
  const institutionalGray = rgb(87 / 255, 87 / 255, 86 / 255);
  const pdf = await PDFDocument.load(await templateResponse.arrayBuffer());
  if (pdf.getPageCount() !== 1) throw new Error('La plantilla institucional debe tener una sola página.');
  const page = pdf.getPages()[0];
  const { width: pageWidth, height: pageHeight } = page.getSize();
  const scaleX = pageWidth / LAYOUT_WIDTH;
  const scaleY = pageHeight / LAYOUT_HEIGHT;

  const nameFont = await pdf.embedFont(StandardFonts.HelveticaBold);
  const detailFont = await pdf.embedFont(StandardFonts.Helvetica);
  let nameSize = NAME_BASE_SIZE * scaleY;
  const displayName = formatCertificateName(data.user_name);
  let nameLines = wrapName(displayName, nameFont, nameSize, pageWidth - 96 * scaleX);
  while (nameLines.length > 2 && nameSize > 16 * scaleY) {
    nameSize -= scaleY;
    nameLines = wrapName(displayName, nameFont, nameSize, pageWidth - 96 * scaleX);
  }
  const nameLineGap = nameSize + 2 * scaleY;
  const firstNameBaseline =
    NAME_CENTER_Y * scaleY + ((nameLines.length - 1) * nameLineGap) / 2;
  nameLines.forEach((line, index) => {
    page.drawText(line, {
      x: centeredTextX(line, nameFont, nameSize, pageWidth, 32 * scaleX),
      y: firstNameBaseline - index * nameLineGap,
      size: nameSize,
      font: nameFont,
      color: institutionalGray,
    });
  });

  const qrUrl = `${window.location.origin}/verificar/${encodeURIComponent(data.folio)}`;
  const qrDataUrl = await QRCode.toDataURL(qrUrl, {
    errorCorrectionLevel: 'M',
    margin: 1,
    width: 256,
    color: { dark: '#575756', light: '#FFFFFF' },
  });
  const qr = await pdf.embedPng(qrDataUrl);
  const qrSize = 60 * scaleY;
  const qrX = 932 * scaleX;
  const qrY = 70 * scaleY;
  page.drawImage(qr, { x: qrX, y: qrY, width: qrSize, height: qrSize });

  const displayFolio = formatCertificateFolio(data.folio);
  const folioSize = 7 * scaleY;
  const folioWidth = detailFont.widthOfTextAtSize(displayFolio, folioSize);
  page.drawText(displayFolio, {
    x: qrX + (qrSize - folioWidth) / 2,
    y: qrY - 13 * scaleY,
    size: folioSize,
    font: detailFont,
    color: institutionalGray,
  });

  const bytes = await pdf.save();
  const url = URL.createObjectURL(new Blob([bytes], { type: 'application/pdf' }));
  const download = document.createElement('a');
  download.href = url;
  download.download = `constancia-${data.folio}.pdf`;
  document.body.appendChild(download);
  download.click();
  download.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
