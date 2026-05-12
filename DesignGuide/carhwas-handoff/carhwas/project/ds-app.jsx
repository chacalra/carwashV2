// ds-app.jsx — assembles the design canvas with sections + artboards.

const App = () => {
  // Standard artboard sizes
  const W_FULL = 1280;   // desktop screen
  const H_FULL = 820;
  const W_DOC = 720;     // narrow ref doc (palette, type, tokens)
  const H_DOC = 820;
  const W_WIDE = 1280;   // components canvas
  const H_COMP = 1280;

  return (
    <DesignCanvas>
      {/* Intro */}
      <DCSection
        id="intro"
        title="Mukusoft · Design System"
        subtitle="Dashboard financiero para Car Wash · Stripe/Vercel-style · Geist + Geist Mono · Light + Dark"
      >
        <DCArtboard id="intro-card" label="Brief" width={720} height={420}>
          <Themed theme="light" style={{ padding: 40, display: 'flex', flexDirection: 'column' }}>
            <Logo size={26} />
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: 28 }}>
              Cómo leer este sistema
            </div>
            <div style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.025em', lineHeight: 1.35, marginTop: 8, color: 'var(--text-primary)' }}>
              Cards planas con borde 1px, vidrio sólo en overlays.
              Tipografía protagonista, números siempre tabulares.
              Acento azul eléctrico únicamente para acción y totales.
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24, marginTop: 32 }}>
              {[
                ['Mood',     'Stripe / Vercel'],
                ['Densidad', 'Cómoda · base 14'],
                ['Acento',   '#3B82F6 · azul eléctrico'],
                ['Type',     'Geist · Geist Mono'],
                ['Spacing',  '4 · 8 · 12 · 16 · 24'],
                ['Stack',    'Flet + MD3 compat.'],
              ].map(([k, v]) => (
                <div key={k}>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>{k}</div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginTop: 4 }}>{v}</div>
                </div>
              ))}
            </div>
          </Themed>
        </DCArtboard>
      </DCSection>

      {/* Foundations */}
      <DCSection
        id="foundations"
        title="01 · Foundations"
        subtitle="Color, tipografía y tokens"
      >
        <DCArtboard id="palette-light" label="Paleta · Light" width={W_DOC} height={H_DOC}>
          <ColorPalette theme="light" />
        </DCArtboard>
        <DCArtboard id="palette-dark" label="Paleta · Dark" width={W_DOC} height={H_DOC}>
          <ColorPalette theme="dark" />
        </DCArtboard>
        <DCArtboard id="type" label="Tipografía" width={900} height={H_DOC}>
          <Typography theme="light" />
        </DCArtboard>
        <DCArtboard id="tokens" label="Spacing · Radii · Shadow" width={W_DOC} height={H_DOC}>
          <Tokens theme="light" />
        </DCArtboard>
      </DCSection>

      {/* Components */}
      <DCSection
        id="components"
        title="02 · Components"
        subtitle="Kit aplicable a Flet · MD3"
      >
        <DCArtboard id="components-light" label="Components · Light" width={W_WIDE} height={H_COMP}>
          <Components theme="light" />
        </DCArtboard>
        <DCArtboard id="components-dark" label="Components · Dark" width={W_WIDE} height={H_COMP}>
          <Components theme="dark" />
        </DCArtboard>
      </DCSection>

      {/* Dashboard */}
      <DCSection
        id="dashboard"
        title="03 · Dashboard"
        subtitle="KPIs · cashflow · movimientos del día"
      >
        <DCArtboard id="dash-light" label="Dashboard · Light" width={W_FULL} height={H_FULL}>
          <Dashboard theme="light" />
        </DCArtboard>
        <DCArtboard id="dash-dark" label="Dashboard · Dark" width={W_FULL} height={H_FULL}>
          <Dashboard theme="dark" />
        </DCArtboard>
      </DCSection>

      {/* Caja diaria */}
      <DCSection
        id="caja"
        title="04 · Caja diaria"
        subtitle="Apertura · arqueo de billetes · cierre"
      >
        <DCArtboard id="caja-light" label="Caja diaria · Light" width={W_FULL} height={H_FULL}>
          <CajaDiaria theme="light" />
        </DCArtboard>
        <DCArtboard id="caja-dark" label="Caja diaria · Dark" width={W_FULL} height={H_FULL}>
          <CajaDiaria theme="dark" />
        </DCArtboard>
      </DCSection>

      {/* Ingreso */}
      <DCSection
        id="ingreso"
        title="05 · Registrar ingreso"
        subtitle="Selector de servicio · cliente · cobro"
      >
        <DCArtboard id="ingreso-light" label="Nuevo ingreso · Light" width={W_FULL} height={H_FULL}>
          <NuevoIngreso theme="light" />
        </DCArtboard>
        <DCArtboard id="ingreso-dark" label="Nuevo ingreso · Dark" width={W_FULL} height={H_FULL}>
          <NuevoIngreso theme="dark" />
        </DCArtboard>
      </DCSection>

      {/* Egreso */}
      <DCSection
        id="egreso"
        title="06 · Registrar egreso"
        subtitle="Categoría · proveedor · comprobante"
      >
        <DCArtboard id="egreso-light" label="Nuevo egreso · Light" width={W_FULL} height={H_FULL}>
          <NuevoEgreso theme="light" />
        </DCArtboard>
        <DCArtboard id="egreso-dark" label="Nuevo egreso · Dark" width={W_FULL} height={H_FULL}>
          <NuevoEgreso theme="dark" />
        </DCArtboard>
      </DCSection>

      {/* Movimientos */}
      <DCSection
        id="movimientos"
        title="07 · Movimientos"
        subtitle="Tabla con filtros · resumen · paginación"
      >
        <DCArtboard id="mov-light" label="Movimientos · Light" width={W_FULL} height={H_FULL}>
          <Movimientos theme="light" />
        </DCArtboard>
        <DCArtboard id="mov-dark" label="Movimientos · Dark" width={W_FULL} height={H_FULL}>
          <Movimientos theme="dark" />
        </DCArtboard>
      </DCSection>

      {/* Reportes */}
      <DCSection
        id="reportes"
        title="08 · Reportes"
        subtitle="Tendencias · top servicios · comparativos"
      >
        <DCArtboard id="rep-light" label="Reportes · Light" width={W_FULL} height={H_FULL}>
          <Reportes theme="light" />
        </DCArtboard>
        <DCArtboard id="rep-dark" label="Reportes · Dark" width={W_FULL} height={H_FULL}>
          <Reportes theme="dark" />
        </DCArtboard>
      </DCSection>

      {/* Patterns */}
      <DCSection
        id="patterns"
        title="09 · Patterns"
        subtitle="Estados vacíos · errores · feedback · modales con vidrio"
      >
        <DCArtboard id="empty-light" label="Patterns · Light" width={1080} height={780}>
          <EmptyStates theme="light" />
        </DCArtboard>
        <DCArtboard id="empty-dark" label="Patterns · Dark" width={1080} height={780}>
          <EmptyStates theme="dark" />
        </DCArtboard>
      </DCSection>

      {/* Responsive */}
      <DCSection
        id="responsive"
        title="10 · Responsive · Mobile + Tablet"
        subtitle="Registrar ingreso optimizado para móvil web · breakpoints + ResponsiveRow"
      >
        <DCArtboard id="responsive-docs" label="Sistema responsive" width={1080} height={1480}>
          <ResponsiveDocs />
        </DCArtboard>
        <DCArtboard id="ingreso-mobile" label="Ingreso · iPhone 14" width={460} height={880}>
          <PhoneFrame><MobileIngreso /></PhoneFrame>
        </DCArtboard>
        <DCArtboard id="ingreso-tablet" label="Ingreso · Tablet vertical" width={880} height={1180}>
          <TabletFrame><TabletIngreso /></TabletFrame>
        </DCArtboard>
      </DCSection>

      {/* Flet mapping */}
      <DCSection
        id="flet"
        title="11 · Flet · MD3 mapping"
        subtitle="Cómo se traduce este sistema a controles reales"
      >
        <DCArtboard id="flet-map" label="Flet mapping" width={900} height={680}>
          <Themed theme="light" style={{ padding: 32, overflowY: 'auto' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Stack guidance</div>
            <div style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.025em', marginTop: 4 }}>Tokens → Flet · Material Design 3</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8, marginBottom: 24, maxWidth: 580, lineHeight: 1.55 }}>
              Tokens DS expresados como <span className="mono" style={{ background: 'var(--bg-sunken)', padding: '1px 6px', borderRadius: 4 }}>ft.colors</span> y propiedades. Mantené esta tabla como la única fuente de verdad.
            </div>

            {[
              ['Surface · bg.app',     'page.bgcolor',                          '#FAFAF9 / #0A0A0A'],
              ['Surface · bg.surface', 'ft.Container(bgcolor=…) · ft.Card',     '#FFFFFF / #141414'],
              ['Border default',       'border=ft.border.all(1, …)',            '#E4E4E0 / #262626'],
              ['Accent',               'ft.colors.PRIMARY override',            '#3B82F6 (ambos)'],
              ['Pos / Neg',            'colors custom · success / error',       '#059669 #DC2626 / #10B981 #EF4444'],
              ['Radius · md',          'border_radius=8',                       'botones, inputs'],
              ['Radius · lg',          'border_radius=12',                      'cards'],
              ['Shadow · xs',          'shadow=ft.BoxShadow(blur=2, …)',        'cards en reposo'],
              ['Type · UI',            'ft.TextStyle(font_family="Geist")',     'preload con google fonts'],
              ['Type · Num',           'ft.TextStyle(font_family="Geist Mono")', 'siempre montos / horarios'],
              ['Button · primary',     'ft.FilledButton(style=…)',              'altura 36 · radius 8'],
              ['Button · secondary',   'ft.OutlinedButton(style=…)',            'borde 1 · sin sombra'],
              ['Button · ghost',       'ft.TextButton(style=…)',                'sólo color secondary'],
              ['Input',                'ft.TextField(border_radius=8, dense=True)', 'altura 38 · borde focus accent'],
              ['Table',                'ft.DataTable o ft.Column de filas',     'header en bg.sunken · CAPS 11px'],
              ['Modal · glass',        'ft.AlertDialog + Container con bgcolor rgba + blur', 'único uso de glassmorphism'],
              ['Sidebar',              'ft.NavigationRail extendido (custom)',  'logo arriba · item activo con bg.sunken + barra accent'],
              ['Iconos',               'ft.icons material-symbols-outlined',    'stroke 1.5 · 18-20px'],
            ].map(([token, flet, val]) => (
              <div key={token} style={{
                display: 'grid',
                gridTemplateColumns: '180px 1fr 200px',
                gap: 16,
                padding: '12px 0',
                borderBottom: '1px solid var(--border-subtle)',
                alignItems: 'baseline',
                fontSize: 13,
              }}>
                <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{token}</span>
                <span className="mono" style={{ fontSize: 12, color: 'var(--accent)' }}>{flet}</span>
                <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{val}</span>
              </div>
            ))}
          </Themed>
        </DCArtboard>
      </DCSection>
    </DesignCanvas>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
