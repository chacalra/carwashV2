// ds-responsive.jsx — Mobile-first Registrar Ingreso + tablet vertical + responsive docs.
// Mapped to Flet ResponsiveRow / col conventions.

// Breakpoints aligned to MD3 + Flet
const BP = {
  xs: { range: '< 600',     name: 'Móvil',           cols: 4 },
  sm: { range: '600–904',   name: 'Móvil grande',    cols: 8 },
  md: { range: '905–1239',  name: 'Tablet vertical', cols: 12 },
  lg: { range: '1240–1439', name: 'Desktop',         cols: 12 },
  xl: { range: '≥ 1440',    name: 'Desktop wide',    cols: 12 },
};

// ============== MOBILE: REGISTRAR INGRESO ==============
// 4 stacked steps in a single scrollable view, optimized for thumb reach
// and single-hand operation. Sticky CTA bottom. 48px+ hit targets.
const MobileIngreso = () => {
  const SERVICES = [
    ['Lavado básico',     '35.000',  false],
    ['Lavado completo',   '85.000',  false],
    ['Encerado premium',  '220.000', true],
    ['Aspirado interior', '45.000',  false],
    ['Pulido óptico',     '180.000', false],
    ['Detallado full',    '450.000', false],
  ];
  const PAYS = [['Efectivo', true], ['Transfer.', false], ['Tarjeta', false], ['QR', false]];

  return (
    <Themed theme="light" style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Header — back + title + step indicator */}
      <header style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '14px 16px',
        background: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-subtle)',
        position: 'sticky', top: 0, zIndex: 5,
      }}>
        <button style={{
          width: 40, height: 40, borderRadius: 10, border: 'none',
          background: 'var(--bg-sunken)', color: 'var(--text-primary)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon name="chevron_right" size={18} stroke={2} color="var(--text-primary)" />
        </button>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Caja 1 · Andrés</div>
          <div style={{ fontSize: 16, fontWeight: 600, letterSpacing: '-0.02em' }}>Nuevo ingreso</div>
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {[1,2,3,4].map(n => (
            <span key={n} style={{
              width: 18, height: 4, borderRadius: 2,
              background: n <= 2 ? 'var(--accent)' : 'var(--bg-sunken)',
            }} />
          ))}
        </div>
      </header>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 16px 120px' }}>
        {/* Step 1 — Service */}
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                      letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 10 }}>
          1 · Servicio
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 24 }}>
          {SERVICES.map(([n, p, sel]) => (
            <div key={n} style={{
              padding: 14, minHeight: 76,
              borderRadius: 12,
              border: `1.5px solid ${sel ? 'var(--accent)' : 'var(--border-default)'}`,
              background: sel ? 'var(--accent-soft)' : 'var(--bg-surface)',
              display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
              position: 'relative',
            }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: sel ? 'var(--accent)' : 'var(--text-primary)', lineHeight: 1.3 }}>{n}</div>
              <div className="num" style={{ fontSize: 14, fontWeight: 600, marginTop: 6,
                                              color: sel ? 'var(--accent)' : 'var(--text-primary)' }}>
                Gs. {p}
              </div>
              {sel && (
                <div style={{ position: 'absolute', top: 8, right: 8,
                              width: 18, height: 18, borderRadius: 999,
                              background: 'var(--accent)',
                              display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon name="check" size={11} stroke={3} color="#fff" />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Step 2 — Vehicle */}
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                      letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 10 }}>
          2 · Vehículo
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 24 }}>
          {/* Larger inputs — 48px height — touch-friendly */}
          <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)' }}>Patente</span>
            <div style={{
              display: 'flex', alignItems: 'center',
              height: 48, padding: '0 14px',
              background: 'var(--bg-surface)',
              border: '1.5px solid var(--accent)',
              borderRadius: 12,
              boxShadow: '0 0 0 4px var(--accent-soft)',
            }}>
              <span className="mono" style={{ fontSize: 18, fontWeight: 600, letterSpacing: '0.05em' }}>CDE 789</span>
              <span style={{ width: 2, height: 22, background: 'var(--accent)', marginLeft: 4,
                              animation: 'blink 1s infinite' }} />
            </div>
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)' }}>Marca y modelo</span>
            <div style={{
              display: 'flex', alignItems: 'center',
              height: 48, padding: '0 14px',
              background: 'var(--bg-surface)',
              border: '1.5px solid var(--border-default)',
              borderRadius: 12,
            }}>
              <span style={{ fontSize: 15, color: 'var(--text-primary)' }}>BMW X3</span>
            </div>
          </label>
        </div>

        {/* Step 3 — Cliente (compact) */}
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                      letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 10 }}>
          3 · Cliente <span style={{ textTransform: 'none', letterSpacing: 0, color: 'var(--text-tertiary)', fontWeight: 400 }}>· opcional</span>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: 12,
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-default)',
          borderRadius: 12,
          marginBottom: 24,
        }}>
          <div style={{ width: 40, height: 40, borderRadius: 999, background: 'var(--accent-soft)',
                        color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 13, fontWeight: 600 }}>RC</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14, fontWeight: 500 }}>Ricardo Cárdenas</div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>18 servicios · frecuente</div>
          </div>
          <Badge tone="accent">−10%</Badge>
        </div>

        {/* Step 4 — Payment */}
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                      letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 10 }}>
          4 · Método de pago
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 6, marginBottom: 16 }}>
          {PAYS.map(([n, sel]) => (
            <div key={n} style={{
              padding: '14px 6px', minHeight: 56,
              borderRadius: 12,
              border: `1.5px solid ${sel ? 'var(--accent)' : 'var(--border-default)'}`,
              background: sel ? 'var(--accent-soft)' : 'var(--bg-surface)',
              color: sel ? 'var(--accent)' : 'var(--text-secondary)',
              fontSize: 12, fontWeight: 500, textAlign: 'center',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>{n}</div>
          ))}
        </div>

        {/* Numeric keypad-friendly amount field */}
        <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)' }}>Recibido</span>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            height: 56, padding: '0 16px',
            background: 'var(--bg-surface)',
            border: '1.5px solid var(--border-default)',
            borderRadius: 12,
          }}>
            <span className="mono" style={{ fontSize: 14, color: 'var(--text-tertiary)' }}>Gs.</span>
            <span className="num" style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.02em' }}>200.000</span>
          </div>
          <span style={{ fontSize: 12, color: 'var(--pos-fg)', marginTop: 4 }}>
            Vuelto: <span className="num" style={{ fontWeight: 500 }}>Gs. 2.000</span>
          </span>
        </label>
      </div>

      {/* Sticky bottom CTA — total + button */}
      <div style={{
        position: 'sticky', bottom: 0,
        padding: '14px 16px 22px',
        background: 'var(--bg-surface)',
        borderTop: '1px solid var(--border-subtle)',
        boxShadow: '0 -8px 16px rgba(0,0,0,0.04)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 10 }}>
          <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Total a cobrar</span>
          <span className="num" style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.025em' }}>Gs. 198.000</span>
        </div>
        <button style={{
          width: '100%', height: 52,
          background: 'var(--pos)', color: '#fff',
          border: 'none', borderRadius: 12,
          fontFamily: 'inherit', fontSize: 15, fontWeight: 600,
          letterSpacing: '-0.01em',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.18), 0 4px 12px rgba(5,150,105,0.25)',
        }}>
          <Icon name="check" size={18} stroke={2.4} color="#fff" />
          Cobrar Gs. 198.000
        </button>
      </div>
    </Themed>
  );
};

