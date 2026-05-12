// ds-screens.jsx — Real product screens applied to the design system.
// Each screen is wrapped in <Themed> and rendered inside its own <DCArtboard>.

// ============== SHARED: SIDEBAR ==============
const navItems = [
  ['dashboard', 'Dashboard', true],
  ['cash',      'Caja diaria', false],
  ['arrow_in',  'Ingresos',  false],
  ['arrow_out', 'Egresos',   false],
  ['list',      'Movimientos', false],
  ['chart',     'Reportes',  false],
];

const Sidebar = ({ active = 'Dashboard', collapsed = false }) => (
  <aside style={{
    width: collapsed ? 64 : 232,
    flex: '0 0 auto',
    background: 'var(--bg-surface)',
    borderRight: '1px solid var(--border-subtle)',
    display: 'flex', flexDirection: 'column',
    padding: '20px 12px',
  }}>
    <div style={{ padding: '4px 8px 24px' }}>
      {collapsed
        ? <div style={{ width: 28, height: 28, borderRadius: 8, background: 'var(--text-primary)' }} />
        : <Logo />
      }
    </div>

    {!collapsed && (
      <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)',
                    letterSpacing: '0.08em', textTransform: 'uppercase',
                    padding: '0 10px 8px' }}>Operación</div>
    )}

    <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {navItems.map(([icon, label]) => {
        const isActive = label === active;
        return (
          <div key={label} style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: collapsed ? '9px' : '8px 10px',
            justifyContent: collapsed ? 'center' : 'flex-start',
            borderRadius: 8,
            background: isActive ? 'var(--bg-sunken)' : 'transparent',
            color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
            fontSize: 13, fontWeight: isActive ? 500 : 400,
            cursor: 'pointer', position: 'relative',
          }}>
            {isActive && !collapsed && (
              <span style={{ position: 'absolute', left: 0, top: 8, bottom: 8, width: 2,
                             background: 'var(--accent)', borderRadius: 2 }} />
            )}
            <Icon name={icon} size={17} stroke={isActive ? 1.8 : 1.5} />
            {!collapsed && <span>{label}</span>}
          </div>
        );
      })}
    </nav>

    <div style={{ marginTop: 'auto' }}>
      {!collapsed && (
        <div style={{
          padding: 12, borderRadius: 10,
          background: 'var(--bg-sunken)',
          marginBottom: 12,
        }}>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Caja 1 · abierta</div>
          <div className="num" style={{ fontSize: 14, fontWeight: 600, marginTop: 2 }}>Gs. 3.595.000</div>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 6 }}>Desde 07:30 · Andrés</div>
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px' }}>
        <div style={{ width: 28, height: 28, borderRadius: 999, background: 'var(--accent-soft)',
                      color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 12, fontWeight: 600 }}>AC</div>
        {!collapsed && (
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 12, fontWeight: 500 }}>Andrés Cárdenas</div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Operador · Caja 1</div>
          </div>
        )}
        {!collapsed && <Icon name="settings" size={15} color="var(--text-tertiary)" />}
      </div>
    </div>
  </aside>
);

// ============== SHARED: TOP BAR ==============
const TopBar = ({ title, subtitle, actions }) => (
  <header style={{
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '20px 32px', borderBottom: '1px solid var(--border-subtle)',
    background: 'var(--bg-app)',
  }}>
    <div>
      <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{subtitle}</div>
      <div style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.025em', marginTop: 2 }}>{title}</div>
    </div>
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>{actions}</div>
  </header>
);

const AppShell = ({ active, title, subtitle, actions, children }) => (
  <div style={{ display: 'flex', height: '100%', minHeight: 0 }}>
    <Sidebar active={active} />
    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <TopBar title={title} subtitle={subtitle} actions={actions} />
      <main style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: '24px 32px 40px' }}>
        {children}
      </main>
    </div>
  </div>
);

// ============== SCREEN: DASHBOARD ==============
const cashflowData = [
  { d: 'L',  in: 3.4, out: 0.6 },
  { d: 'M',  in: 4.1, out: 0.9 },
  { d: 'M',  in: 3.8, out: 0.7 },
  { d: 'J',  in: 4.6, out: 1.1 },
  { d: 'V',  in: 5.2, out: 0.8 },
  { d: 'S',  in: 6.4, out: 1.2 },
  { d: 'D',  in: 4.3, out: 0.7 },
];

