// ds-foundations.jsx — Color palette, type scale, spacing, radii, shadows, depth.
// All visuals derive from CSS vars so they stay in sync with theme switches.

const Swatch = ({ varName, label, hex }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px',
                background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--r-md)' }}>
    <div style={{
      width: 32, height: 32, borderRadius: 8,
      background: `var(${varName})`,
      boxShadow: 'inset 0 0 0 1px rgba(0,0,0,0.06)',
      flex: '0 0 auto',
    }} />
    <div style={{ minWidth: 0, flex: 1 }}>
      <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>{label}</div>
      <div className="mono" style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 1 }}>{hex}</div>
    </div>
  </div>
);

// Colors split by semantic role; not the raw palette but tokenized so the
// values visible here are exactly what the dev would reference in code.
const COLOR_GROUPS = {
  light: {
    Surface: [
      ['--bg-app', 'bg.app', '#FAFAF9'],
      ['--bg-surface', 'bg.surface', '#FFFFFF'],
      ['--bg-sunken', 'bg.sunken', '#F4F4F2'],
    ],
    Text: [
      ['--text-primary', 'text.primary', '#0A0A0A'],
      ['--text-secondary', 'text.secondary', '#525252'],
      ['--text-tertiary', 'text.tertiary', '#737373'],
      ['--text-disabled', 'text.disabled', '#A3A3A3'],
    ],
    Borders: [
      ['--border-subtle', 'border.subtle', '#EDEDEA'],
      ['--border-default', 'border.default', '#E4E4E0'],
      ['--border-strong', 'border.strong', '#D4D4D0'],
    ],
    Accent: [
      ['--accent', 'accent', '#3B82F6'],
      ['--accent-hover', 'accent.hover', '#2563EB'],
      ['--accent-soft', 'accent.soft', '#EFF6FF'],
    ],
    'Estado financiero': [
      ['--pos', 'pos · ingreso', '#059669'],
      ['--pos-soft', 'pos.soft', '#ECFDF5'],
      ['--neg', 'neg · egreso', '#DC2626'],
      ['--neg-soft', 'neg.soft', '#FEF2F2'],
      ['--warn', 'warn', '#D97706'],
      ['--warn-soft', 'warn.soft', '#FFFBEB'],
    ],
  },
  dark: {
    Surface: [
      ['--bg-app', 'bg.app', '#0A0A0A'],
      ['--bg-surface', 'bg.surface', '#141414'],
      ['--bg-sunken', 'bg.sunken', '#0F0F0F'],
    ],
    Text: [
      ['--text-primary', 'text.primary', '#FAFAFA'],
      ['--text-secondary', 'text.secondary', '#A3A3A3'],
      ['--text-tertiary', 'text.tertiary', '#737373'],
      ['--text-disabled', 'text.disabled', '#525252'],
    ],
    Borders: [
      ['--border-subtle', 'border.subtle', '#1F1F1F'],
      ['--border-default', 'border.default', '#262626'],
      ['--border-strong', 'border.strong', '#333333'],
    ],
    Accent: [
      ['--accent', 'accent', '#3B82F6'],
      ['--accent-hover', 'accent.hover', '#60A5FA'],
      ['--accent-soft', 'accent.soft', 'rgba(59,130,246,.12)'],
    ],
    'Estado financiero': [
      ['--pos', 'pos · ingreso', '#10B981'],
      ['--pos-soft', 'pos.soft', 'rgba(16,185,129,.12)'],
      ['--neg', 'neg · egreso', '#EF4444'],
      ['--neg-soft', 'neg.soft', 'rgba(239,68,68,.12)'],
      ['--warn', 'warn', '#F59E0B'],
      ['--warn-soft', 'warn.soft', 'rgba(245,158,11,.12)'],
    ],
  },
};

const ColorPalette = ({ theme }) => {
  const groups = COLOR_GROUPS[theme];
  return (
    <Themed theme={theme} style={{ padding: 'var(--s-6)', overflowY: 'auto' }}>
      <div style={{ marginBottom: 'var(--s-5)' }}>
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>01 · Foundations</div>
        <div style={{ fontSize: 26, fontWeight: 600, letterSpacing: '-0.03em', marginTop: 4 }}>Paleta · {theme === 'light' ? 'Claro' : 'Oscuro'}</div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 6, maxWidth: 540 }}>
          Tokens semánticos. Usa siempre la variable, nunca el HEX. Cada token mapea a un color de Material 3 en Flet.
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--s-4)' }}>
        {Object.entries(groups).map(([groupName, items]) => (
          <div key={groupName}>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                          letterSpacing: '0.06em', textTransform: 'uppercase',
                          marginBottom: 8 }}>{groupName}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {items.map(([v, l, h]) => <Swatch key={v} varName={v} label={l} hex={h} />)}
            </div>
          </div>
        ))}
      </div>
    </Themed>
  );
};

// ============== TYPE SCALE ==============
const TypeRow = ({ label, sample, size, weight, lh, ls, mono, role }) => (
  <div style={{ display: 'grid', gridTemplateColumns: '110px 1fr 200px', gap: 24,
                alignItems: 'baseline',
                padding: '18px 0',
                borderBottom: '1px solid var(--border-subtle)' }}>
    <div>
      <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>{label}</div>
      <div className="mono" style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2 }}>{role}</div>
    </div>
    <div style={{
      fontSize: size, fontWeight: weight, lineHeight: lh, letterSpacing: ls,
      fontFamily: mono ? 'var(--font-mono)' : 'var(--font-sans)',
      color: 'var(--text-primary)',
    }}>{sample}</div>
    <div className="mono" style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
      {mono ? 'Geist Mono' : 'Geist'} · {size}/{lh} · {weight}
    </div>
  </div>
);