// ============== TABLET VERTICAL: REGISTRAR INGRESO ==============
// 2-column adaptive: form left, summary right (sticky).
// Larger touch targets than desktop, but uses the available width.
const TabletIngreso = () => (
  <Themed theme="light">
    <header style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '18px 24px',
      background: 'var(--bg-surface)',
      borderBottom: '1px solid var(--border-subtle)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <button style={{ width: 40, height: 40, borderRadius: 10, border: 'none',
                          background: 'var(--bg-sunken)' }}>
          <Icon name="chevron_right" size={18} stroke={2} />
        </button>
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Caja 1 · Andrés</div>
          <div style={{ fontSize: 18, fontWeight: 600, letterSpacing: '-0.02em' }}>Registrar ingreso</div>
        </div>
      </div>
      <Button variant="ghost" size="md">Cancelar</Button>
    </header>

    <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 16, padding: 20 }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <Card title="Servicio">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10 }}>
            {[
              ['Lavado básico',    '35.000',  false],
              ['Lavado completo',  '85.000',  false],
              ['Encerado premium', '220.000', true],
              ['Aspirado interior','45.000',  false],
              ['Pulido óptico',    '180.000', false],
              ['Detallado full',   '450.000', false],
            ].map(([n, p, sel]) => (
              <div key={n} style={{
                padding: 16, minHeight: 76,
                borderRadius: 12,
                border: `1.5px solid ${sel ? 'var(--accent)' : 'var(--border-default)'}`,
                background: sel ? 'var(--accent-soft)' : 'var(--bg-surface)',
              }}>
                <div style={{ fontSize: 14, fontWeight: 500, color: sel ? 'var(--accent)' : 'var(--text-primary)' }}>{n}</div>
                <div className="num" style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 6 }}>Gs. {p}</div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Vehículo y operario">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Input label="Patente" value="CDE 789" />
            <Input label="Marca y modelo" value="BMW X3" />
            <Input label="Operario" value="Ramón Duarte" trailing={<Icon name="chevron_down" size={15} />} />
            <Input label="Tiempo estimado" suffix="min" value="45" />
          </div>
        </Card>
      </div>

      <Card title="Cobro">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, paddingBottom: 14,
                      borderBottom: '1px solid var(--border-subtle)' }}>
          {[['Encerado premium', 220000], ['Descuento frecuente', -22000]].map(([l, v]) => (
            <div key={l} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span style={{ color: 'var(--text-secondary)' }}>{l}</span>
              <span className="num" style={{ fontWeight: 500, color: v < 0 ? 'var(--neg-fg)' : 'var(--text-primary)' }}>
                {fmtPYG(v, { sign: v < 0 })}
              </span>
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '14px 0' }}>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Total</span>
          <span className="num" style={{ fontSize: 26, fontWeight: 600, letterSpacing: '-0.03em' }}>Gs. 198.000</span>
        </div>

        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                      letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 8 }}>
          Método de pago
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8, marginBottom: 14 }}>
          {[['Efectivo', true],['Transferencia', false],['Tarjeta', false],['QR', false]].map(([n, sel]) => (
            <div key={n} style={{
              padding: '14px 12px', borderRadius: 10,
              border: `1.5px solid ${sel ? 'var(--accent)' : 'var(--border-default)'}`,
              background: sel ? 'var(--accent-soft)' : 'var(--bg-surface)',
              color: sel ? 'var(--accent)' : 'var(--text-secondary)',
              fontSize: 13, fontWeight: 500, textAlign: 'center', minHeight: 48,
            }}>{n}</div>
          ))}
        </div>

        <Input label="Recibido" prefix="Gs." value="200.000" />
        <button style={{
          width: '100%', height: 52, marginTop: 16,
          background: 'var(--pos)', color: '#fff',
          border: 'none', borderRadius: 12,
          fontFamily: 'inherit', fontSize: 15, fontWeight: 600,
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
        }}>
          <Icon name="check" size={18} stroke={2.4} color="#fff" />
          Cobrar Gs. 198.000
        </button>
      </Card>
    </div>
  </Themed>
);

