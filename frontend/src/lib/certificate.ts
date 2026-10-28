export type CertificateDraftData = {
  moduleId: number;
  moduleName: string;
  participantName: string;
  score: number;
  issuedAt: string | Date;
};

export function openCertificateWindow(): Window | null {
  return window.open('', '_blank', 'width=1000,height=760');
}

function escapeHtml(value: unknown): string {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[character]!);
}

export function renderCertificateDraft(target: Window, data: CertificateDraftData) {
  const issueDate = new Date(data.issuedAt);
  const formattedDate = Number.isNaN(issueDate.getTime())
    ? 'Fecha pendiente de confirmar'
    : issueDate.toLocaleDateString('es-MX', { year: 'numeric', month: 'long', day: 'numeric' });

  target.document.write(`<!doctype html>
  <html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Borrador de constancia · Módulo ${escapeHtml(data.moduleId)}</title>
  <style>
    @page{size:landscape;margin:12mm}*{box-sizing:border-box}body{margin:0;background:#f0f0ef;color:#202020;font:16px/1.5 Arial,Helvetica,sans-serif}
    .sheet{width:100%;min-height:180mm;margin:0 auto;padding:18mm 22mm;position:relative;display:grid;place-items:center;overflow:hidden;background:#fff;border:2px solid #575756}
    .logos{position:absolute;inset:9mm 12mm auto;display:flex;justify-content:space-between;align-items:center}.logos img{width:min(25vw,185px);height:48px;object-fit:contain}
    .content{position:relative;z-index:1;width:100%;max-width:850px;text-align:center}.institution{margin:0;color:#575756;font-size:11px;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
    h1{margin:8px 0 20px;font:700 34px/1.15 Georgia,'Times New Roman',serif;letter-spacing:.02em}h2{margin:7px 0 14px;font:700 29px/1.2 Georgia,'Times New Roman',serif}
    .module{max-width:740px;margin:12px auto;font-size:19px}.score{margin:12px 0 3px;font-weight:700}.date{margin:0;color:#575756;font-size:14px}
    .signature{width:260px;margin:22px auto 0;padding-top:8px;border-top:1px solid #777;font-size:11px}.folio{margin:7px 0 0;font-size:11px;color:#575756}
    .draft{position:absolute;inset:0;display:grid;place-items:center;pointer-events:none;color:rgba(150,36,36,.13);font-size:clamp(56px,10vw,100px);font-weight:900;letter-spacing:.16em;transform:rotate(-24deg)}
    .notice{position:absolute;right:12mm;bottom:6mm;left:12mm;margin:0;text-align:center;color:#575756;font-size:9px;font-weight:700;letter-spacing:.13em;text-transform:uppercase}
    @media(max-width:650px){.sheet{min-height:100vh;padding:120px 22px 70px}h1{font-size:27px}h2{font-size:23px}.logos{inset:18px 20px auto}.logos img{width:30vw;height:40px}.draft{font-size:44px}}
    @media print{body{background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}.sheet{min-height:180mm}}
  </style></head><body><main class="sheet">
    <div class="logos"><img src="/logo_fgjtam.png" alt="Fiscalía General de Justicia de Tamaulipas"><img src="/logo_fede.png" alt="Fiscalía Especializada en Delitos Electorales"></div>
    <div class="draft">BORRADOR</div>
    <section class="content"><p class="institution">Fiscalía General de Justicia del Estado de Tamaulipas</p><h1>Constancia de acreditación</h1>
      <p>Se hace constar que</p><h2>${escapeHtml(data.participantName || 'Nombre del participante')}</h2>
      <p class="module">acreditó el <strong>Módulo ${escapeHtml(data.moduleId)}: ${escapeHtml(data.moduleName)}</strong></p>
      <p class="score">Calificación: ${escapeHtml(data.score)}/100</p><p class="date">Fecha de expedición: ${escapeHtml(formattedDate)}</p>
      <p class="signature">[NOMBRE Y CARGO DE AUTORIDAD FACULTADA]</p><p class="folio">Folio institucional: [PENDIENTE DE ASIGNAR]</p>
    </section><p class="notice">Documento de trabajo · borrador pendiente de validación institucional</p>
  </main><script>window.addEventListener('load',()=>window.print())<\/script></body></html>`);
  target.document.close();
}