const Typography = ({ theme }) => (
  <Themed theme={theme} style={{ padding: 'var(--s-6)', overflowY: 'auto' }}>
    <div style={{ marginBottom: 'var(--s-5)' }}>
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>02 · Foundations</div>
      <div style={{ fontSize: 26, fontWeight: 600, letterSpacing: '-0.03em', marginTop: 4 }}>Tipografía</div>
      <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 6, maxWidth: 540 }}>
        Geist para UI · Geist Mono para todos los números financieros (tabular, alineados). Pareja moderna estilo Vercel/Linear.
      </div>
    </div>
    <div>
      <TypeRow label="Display"  role="Pantallas vacías"      sample="Sin movimientos hoy"     size={36} weight={600} lh={1.1} ls="-0.04em" />
      <TypeRow label="Title XL" role="Encabezado de sección" sample="Caja diaria"             size={26} weight={600} lh={1.15} ls="-0.03em" />
      <TypeRow label="Title L"  role="Títulos de página"     sample="Movimientos recientes"   size={20} weight={600} lh={1.2} ls="-0.025em" />
      <TypeRow label="Title M"  role="Cards"                 sample="Total ingresos"          size={16} weight={600} lh={1.3} ls="-0.02em" />
      <TypeRow label="Body"     role="Texto principal"       sample="Lavado completo · Toyota Hilux ABC 123" size={14} weight={400} lh={1.5} ls="-0.01em" />
      <TypeRow label="Body S"   role="Secundario"            sample="Hace 4 minutos · Caja 1" size={13} weight={400} lh={1.5} ls="-0.005em" />
      <TypeRow label="Caption"  role="Labels, hints"         sample="Método de pago"          size={12} weight={500} lh={1.4} ls="0" />
      <TypeRow label="Overline" role="Etiquetas en CAPS"     sample="EGRESO · OPERACIÓN"      size={11} weight={500} lh={1.4} ls="0.06em" />
      <TypeRow label="Num XL"   role="Total destacado"       sample="Gs. 4.280.000" mono     size={36} weight={600} lh={1.1} ls="-0.04em" />
      <TypeRow label="Num L"    role="KPI"                   sample="Gs. 1.250.000" mono     size={26} weight={600} lh={1.15} ls="-0.03em" />
      <TypeRow label="Num M"    role="Tablas"                sample="Gs. 85.000"    mono     size={14} weight={500} lh={1.5} ls="-0.01em" />
    </div>
  </Themed>
);

// ============== SPACING + RADII + SHADOWS ==============
const Tokens = ({ theme }) => (
  <Themed theme={theme} style={{ padding: 'var(--s-6)', overflowY: 'auto' }}>
    <div style={{ marginBottom: 'var(--s-5)' }}>
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>03 · Foundations</div>
      <div style={{ fontSize: 26, fontWeight: 600, letterSpacing: '-0.03em', marginTop: 4 }}>Spacing · Radii · Shadows</div>
    </div>

    {/* Spacing */}
    <div style={{ marginBottom: 'var(--s-6)' }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                    letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 12 }}>
        Spacing scale · base 4px
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {[
          ['s-1', 4],['s-2', 8],['s-3', 12],['s-4', 16],
          ['s-5', 24],['s-6', 32],['s-7', 48],['s-8', 64],
        ].map(([t, px]) => (
          <div key={t} style={{ display: 'grid', gridTemplateColumns: '60px 60px 1fr', alignItems: 'center', gap: 12 }}>
            <span className="mono" style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{t}</span>
            <span className="mono" style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{px}px</span>
            <div style={{ height: 12, background: 'var(--accent)', width: px, borderRadius: 2 }} />
          </div>
        ))}
      </div>
    </div>

    {/* Radii */}
    <div style={{ marginBottom: 'var(--s-6)' }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                    letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 12 }}>
        Border radius
      </div>
      <div style={{ display: 'flex', gap: 16 }}>
        {[['sm', 6, 'inputs · badges'], ['md', 8, 'botones'], ['lg', 12, 'cards'], ['xl', 16, 'modales']].map(([n, px, use]) => (
          <div key={n} style={{ flex: 1, textAlign: 'center' }}>
            <div style={{ height: 64, background: 'var(--bg-surface)',
                          border: '1px solid var(--border-default)',
                          borderRadius: px, marginBottom: 8 }} />
            <div className="mono" style={{ fontSize: 11, color: 'var(--text-secondary)' }}>r-{n} · {px}px</div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{use}</div>
          </div>
        ))}
      </div>
    </div>

    {/* Elevations */}
    <div>
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                    letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 12 }}>
        Elevation · sombras planas
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
        {[['xs', 'cards · botones'], ['sm', 'hover'], ['md', 'dropdowns'], ['lg', 'popovers']].map(([n, use]) => (
          <div key={n} style={{ textAlign: 'center', padding: 8 }}>
            <div style={{ height: 64, background: 'var(--bg-surface)',
                          border: '1px solid var(--border-default)',
                          borderRadius: 12, marginBottom: 12,
                          boxShadow: `var(--shadow-${n})` }} />
            <div className="mono" style={{ fontSize: 11, color: 'var(--text-secondary)' }}>shadow-{n}</div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{use}</div>
          </div>
        ))}
      </div>
    </div>
  </Themed>
);

Object.assign(window, { ColorPalette, Typography, Tokens });