const CashflowChart = () => {
  const W = 720, H = 220, P = { t: 12, r: 12, b: 28, l: 44 };
  const innerW = W - P.l - P.r, innerH = H - P.t - P.b;
  const max = 7;
  const barW = innerW / cashflowData.length / 3;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 220, display: 'block' }}>
      {/* gridlines */}
      {[0, 2, 4, 6].map(v => {
        const y = P.t + innerH - (v / max) * innerH;
        return (
          <g key={v}>
            <line x1={P.l} x2={W - P.r} y1={y} y2={y} stroke="var(--border-subtle)" strokeWidth="1" />
            <text x={P.l - 8} y={y + 3} fontSize="10" fill="var(--text-tertiary)" textAnchor="end" fontFamily="var(--font-mono)">
              {v}M
            </text>
          </g>
        );
      })}
      {/* bars */}
      {cashflowData.map((d, i) => {
        const cx = P.l + (i + 0.5) * (innerW / cashflowData.length);
        const inH = (d.in / max) * innerH;
        const outH = (d.out / max) * innerH;
        return (
          <g key={i}>
            <rect x={cx - barW - 1} y={P.t + innerH - inH} width={barW} height={inH}
                  fill="var(--pos)" rx="2" />
            <rect x={cx + 1} y={P.t + innerH - outH} width={barW} height={outH}
                  fill="var(--neg)" rx="2" opacity="0.85" />
            <text x={cx} y={H - 8} fontSize="11" fill="var(--text-tertiary)" textAnchor="middle">{d.d}</text>
          </g>
        );
      })}
    </svg>
  );
};