// ============== RESPONSIVE DOCS ==============
const ResponsiveDocs = () => (
  <Themed theme="light" style={{ padding: 32, overflowY: 'auto' }}>
    <div style={{ marginBottom: 24 }}>
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>11 · Responsive</div>
      <div style={{ fontSize: 26, fontWeight: 600, letterSpacing: '-0.03em', marginTop: 4 }}>Sistema responsive · Flet</div>
      <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8, maxWidth: 580, lineHeight: 1.55 }}>
        Breakpoints alineados a Material Design 3 + grid de 12 columnas para `ft.ResponsiveRow`. Mobile-first: el layout móvil es la base y crece hacia arriba.
      </div>
    </div>

    {/* Breakpoints */}
    <div style={{ marginBottom: 32 }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                    letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 12 }}>
        Breakpoints
      </div>
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-default)',
                    borderRadius: 12, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: 'var(--bg-sunken)' }}>
              {['Token', 'Rango (px)', 'Dispositivo', 'Cols ResponsiveRow', 'Padding', 'Gap'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '11px 16px',
                                      fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                                      letterSpacing: '0.06em', textTransform: 'uppercase',
                                      borderBottom: '1px solid var(--border-subtle)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              ['xs', '< 600',     'Móvil',           '4 cols',  '16px', '8/12'],
              ['sm', '600–904',   'Móvil grande',    '8 cols',  '20px', '12'],
              ['md', '905–1239',  'Tablet vertical', '12 cols', '24px', '16'],
              ['lg', '1240–1439', 'Desktop',         '12 cols', '32px', '16'],
              ['xl', '≥ 1440',    'Desktop wide',    '12 cols', '40px', '24'],
            ].map(([t, r, d, c, p, g]) => (
              <tr key={t} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <td className="mono" style={{ padding: '12px 16px', fontWeight: 500, color: 'var(--accent)' }}>{t}</td>
                <td className="mono" style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{r}</td>
                <td style={{ padding: '12px 16px', color: 'var(--text-primary)' }}>{d}</td>
                <td className="mono" style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{c}</td>
                <td className="mono" style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{p}</td>
                <td className="mono" style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{g}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>

    {/* Visual breakpoint diagram */}
    <div style={{ marginBottom: 32 }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                    letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 12 }}>
        Reflow de Registrar Ingreso
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
        {[
          { lbl: 'xs · Móvil', w: 320, layout: ['Servicio (2col)', 'Vehículo (1col)', 'Cliente', 'Pago (4col)', 'CTA sticky'] },
          { lbl: 'md · Tablet', w: 720, layout: ['Form izq · Cobro der', '2 cols cards', 'CTA en card'] },
          { lbl: 'lg · Desktop', w: 1280, layout: ['Sidebar · Form · Cobro', '3 cols servicios', 'CTA en topbar'] },
        ].map(b => (
          <div key={b.lbl}>
            <div className="mono" style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 6 }}>{b.lbl} · {b.w}px</div>
            <div style={{
              border: '1.5px solid var(--border-default)',
              borderRadius: 10, padding: 8,
              background: 'var(--bg-surface)',
              display: 'flex', flexDirection: 'column', gap: 5,
            }}>
              {b.layout.map((l, i) => (
                <div key={i} style={{
                  height: 24, borderRadius: 5,
                  background: i === b.layout.length - 1 ? 'var(--accent)' : 'var(--bg-sunken)',
                  color: i === b.layout.length - 1 ? '#fff' : 'var(--text-secondary)',
                  fontSize: 10, padding: '0 8px',
                  display: 'flex', alignItems: 'center',
                }}>{l}</div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>

    {/* Touch targets */}
    <div style={{ marginBottom: 32 }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                    letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 12 }}>
        Tamaños táctiles · mínimo 44px (Apple HIG) · 48px recomendado (MD3)
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        {[
          ['Botón primario', '52px', 'Sticky CTA móvil'],
          ['Inputs',         '48px', 'Más alto que desktop (38px)'],
          ['Service chips',  '76px', 'Mínima altura 2 líneas + monto'],
          ['Pago tabs',      '56px', 'Cuadrícula 4×56'],
        ].map(([l, h, n]) => (
          <div key={l} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-default)',
                                 borderRadius: 10, padding: 14 }}>
            <div className="num" style={{ fontSize: 22, fontWeight: 600, color: 'var(--accent)' }}>{h}</div>
            <div style={{ fontSize: 13, fontWeight: 500, marginTop: 4 }}>{l}</div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>{n}</div>
          </div>
        ))}
      </div>
    </div>

    {/* Flet code */}
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                    letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 12 }}>
        Implementación · Flet ResponsiveRow
      </div>
      <div className="mono" style={{
        background: '#0A0A0A', color: '#E4E4E0',
        padding: 18, borderRadius: 10,
        fontSize: 12, lineHeight: 1.65,
        whiteSpace: 'pre', overflowX: 'auto',
      }}>
{`# Servicio cards: 2 cols xs, 3 cols md, 6 cols lg
ft.ResponsiveRow(
    columns=12, spacing=10, run_spacing=10,
    controls=[
        service_card(s, col={"xs": 6, "md": 4, "lg": 2})
        for s in SERVICES
    ],
)

# Form left + summary right (md+) — stacks on xs
ft.ResponsiveRow(
    columns=12, spacing=16,
    controls=[
        ft.Container(content=form,    col={"xs": 12, "md": 7}),
        ft.Container(content=summary, col={"xs": 12, "md": 5}),
    ],
)

# Touch-friendly input (mobile)
ft.TextField(
    label="Patente",
    text_size=18,
    height=48,                     # vs 38 desktop
    border_radius=12,
    keyboard_type=ft.KeyboardType.TEXT,
    text_capitalization=ft.TextCapitalization.CHARACTERS,
)

# Numeric input — opens numpad
ft.TextField(
    label="Recibido", prefix_text="Gs. ",
    keyboard_type=ft.KeyboardType.NUMBER,
    height=56, text_size=22,
    text_style=ft.TextStyle(font_family="Geist Mono", weight=ft.FontWeight.W_600),
)

# Sticky bottom CTA — Stack + alignment
ft.Stack([
    main_scroll_view,
    ft.Container(
        content=cta_button,
        bottom=0, left=0, right=0,
        bgcolor=SURFACE,
        padding=ft.padding.only(left=16, right=16, top=14, bottom=22),
        border=ft.border.only(top=ft.BorderSide(1, BORDER_SUBTLE)),
    ),
])

# Adapt sidebar -> bottom nav
def build_nav(page):
    if page.width < 905:                    # xs/sm
        return ft.NavigationBar(destinations=[...])  # bottom
    return ft.NavigationRail(extended=page.width >= 1240)

page.on_resized = lambda e: page.update()`}
      </div>
    </div>

    {/* Reflow rules */}
    <div>
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                    letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 12 }}>
        Reglas de adaptación
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        {[
          ['Sidebar', 'lg+: NavigationRail extendido · md: rail compacto · xs/sm: NavigationBar (bottom)'],
          ['KPIs',    'lg: 4 en fila · md: 2×2 · xs: 1 col scroll vertical (o carrusel horizontal)'],
          ['Tabla',   'lg/md: DataTable · xs/sm: lista de cards apiladas con monto destacado'],
          ['Forms',   'lg/md: 2 cols · xs/sm: 1 col, 100% ancho'],
          ['Modales', 'md+: AlertDialog centrado · xs: BottomSheet full-height'],
          ['Filtros', 'lg: barra horizontal · xs: BottomSheet con chips'],
          ['Topbar',  'lg: título + acciones inline · xs: título + 1 acción primaria + kebab'],
          ['CTA',     'lg: top-right · xs: sticky bottom 100% width'],
        ].map(([k, v]) => (
          <div key={k} style={{
            padding: 14,
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-default)',
            borderRadius: 10,
          }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)' }}>{k}</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.55 }}>{v}</div>
          </div>
        ))}
      </div>
    </div>
  </Themed>
);

