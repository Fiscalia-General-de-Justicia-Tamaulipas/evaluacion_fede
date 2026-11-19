import type { PDFFont } from 'pdf-lib';

export type CertificateIssueData = {
  folio: string;
  user_name: string;
  course_name: string;
  issued_at: string;
};

const PAGE_WIDTH = 1024;
const PAGE_HEIGHT = 768;

function centeredTextX(text: string, font: PDFFont, size: number) {
  return Math.max(32, (PAGE_WIDTH - font.widthOfTextAtSize(text, size)) / 2);
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
  const templateResponse = await fetch('/constancia-template.jpg');
  if (!templateResponse.ok) throw new Error('No se pudo cargar la plantilla institucional de la constancia.');

  const [{ PDFDocument, rgb, StandardFonts }, { default: QRCode }] = await Promise.all([
    import('pdf-lib'),
    import('qrcode'),
  ]);
  const institutionalGray = rgb(87 / 255, 87 / 255, 86 / 255);
  const pdf = await PDFDocument.create();
  const template = await pdf.embedJpg(await templateResponse.arrayBuffer());
  const page = pdf.addPage([PAGE_WIDTH, PAGE_HEIGHT]);
  page.drawImage(template, { x: 0, y: 0, width: PAGE_WIDTH, height: PAGE_HEIGHT });

  const nameFont = await pdf.embedFont(StandardFonts.HelveticaBold);
  const detailFont = await pdf.embedFont(StandardFonts.Helvetica);
  let nameSize = 25;
  let nameLines = wrapName(data.user_name, nameFont, nameSize, PAGE_WIDTH - 96);
  while (nameLines.length > 2 && nameSize > 16) {
    nameSize -= 1;
    nameLines = wrapName(data.user_name, nameFont, nameSize, PAGE_WIDTH - 96);
  }
  nameLines.forEach((line, index) => {
    page.drawText(line, {
      x: centeredTextX(line, nameFont, nameSize),
      y: 365 - index * (nameSize + 2),
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
  const qrSize = 60;
  const qrX = 932;
  const qrY = 70;
  page.drawImage(qr, { x: qrX, y: qrY, width: qrSize, height: qrSize });

  const folioSize = 7;
  const folioWidth = detailFont.widthOfTextAtSize(data.folio, folioSize);
  page.drawText(data.folio, {
    x: qrX + (qrSize - folioWidth) / 2,
    y: qrY - 13,
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