const Dashboard = ({ theme }) => (
  <Themed theme={theme}>
    <AppShell
      active="Dashboard"
      subtitle="Operación · Caja 1"
      title="Buen día, Andrés"
      actions={<>
        <Button variant="secondary" size="sm" leading={<Icon name="calendar" size={14} />}>Hoy · 07 may</Button>
        <Button variant="primary" size="sm" leading={<Icon name="plus" size={14} />}>Nuevo movimiento</Button>
      </>}
    >
      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        <KPI label="Ingresos del día" value="Gs. 4.280.000" delta="+12.4%" deltaTone="pos"
             hint="vs. promedio semanal"
             sparkline={<Sparkline data={[3,5,4,7,6,9,8,11,10,12]} color="var(--pos)" />} />
        <KPI label="Egresos del día" value="Gs. 685.000" delta="−4.1%" deltaTone="pos"
             hint="bajo presupuesto"
             sparkline={<Sparkline data={[5,4,6,3,5,4,3,4,3,2]} color="var(--neg)" />} />
        <KPI label="Balance neto" value="Gs. 3.595.000" delta="+18.2%" deltaTone="pos"
             hint="utilidad operativa"
             sparkline={<Sparkline data={[2,4,3,5,7,6,8,9,11,10]} color="var(--accent)" />} />
        <KPI label="Servicios" value="34" delta="+6" deltaTone="pos"
             hint="ticket prom. Gs. 125.882"
             sparkline={<Sparkline data={[4,5,6,5,8,7,9,8,10,11]} color="var(--text-secondary)" fill={false} />} />
      </div>

      {/* Chart + Side */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 16, marginBottom: 24 }}>
        <Card
          padding="0"
          title="Flujo de caja"
          action={<Row>
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 8, height: 8, borderRadius: 2, background: 'var(--pos)' }} /> Ingresos
            </span>
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 8, height: 8, borderRadius: 2, background: 'var(--neg)' }} /> Egresos
            </span>
            <Button variant="ghost" size="sm" trailing={<Icon name="chevron_down" size={14} />}>Esta semana</Button>
          </Row>}
        >
          <div style={{ padding: 'var(--s-4) var(--s-5)' }}>
            <CashflowChart />
          </div>
        </Card>

        <Card title="Métodos de pago" action={<span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Hoy</span>}>
          {[
            ['Efectivo',       'Gs. 2.450.000', 57, 'var(--accent)'],
            ['Transferencia',  'Gs. 1.180.000', 28, 'var(--pos)'],
            ['Tarjeta',        'Gs. 520.000',   12, 'var(--warn)'],
            ['QR · Pago Móvil','Gs. 130.000',    3, 'var(--text-tertiary)'],
          ].map(([n, m, p, c]) => (
            <div key={n} style={{ marginBottom: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13 }}>
                <span style={{ color: 'var(--text-secondary)' }}>{n}</span>
                <span className="num" style={{ fontWeight: 500 }}>{m}</span>
              </div>
              <div style={{ height: 6, background: 'var(--bg-sunken)', borderRadius: 999, overflow: 'hidden' }}>
                <div style={{ width: `${p}%`, height: '100%', background: c, borderRadius: 999 }} />
              </div>
            </div>
          ))}
        </Card>
      </div>

      {/* Recent movements */}
      <Card title="Movimientos recientes" padding="0"
        action={<Button variant="ghost" size="sm" trailing={<Icon name="arrow_right" size={14} />}>Ver todos</Button>}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr>
              {['Hora','Tipo','Detalle','Método','Estado','Monto'].map((h, i) => (
                <th key={h} style={{
                  textAlign: i === 5 ? 'right' : 'left',
                  padding: '10px 20px',
                  fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                  letterSpacing: '0.06em', textTransform: 'uppercase',
                  borderBottom: '1px solid var(--border-subtle)',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              ['14:32', 'in',  'Lavado completo',  'Toyota Hilux · ABC 123',    'Efectivo',      ['pos','Cobrado'],   85000],
              ['14:18', 'in',  'Aspirado interior','Honda Fit · BCD 456',       'Transferencia', ['accent','En curso'], 45000],
              ['13:55', 'in',  'Encerado premium', 'BMW X3 · CDE 789',           'Tarjeta',       ['pos','Cobrado'],  220000],
              ['13:40', 'out', 'Compra de jabón',  'Distribuidora Sur · F-2841', 'Efectivo',      ['pos','Pagado'],   -180000],
              ['13:12', 'in',  'Lavado básico',    'Volkswagen Gol · DEF 012',   'Efectivo',      ['warn','Pendiente'], 35000],
            ].map(([h, type, det, sub, m, st, mt], i) => (
              <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <td className="mono" style={{ padding: '14px 20px', color: 'var(--text-tertiary)' }}>{h}</td>
                <td style={{ padding: '14px 20px' }}>
                  <span style={{
                    width: 26, height: 26, borderRadius: 8,
                    background: type === 'in' ? 'var(--pos-soft)' : 'var(--neg-soft)',
                    color: type === 'in' ? 'var(--pos)' : 'var(--neg)',
                    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <Icon name={type === 'in' ? 'arrow_in' : 'arrow_out'} size={14} stroke={2} />
                  </span>
                </td>
                <td style={{ padding: '14px 20px' }}>
                  <div style={{ fontWeight: 500 }}>{det}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>{sub}</div>
                </td>
                <td style={{ padding: '14px 20px' }}><Badge tone="neutral">{m}</Badge></td>
                <td style={{ padding: '14px 20px' }}><Badge tone={st[0]} dot>{st[1]}</Badge></td>
                <td className="num" style={{ padding: '14px 20px', textAlign: 'right', fontWeight: 500,
                                              color: mt < 0 ? 'var(--neg-fg)' : 'var(--text-primary)' }}>
                  {fmtPYG(mt, { sign: true })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </AppShell>
  </Themed>
);

// ============== SCREEN: CAJA DIARIA ==============
const CajaDiaria = ({ theme }) => (
  <Themed theme={theme}>
    <AppShell
      active="Caja diaria"
      subtitle="Operación"
      title="Caja diaria · Caja 1"
      actions={<>
        <Badge tone="pos" dot>Abierta · 06h 47m</Badge>
        <Button variant="secondary" size="sm" leading={<Icon name="print" size={14} />}>Imprimir arqueo</Button>
        <Button variant="primary" size="sm" leading={<Icon name="lock" size={14} />}>Cerrar caja</Button>
      </>}
    >
      {/* Status strip */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--r-lg)',
        boxShadow: 'var(--shadow-xs)',
        marginBottom: 24,
        overflow: 'hidden',
      }}>
        {[
          ['Apertura', 'Gs. 200.000', '07:30 · Andrés C.'],
          ['Ingresos', 'Gs. 4.280.000', '34 servicios'],
          ['Egresos',  'Gs. 685.000',   '4 movimientos'],
          ['Saldo en caja', 'Gs. 3.795.000', 'Esperado · físico por arquear'],
        ].map(([l, v, h], i) => (
          <div key={l} style={{
            padding: 'var(--s-5)',
            borderRight: i < 3 ? '1px solid var(--border-subtle)' : 'none',
          }}>
            <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-tertiary)',
                          letterSpacing: '0.04em', textTransform: 'uppercase' }}>{l}</div>
            <div className="num" style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.025em', marginTop: 8,
                                          color: i === 3 ? 'var(--accent)' : 'var(--text-primary)' }}>{v}</div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 6 }}>{h}</div>
          </div>
        ))}
      </div>

      {/* Arqueo + denominaciones */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 16, marginBottom: 24 }}>
        <Card title="Arqueo de efectivo" action={<Badge tone="warn" dot>En proceso</Badge>}>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 16 }}>
            Contá los billetes y monedas físicos. El sistema calcula la diferencia automáticamente.
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10 }}>
            {[
              ['100.000', 18, 1800000],
              ['50.000',  21, 1050000],
              ['20.000',  14, 280000],
              ['10.000',  19, 190000],
              ['5.000',    8, 40000],
              ['2.000',   12, 24000],
              ['1.000',   15, 15000],
              ['500',     22, 11000],
            ].map(([den, qty, total]) => (
              <div key={den} style={{
                display: 'grid', gridTemplateColumns: '70px 1fr 100px',
                alignItems: 'center', gap: 10,
                padding: '8px 12px',
                background: 'var(--bg-sunken)',
                borderRadius: 'var(--r-md)',
                border: '1px solid var(--border-subtle)',
              }}>
                <span className="num" style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)' }}>{den}</span>
                <Input style={{ marginBottom: 0 }} prefix="×" value={String(qty)} />
                <span className="num" style={{ fontSize: 12, fontWeight: 500, textAlign: 'right' }}>
                  {fmtPYG(total)}
                </span>
              </div>
            ))}
          </div>
        </Card>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card title="Resumen de cierre">
            {[
              ['Saldo esperado',  'Gs. 3.795.000', 'var(--text-secondary)'],
              ['Conteo físico',   'Gs. 3.410.000', 'var(--text-primary)'],
              ['Diferencia',      '− Gs. 385.000', 'var(--neg-fg)'],
            ].map(([l, v, c]) => (
              <div key={l} style={{ display: 'flex', justifyContent: 'space-between',
                                    padding: '10px 0',
                                    borderBottom: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{l}</span>
                <span className="num" style={{ fontSize: 14, fontWeight: 500, color: c }}>{v}</span>
              </div>
            ))}
            <div style={{ padding: 12, marginTop: 12,
                          background: 'var(--neg-soft)',
                          borderRadius: 8,
                          fontSize: 12, color: 'var(--neg-fg)', lineHeight: 1.5 }}>
              Diferencia significativa. Verificá los billetes de Gs. 100.000 antes de cerrar.
            </div>
            <Button variant="primary" full style={{ marginTop: 16 }} leading={<Icon name="lock" size={15} />}>
              Cerrar caja con diferencia
            </Button>
          </Card>

          <Card title="Próxima caja">
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              Operador siguiente: <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>Lucía Benítez</span>
            </div>
            <Input label="Apertura sugerida" prefix="Gs." value="200.000" style={{ marginTop: 12 }} />
          </Card>
        </div>
      </div>
    </AppShell>
  </Themed>
);

// ============== SCREEN: NUEVO INGRESO ==============
const NuevoIngreso = ({ theme }) => (
  <Themed theme={theme}>
    <AppShell
      active="Ingresos"
      subtitle="Operación · Caja 1"
      title="Registrar ingreso"
      actions={<>
        <Button variant="ghost" size="sm">Cancelar</Button>
        <Button variant="success" size="sm" leading={<Icon name="check" size={14} />}>Cobrar Gs. 220.000</Button>
      </>}
    >
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 16, maxWidth: 1180 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card title="Servicio">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 16 }}>
              {[
                ['Lavado básico',    '35.000',  false],
                ['Lavado completo',  '85.000',  false],
                ['Encerado premium', '220.000', true],
                ['Aspirado interior','45.000',  false],
                ['Pulido óptico',    '180.000', false],
                ['Detallado full',   '450.000', false],
              ].map(([n, p, sel]) => (
                <div key={n} style={{
                  padding: 14,
                  borderRadius: 10,
                  border: `1px solid ${sel ? 'var(--accent)' : 'var(--border-default)'}`,
                  background: sel ? 'var(--accent-soft)' : 'var(--bg-surface)',
                  cursor: 'pointer', position: 'relative',
                }}>
                  <div style={{ fontSize: 13, fontWeight: 500,
                                color: sel ? 'var(--accent)' : 'var(--text-primary)' }}>{n}</div>
                  <div className="num" style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>
                    Gs. {p}
                  </div>
                  {sel && <div style={{ position: 'absolute', top: 8, right: 8 }}><Icon name="check" size={14} color="var(--accent)" stroke={2.5} /></div>}
                </div>
              ))}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
              <Input label="Vehículo" placeholder="Marca y modelo" value="BMW X3" />
              <Input label="Patente" placeholder="ABC 123" value="CDE 789" />
              <Input label="Operario asignado" placeholder="Seleccionar" value="Ramón Duarte" trailing={<Icon name="chevron_down" size={15} />} />
              <Input label="Tiempo estimado" suffix="min" value="45" />
            </div>
          </Card>

          <Card title="Cliente">
            <Row>
              <Input label="Buscar cliente" placeholder="Nombre, cédula o teléfono"
                     leading={<Icon name="search" size={15} />}
                     style={{ flex: 1 }} />
              <div style={{ marginTop: 22 }}>
                <Button variant="secondary" leading={<Icon name="plus" size={15} />}>Nuevo</Button>
              </div>
            </Row>
            <div style={{
              marginTop: 12, padding: 14,
              background: 'var(--bg-sunken)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--r-md)',
              display: 'flex', alignItems: 'center', gap: 12,
            }}>
              <div style={{ width: 36, height: 36, borderRadius: 999, background: 'var(--accent-soft)',
                            color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: 12, fontWeight: 600 }}>RC</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 500 }}>Ricardo Cárdenas</div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>+595 981 234 567 · 18 servicios · Cliente frecuente</div>
              </div>
              <Badge tone="accent">Premium</Badge>
            </div>
          </Card>
        </div>

        <Card title="Resumen y cobro">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, paddingBottom: 16,
                        borderBottom: '1px solid var(--border-subtle)' }}>
            {[
              ['Encerado premium', 220000],
              ['Descuento cliente frecuente', -22000],
            ].map(([l, v]) => (
              <div key={l} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span style={{ color: 'var(--text-secondary)' }}>{l}</span>
                <span className="num" style={{ fontWeight: 500,
                                                color: v < 0 ? 'var(--neg-fg)' : 'var(--text-primary)' }}>
                  {fmtPYG(v, { sign: v < 0 })}
                </span>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                        padding: '16px 0' }}>
            <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Total a cobrar</span>
            <span className="num" style={{ fontSize: 28, fontWeight: 600, letterSpacing: '-0.03em' }}>
              Gs. 198.000
            </span>
          </div>

          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                        letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 8 }}>
            Método de pago
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
            {[
              ['Efectivo', true],
              ['Transferencia', false],
              ['Tarjeta', false],
              ['QR', false],
            ].map(([n, sel]) => (
              <div key={n} style={{
                padding: '10px 12px', borderRadius: 8,
                border: `1px solid ${sel ? 'var(--accent)' : 'var(--border-default)'}`,
                background: sel ? 'var(--accent-soft)' : 'var(--bg-surface)',
                color: sel ? 'var(--accent)' : 'var(--text-secondary)',
                fontSize: 13, fontWeight: 500, textAlign: 'center', cursor: 'pointer',
              }}>{n}</div>
            ))}
          </div>

          <Input label="Recibido" prefix="Gs." value="200.000" style={{ marginTop: 16 }} />
          <div style={{ display: 'flex', justifyContent: 'space-between',
                        padding: '12px 0',
                        fontSize: 13 }}>
            <span style={{ color: 'var(--text-secondary)' }}>Vuelto</span>
            <span className="num" style={{ fontWeight: 500, color: 'var(--pos-fg)' }}>Gs. 2.000</span>
          </div>
        </Card>
      </div>
    </AppShell>
  </Themed>
);

