// ds-components.jsx — Buttons, inputs, badges, cards, table samples, depth.

const Row = ({ children, style }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--s-3)', flexWrap: 'wrap', ...style }}>
    {children}
  </div>
);

const Group = ({ title, children, hint }) => (
  <div style={{ marginBottom: 'var(--s-6)' }}>
    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                  letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 4 }}>{title}</div>
    {hint && <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 12 }}>{hint}</div>}
    <div style={{ marginTop: 12 }}>{children}</div>
  </div>
);

const Components = ({ theme }) => (
  <Themed theme={theme} style={{ padding: 'var(--s-6)', overflowY: 'auto' }}>
    <div style={{ marginBottom: 'var(--s-6)' }}>
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>04 · Components</div>
      <div style={{ fontSize: 26, fontWeight: 600, letterSpacing: '-0.03em', marginTop: 4 }}>UI Kit</div>
      <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 6, maxWidth: 540 }}>
        Componentes equivalentes a controles de Flet · MD3. Cada uno mapea a `ft.FilledButton`, `ft.TextField`, `ft.Card`, etc.
      </div>
    </div>

    <Group title="Buttons" hint="Primary = ft.FilledButton · Secondary = ft.OutlinedButton · Ghost = ft.TextButton · Success = ft.FilledButton (color verde)">
      <Row>
        <Button variant="primary">Registrar ingreso</Button>
        <Button variant="secondary">Cancelar</Button>
        <Button variant="ghost">Ver detalles</Button>
        <Button variant="danger">Anular</Button>
        <Button variant="success" leading={<Icon name="check" size={15} />}>Cerrar caja</Button>
      </Row>
      <Row style={{ marginTop: 12 }}>
        <Button variant="primary" size="sm">SM 30px</Button>
        <Button variant="primary" size="md">MD 36px</Button>
        <Button variant="primary" size="lg">LG 44px</Button>
        <Button variant="primary" leading={<Icon name="plus" size={15} />}>Nuevo movimiento</Button>
        <Button variant="secondary" trailing={<Icon name="chevron_down" size={15} />}>Filtros</Button>
        <Button variant="ghost" leading={<Icon name="download" size={15} />}>Exportar</Button>
      </Row>
    </Group>

    <Group title="Inputs · TextField" hint="Altura 38px · radio 8px · borde focus = accent · monoespaciado para montos">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, maxWidth: 800 }}>
        <Input label="Cliente" placeholder="Nombre o cédula" leading={<Icon name="search" size={15} />} />
        <Input label="Monto" prefix="Gs." placeholder="0" />
        <Input label="Vehículo" placeholder="Patente" hint="Opcional" />
        <Input label="Fecha" placeholder="07/05/2026" trailing={<Icon name="calendar" size={15} />} />
        <Input label="Concepto" placeholder="Detalle del egreso" error hint="Este campo es obligatorio" />
        <Input label="Caja" prefix="Caja" suffix="↑" placeholder="1" />
      </div>
    </Group>

    <Group title="Badges · Status">
      <Row>
        <Badge tone="pos" dot>Cobrado</Badge>
        <Badge tone="warn" dot>Pendiente</Badge>
        <Badge tone="neg" dot>Anulado</Badge>
        <Badge tone="accent" dot>En curso</Badge>
        <Badge tone="neutral">Caja 1</Badge>
        <Badge tone="neutral">Efectivo</Badge>
        <Badge tone="neutral">Transferencia</Badge>
        <Badge tone="accent">Premium</Badge>
      </Row>
    </Group>

    <Group title="Cards · Elevation" hint="Estructura base · ft.Container con border + boxShadow">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
        <KPI label="Ingresos hoy"  value="Gs. 4.280.000" delta="+12.4%" deltaTone="pos"
             hint="vs. ayer Gs. 3.808.000"
             sparkline={<Sparkline data={[3,5,4,7,6,9,8,11,10,12]} color="var(--pos)" />} />
        <KPI label="Egresos hoy"   value="Gs. 685.000"   delta="−4.1%"  deltaTone="neg"
             hint="vs. ayer Gs. 715.000"
             sparkline={<Sparkline data={[5,4,6,3,5,4,3,4,3,2]} color="var(--neg)" />} />
        <KPI label="Servicios"     value="34"            delta="+6"     deltaTone="pos"
             hint="vehículos atendidos"
             sparkline={<Sparkline data={[2,4,3,5,7,6,8,9,11,10]} color="var(--accent)" />} />
      </div>
    </Group>

    <Group title="Table" hint="Hover row · zebra opcional · headers compactos en CAPS · números monoespaciados alineados a la derecha">
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-default)',
                    borderRadius: 'var(--r-lg)', overflow: 'hidden', boxShadow: 'var(--shadow-xs)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: 'var(--bg-sunken)' }}>
              {['Hora', 'Cliente', 'Servicio', 'Método', 'Estado', 'Monto'].map((h, i) => (
                <th key={h} style={{
                  textAlign: i === 5 ? 'right' : 'left',
                  padding: '10px 16px',
                  fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                  letterSpacing: '0.06em', textTransform: 'uppercase',
                  borderBottom: '1px solid var(--border-subtle)',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              ['14:32', 'Cárdenas, M.', 'Lavado completo · Toyota Hilux', 'Efectivo', ['pos','Cobrado'], 85000],
              ['14:18', 'González, R.', 'Aspirado interior · Honda Fit',  'Transferencia', ['accent','En curso'], 45000],
              ['13:55', 'Riveros, A.',  'Encerado premium · BMW X3',      'Tarjeta', ['pos','Cobrado'], 220000],
              ['13:40', 'Martínez, L.', 'Lavado básico · Volkswagen Gol', 'Efectivo', ['warn','Pendiente'], 35000],
            ].map(([h, c, s, m, st, mt], i) => (
              <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <td className="mono" style={{ padding: '12px 16px', color: 'var(--text-tertiary)' }}>{h}</td>
                <td style={{ padding: '12px 16px', color: 'var(--text-primary)', fontWeight: 500 }}>{c}</td>
                <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{s}</td>
                <td style={{ padding: '12px 16px' }}><Badge tone="neutral">{m}</Badge></td>
                <td style={{ padding: '12px 16px' }}><Badge tone={st[0]} dot>{st[1]}</Badge></td>
                <td className="num" style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 500, color: 'var(--text-primary)' }}>
                  {fmtPYG(mt)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Group>

    <Group title="Glass · Modal overlay" hint="Único uso de glassmorphism · solo overlays / dialogs">
      <div style={{ position: 'relative', height: 220, borderRadius: 12, overflow: 'hidden',
                    background: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%)' }}>
        <div style={{
          position: 'absolute', inset: 'auto 24px 24px auto',
          width: 320, padding: 'var(--s-5)',
          background: 'var(--bg-overlay)',
          backdropFilter: 'blur(24px) saturate(1.4)',
          WebkitBackdropFilter: 'blur(24px) saturate(1.4)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--r-xl)',
          boxShadow: 'var(--shadow-glass)',
        }}>
          <div style={{ fontSize: 14, fontWeight: 600 }}>Confirmar cierre de caja</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 6, lineHeight: 1.5 }}>
            Total efectivo: <span className="num" style={{ color: 'var(--text-primary)', fontWeight: 500 }}>Gs. 3.595.000</span>
          </div>
          <Row style={{ marginTop: 16, justifyContent: 'flex-end', gap: 8 }}>
            <Button variant="ghost" size="sm">Cancelar</Button>
            <Button variant="primary" size="sm">Cerrar caja</Button>
          </Row>
        </div>
      </div>
    </Group>
  </Themed>
);

Object.assign(window, { Components });