// ============== iPHONE FRAME WRAPPER ==============
const PhoneFrame = ({ children }) => (
  <div style={{
    width: '100%', height: '100%',
    background: '#f0eee9',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: 24,
  }}>
    <div style={{
      width: 390, height: 800,
      background: 'var(--bg-app)',
      borderRadius: 44,
      boxShadow: '0 0 0 12px #1a1a1a, 0 24px 60px rgba(0,0,0,0.18)',
      overflow: 'hidden', position: 'relative',
      display: 'flex', flexDirection: 'column',
    }}>
      {/* Notch / dynamic island */}
      <div style={{
        position: 'absolute', top: 12, left: '50%', transform: 'translateX(-50%)',
        width: 110, height: 30, borderRadius: 999,
        background: '#000', zIndex: 50,
      }} />
      {/* Status bar spacer */}
      <div style={{ height: 50, flex: '0 0 auto', display: 'flex',
                    alignItems: 'center', justifyContent: 'space-between',
                    padding: '0 28px', fontSize: 14, fontWeight: 600,
                    fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif' }}>
        <span>9:41</span>
        <span style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
          <span style={{ width: 16, height: 10, border: '1.2px solid currentColor', borderRadius: 2,
                          position: 'relative' }}>
            <span style={{ position: 'absolute', inset: 1, background: 'currentColor', width: '70%', borderRadius: 1 }} />
          </span>
        </span>
      </div>
      <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
        {children}
      </div>
    </div>
  </div>
);

const TabletFrame = ({ children }) => (
  <div style={{
    width: '100%', height: '100%',
    background: '#f0eee9',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: 20,
  }}>
    <div style={{
      width: 820, height: 1100,
      background: 'var(--bg-app)',
      borderRadius: 28,
      boxShadow: '0 0 0 14px #1a1a1a, 0 24px 60px rgba(0,0,0,0.18)',
      overflow: 'hidden',
      display: 'flex', flexDirection: 'column',
    }}>
      {children}
    </div>
  </div>
);

Object.assign(window, { MobileIngreso, TabletIngreso, ResponsiveDocs, PhoneFrame, TabletFrame });