// ============== SCREEN: NUEVO EGRESO ==============
const NuevoEgreso = ({ theme }) => (
  <Themed theme={theme}>
    <AppShell
      active="Egresos"
      subtitle="Operación · Caja 1"
      title="Registrar egreso"
      actions={<>
        <Button variant="ghost" size="sm">Cancelar</Button>
        <Button variant="primary" size="sm" leading={<Icon name="check" size={14} />}>Registrar Gs. 180.000</Button>
      </>}
    >
      <div style={{ maxWidth: 760 }}>
        <Card title="Detalle del egreso">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 14 }}>
            <div style={{ gridColumn: '1 / -1' }}>
              <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 6 }}>Categoría</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {[
                  ['Insumos', true],
                  ['Servicios públicos', false],
                  ['Sueldos', false],
                  ['Mantenimiento', false],
                  ['Combustible', false],
                  ['Otros', false],
                ].map(([n, sel]) => (
                  <span key={n} style={{
                    padding: '8px 14px', borderRadius: 'var(--r-pill)',
                    border: `1px solid ${sel ? 'var(--accent)' : 'var(--border-default)'}`,
                    background: sel ? 'var(--accent-soft)' : 'var(--bg-surface)',
                    color: sel ? 'var(--accent)' : 'var(--text-secondary)',
                    fontSize: 13, fontWeight: 500, cursor: 'pointer',
                  }}>{n}</span>
                ))}
              </div>
            </div>

            <Input label="Concepto" placeholder="Detalle breve" value="Compra de jabón industrial" />
            <Input label="Proveedor" placeholder="Razón social" value="Distribuidora Sur S.A." trailing={<Icon name="chevron_down" size={15} />} />

            <Input label="Monto" prefix="Gs." value="180.000" />
            <Input label="Fecha" value="07/05/2026" trailing={<Icon name="calendar" size={15} />} />

            <Input label="N° comprobante" placeholder="Factura / ticket" value="F-2841" />
            <Input label="Método de pago" value="Efectivo · Caja 1" trailing={<Icon name="chevron_down" size={15} />} />

            <div style={{ gridColumn: '1 / -1' }}>
              <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 6 }}>Comprobante adjunto</div>
              <div style={{
                padding: 24, border: '1.5px dashed var(--border-strong)', borderRadius: 10,
                textAlign: 'center', color: 'var(--text-tertiary)',
                background: 'var(--bg-sunken)',
              }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                  <Icon name="upload" size={16} />
                  <span>Arrastrá una foto o <span style={{ color: 'var(--accent)', fontWeight: 500 }}>buscá un archivo</span></span>
                </div>
                <div style={{ fontSize: 11, marginTop: 6 }}>JPG, PNG o PDF · máx. 5MB</div>
              </div>
            </div>

            <div style={{ gridColumn: '1 / -1' }}>
              <Input label="Notas" placeholder="Observaciones adicionales (opcional)" />
            </div>
          </div>
        </Card>
      </div>
    </AppShell>
  </Themed>
);

// ============== SCREEN: MOVIMIENTOS (table + filters) ==============
const Movimientos = ({ theme }) => (
  <Themed theme={theme}>
    <AppShell
      active="Movimientos"
      subtitle="Operación"
      title="Movimientos"
      actions={<>
        <Button variant="secondary" size="sm" leading={<Icon name="download" size={14} />}>Exportar</Button>
        <Button variant="primary" size="sm" leading={<Icon name="plus" size={14} />}>Nuevo</Button>
      </>}
    >
      {/* Filter bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
        padding: 12, marginBottom: 16,
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--r-lg)',
      }}>
        <Input placeholder="Buscar por cliente, vehículo, concepto…" leading={<Icon name="search" size={15} />}
               style={{ flex: 1, minWidth: 240 }} />
        <Button variant="secondary" size="sm" trailing={<Icon name="chevron_down" size={14} />}>Tipo · Todos</Button>
        <Button variant="secondary" size="sm" trailing={<Icon name="chevron_down" size={14} />}>Método · Todos</Button>
        <Button variant="secondary" size="sm" trailing={<Icon name="chevron_down" size={14} />}>Estado · Todos</Button>
        <Button variant="secondary" size="sm" leading={<Icon name="calendar" size={14} />}>01–07 may</Button>
        <Badge tone="accent" dot>3 filtros activos</Badge>
      </div>

      {/* Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 16 }}>
        {[
          ['Total movimientos', '184',         'neutral'],
          ['Ingresos',          'Gs. 28.450.000', 'pos'],
          ['Egresos',           'Gs. 4.120.000',  'neg'],
          ['Balance',           'Gs. 24.330.000', 'accent'],
        ].map(([l, v, t]) => (
          <div key={l} style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--r-lg)',
            padding: 16, boxShadow: 'var(--shadow-xs)',
          }}>
            <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-tertiary)',
                          letterSpacing: '0.04em', textTransform: 'uppercase' }}>{l}</div>
            <div className="num" style={{ fontSize: 20, fontWeight: 600, marginTop: 6,
                                          color: t === 'pos' ? 'var(--pos-fg)'
                                              : t === 'neg' ? 'var(--neg-fg)'
                                              : t === 'accent' ? 'var(--accent)'
                                              : 'var(--text-primary)' }}>{v}</div>
          </div>
        ))}
      </div>

      <Card padding="0">
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: 'var(--bg-sunken)' }}>
              {['Fecha', 'Tipo', 'Concepto', 'Cliente / Proveedor', 'Método', 'Estado', 'Monto'].map((h, i) => (
                <th key={h} style={{
                  textAlign: i === 6 ? 'right' : 'left',
                  padding: '11px 16px',
                  fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                  letterSpacing: '0.06em', textTransform: 'uppercase',
                  borderBottom: '1px solid var(--border-subtle)',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              ['07/05 · 14:32','in', 'Lavado completo',     'Cárdenas, M.',  'Efectivo',      ['pos','Cobrado'],   85000],
              ['07/05 · 14:18','in', 'Aspirado interior',   'González, R.',  'Transferencia', ['accent','En curso'], 45000],
              ['07/05 · 13:55','in', 'Encerado premium',    'Riveros, A.',   'Tarjeta',       ['pos','Cobrado'],  220000],
              ['07/05 · 13:40','out','Compra de jabón',     'Distrib. Sur',  'Efectivo',      ['pos','Pagado'],  -180000],
              ['07/05 · 13:12','in', 'Lavado básico',       'Martínez, L.',  'Efectivo',      ['warn','Pendiente'], 35000],
              ['07/05 · 12:48','in', 'Detallado full',      'Empresa Pegasus','Transferencia', ['pos','Cobrado'],  450000],
              ['07/05 · 12:15','out','Pago empleado · día', 'Duarte, R.',    'Efectivo',      ['pos','Pagado'],  -220000],
              ['07/05 · 11:30','in', 'Pulido óptico',       'Velázquez, P.', 'QR',            ['pos','Cobrado'],  180000],
              ['07/05 · 10:42','in', 'Lavado completo',     'Acosta, F.',    'Efectivo',      ['neg','Anulado'],   85000],
              ['07/05 · 09:55','out','Combustible · moto',  'Petrobras',     'Efectivo',      ['pos','Pagado'],   -85000],
            ].map(([d, type, c, p, m, st, mt], i) => (
              <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)',
                                    background: i % 2 === 1 ? 'transparent' : 'transparent' }}>
                <td className="mono" style={{ padding: '12px 16px', color: 'var(--text-tertiary)' }}>{d}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{
                    width: 22, height: 22, borderRadius: 6,
                    background: type === 'in' ? 'var(--pos-soft)' : 'var(--neg-soft)',
                    color: type === 'in' ? 'var(--pos)' : 'var(--neg)',
                    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  }}><Icon name={type === 'in' ? 'arrow_in' : 'arrow_out'} size={12} stroke={2.2} /></span>
                </td>
                <td style={{ padding: '12px 16px', color: 'var(--text-primary)', fontWeight: 500 }}>{c}</td>
                <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{p}</td>
                <td style={{ padding: '12px 16px' }}><Badge tone="neutral">{m}</Badge></td>
                <td style={{ padding: '12px 16px' }}><Badge tone={st[0]} dot>{st[1]}</Badge></td>
                <td className="num" style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 500,
                                              color: mt < 0 ? 'var(--neg-fg)'
                                                    : st[1] === 'Anulado' ? 'var(--text-disabled)'
                                                    : 'var(--text-primary)',
                                              textDecoration: st[1] === 'Anulado' ? 'line-through' : 'none' }}>
                  {fmtPYG(mt, { sign: true })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '12px 16px', borderTop: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Mostrando 1–10 de 184</div>
          <Row>
            <Button variant="secondary" size="sm">Anterior</Button>
            <Button variant="secondary" size="sm">Siguiente</Button>
          </Row>
        </div>
      </Card>
    </AppShell>
  </Themed>
);

// ============== SCREEN: REPORTES ==============
const Reportes = ({ theme }) => {
  const trend = [12, 18, 15, 22, 28, 24, 32, 38, 35, 42, 48, 52, 49, 58, 62, 65, 68, 72, 78, 82, 88, 92, 89, 95, 102, 108, 112, 118, 122, 128];

  return (
    <Themed theme={theme}>
      <AppShell
        active="Reportes"
        subtitle="Análisis"
        title="Reportes"
        actions={<>
          <Button variant="secondary" size="sm" leading={<Icon name="calendar" size={14} />}>Mayo 2026</Button>
          <Button variant="secondary" size="sm" leading={<Icon name="download" size={14} />}>Exportar PDF</Button>
        </>}
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 16 }}>
          <KPI label="Facturación mensual" value="Gs. 84.2M" delta="+18%" deltaTone="pos"
               hint="objetivo Gs. 80M · 105%"
               sparkline={<Sparkline data={trend.slice(-12)} color="var(--pos)" />} />
          <KPI label="Margen operativo" value="68.4%" delta="+2.1pp" deltaTone="pos"
               hint="vs. mes anterior 66.3%"
               sparkline={<Sparkline data={[60,62,61,64,66,65,67,68,68,68]} color="var(--accent)" />} />
          <KPI label="Ticket promedio" value="Gs. 142.500" delta="+5.8%" deltaTone="pos"
               hint="por servicio cobrado"
               sparkline={<Sparkline data={[8,9,10,11,10,12,13,12,14,15]} color="var(--text-secondary)" fill={false} />} />
          <KPI label="Servicios totales" value="591" delta="+12.3%" deltaTone="pos"
               hint="19.7 por día"
               sparkline={<Sparkline data={[15,18,16,20,22,21,24,26,28,30]} color="var(--warn)" />} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 16 }}>
          <Card padding="0" title="Tendencia · ingresos del mes"
                action={<Row>
                  <Badge tone="neutral">Mayo</Badge>
                  <Badge tone="neutral">vs. abril</Badge>
                </Row>}>
            <div style={{ padding: '16px 24px 8px' }}>
              <svg viewBox="0 0 720 240" style={{ width: '100%', height: 240, display: 'block' }}>
                {[0, 1, 2, 3].map(i => (
                  <line key={i} x1="40" x2="710" y1={20 + i * 50} y2={20 + i * 50}
                        stroke="var(--border-subtle)" strokeWidth="1" />
                ))}
                {(() => {
                  const max = Math.max(...trend);
                  const points = trend.map((v, i) => [
                    40 + (i / (trend.length - 1)) * 670,
                    220 - (v / max) * 200,
                  ]);
                  const path = 'M' + points.map(p => p.join(',')).join(' L');
                  const area = path + ` L${points[points.length-1][0]},220 L40,220 Z`;
                  return <>
                    <defs>
                      <linearGradient id="g-rep" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.18" />
                        <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
                      </linearGradient>
                    </defs>
                    <path d={area} fill="url(#g-rep)" />
                    <path d={path} stroke="var(--accent)" strokeWidth="2" fill="none" strokeLinecap="round" />
                    <circle cx={points[points.length-1][0]} cy={points[points.length-1][1]} r="4" fill="var(--accent)" stroke="var(--bg-surface)" strokeWidth="2" />
                  </>;
                })()}
                {[1, 8, 15, 22, 30].map((d, i) => (
                  <text key={d} x={40 + ((d-1) / 29) * 670} y="234"
                        fontSize="10" fill="var(--text-tertiary)" textAnchor="middle">{d} may</text>
                ))}
              </svg>
            </div>
          </Card>

          <Card title="Top servicios · mes">
            {[
              ['Lavado completo',  185, 'var(--accent)'],
              ['Lavado básico',    142, 'var(--pos)'],
              ['Encerado premium',  87, 'var(--warn)'],
              ['Aspirado interior', 76, 'var(--text-secondary)'],
              ['Detallado full',    44, 'var(--text-tertiary)'],
            ].map(([n, c, color], i) => {
              const pct = (c / 185) * 100;
              return (
                <div key={n} style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between',
                                fontSize: 13, marginBottom: 6 }}>
                    <span>{n}</span>
                    <span className="num" style={{ color: 'var(--text-secondary)' }}>{c}</span>
                  </div>
                  <div style={{ height: 6, background: 'var(--bg-sunken)', borderRadius: 999, overflow: 'hidden' }}>
                    <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 999 }} />
                  </div>
                </div>
              );
            })}
          </Card>
        </div>

        <Card title="Comparativo por día de la semana">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 12 }}>
            {['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'].map((d, i) => {
              const vals = [3.4, 4.1, 3.8, 4.6, 5.2, 6.4, 4.3];
              const max = 6.4;
              return (
                <div key={d} style={{ textAlign: 'center' }}>
                  <div style={{ height: 110, display: 'flex', alignItems: 'flex-end', justifyContent: 'center' }}>
                    <div style={{
                      width: '60%',
                      height: `${(vals[i] / max) * 100}%`,
                      background: i === 5 ? 'var(--accent)' : 'var(--bg-sunken)',
                      border: i === 5 ? 'none' : '1px solid var(--border-default)',
                      borderRadius: '6px 6px 0 0',
                    }} />
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 8 }}>{d}</div>
                  <div className="num" style={{ fontSize: 12, fontWeight: 500, marginTop: 2,
                                                  color: i === 5 ? 'var(--accent)' : 'var(--text-primary)' }}>
                    Gs. {vals[i]}M
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </AppShell>
    </Themed>
  );
};

// ============== SCREEN: EMPTY STATES ==============
const EmptyStates = ({ theme }) => (
  <Themed theme={theme} style={{ padding: 32, overflowY: 'auto' }}>
    <div style={{ marginBottom: 24 }}>
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>05 · Patterns</div>
      <div style={{ fontSize: 26, fontWeight: 600, letterSpacing: '-0.03em', marginTop: 4 }}>Estados vacíos & feedback</div>
    </div>

    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
      {/* Empty state */}
      <Card padding="0" style={{ minHeight: 320 }}>
        <div style={{ padding: 'var(--s-7) var(--s-5)', textAlign: 'center' }}>
          <div style={{
            width: 56, height: 56, borderRadius: 14,
            background: 'var(--bg-sunken)',
            border: '1px solid var(--border-subtle)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--text-tertiary)',
          }}>
            <Icon name="inbox" size={26} stroke={1.4} />
          </div>
          <div style={{ fontSize: 16, fontWeight: 600, marginTop: 16, letterSpacing: '-0.02em' }}>
            Sin movimientos hoy
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 6, maxWidth: 320, marginInline: 'auto', lineHeight: 1.5 }}>
            Cuando registres un ingreso o egreso aparecerá acá.
          </div>
          <div style={{ marginTop: 20, display: 'flex', gap: 8, justifyContent: 'center' }}>
            <Button variant="primary" size="sm" leading={<Icon name="plus" size={14} />}>Registrar ingreso</Button>
            <Button variant="ghost" size="sm">Ver ayer</Button>
          </div>
        </div>
      </Card>

      {/* Error state */}
      <Card padding="0" style={{ minHeight: 320 }}>
        <div style={{ padding: 'var(--s-7) var(--s-5)', textAlign: 'center' }}>
          <div style={{
            width: 56, height: 56, borderRadius: 14,
            background: 'var(--neg-soft)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--neg)',
          }}>
            <Icon name="x" size={26} stroke={2} />
          </div>
          <div style={{ fontSize: 16, fontWeight: 600, marginTop: 16, letterSpacing: '-0.02em' }}>
            No pudimos sincronizar la caja
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 6, maxWidth: 340, marginInline: 'auto', lineHeight: 1.5 }}>
            Hay 3 movimientos guardados localmente. Revisá tu conexión o reintentá ahora.
          </div>
          <div style={{ marginTop: 20, display: 'flex', gap: 8, justifyContent: 'center' }}>
            <Button variant="primary" size="sm">Reintentar</Button>
            <Button variant="ghost" size="sm">Ver detalles</Button>
          </div>
        </div>
      </Card>

      {/* Success toast */}
      <Card title="Toast · success">
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12,
                      padding: 14, background: 'var(--bg-sunken)',
                      border: '1px solid var(--border-default)',
                      borderRadius: 10,
                      borderLeft: '3px solid var(--pos)' }}>
          <span style={{ width: 24, height: 24, borderRadius: 999, background: 'var(--pos-soft)',
                         color: 'var(--pos)', display: 'inline-flex',
                         alignItems: 'center', justifyContent: 'center', flex: '0 0 auto' }}>
            <Icon name="check" size={14} stroke={2.4} />
          </span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 500 }}>Ingreso registrado</div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>
              Gs. 198.000 · BMW X3 · Encerado premium
            </div>
          </div>
          <Icon name="x" size={14} color="var(--text-tertiary)" />
        </div>
      </Card>

      {/* Confirm dialog (glass) */}
      <Card title="Modal · glass overlay">
        <div style={{ position: 'relative', height: 220, borderRadius: 10, overflow: 'hidden',
                      background: 'linear-gradient(135deg, #1e3a8a 0%, #3B82F6 100%)' }}>
          <div style={{
            position: 'absolute', inset: 'auto 16px 16px 16px',
            padding: 18,
            background: 'var(--bg-overlay)',
            backdropFilter: 'blur(20px) saturate(1.4)',
            WebkitBackdropFilter: 'blur(20px) saturate(1.4)',
            border: '1px solid var(--border-default)',
            borderRadius: 14,
            boxShadow: 'var(--shadow-glass)',
          }}>
            <div style={{ fontSize: 14, fontWeight: 600 }}>¿Anular este movimiento?</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
              Esta acción no se puede deshacer.
            </div>
            <Row style={{ marginTop: 14, justifyContent: 'flex-end', gap: 6 }}>
              <Button variant="ghost" size="sm">Cancelar</Button>
              <Button variant="danger" size="sm">Anular</Button>
            </Row>
          </div>
        </div>
      </Card>
    </div>
  </Themed>
);

Object.assign(window, {
  Dashboard, CajaDiaria, NuevoIngreso, NuevoEgreso, Movimientos, Reportes, EmptyStates,
});
