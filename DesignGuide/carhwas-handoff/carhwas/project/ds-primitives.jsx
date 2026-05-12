// ds-primitives.jsx — atoms shared across DS artboards.
// Every component reads from CSS vars so the same JSX renders correctly
// inside .theme-light and .theme-dark wrappers.

// ============== ICONS ==============
// Stroke-only line icons, 1.5px, 20px viewBox. Lucide-style. Original.
const Icon = ({ name, size = 18, stroke = 1.6, color = 'currentColor' }) => {
  const paths = {
    dashboard: <><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></>,
    cash:      <><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M6 9v6M18 9v6"/></>,
    arrow_in:  <><path d="M12 5v14M5 12l7 7 7-7"/></>,
    arrow_out: <><path d="M12 19V5M5 12l7-7 7 7"/></>,
    list:      <><path d="M8 6h13M8 12h13M8 18h13"/><circle cx="3.5" cy="6" r="1"/><circle cx="3.5" cy="12" r="1"/><circle cx="3.5" cy="18" r="1"/></>,
    chart:     <><path d="M3 3v18h18"/><path d="M7 14l4-4 3 3 5-6"/></>,
    settings:  <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></>,
    search:    <><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></>,
    plus:      <><path d="M12 5v14M5 12h14"/></>,
    bell:      <><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10 21a2 2 0 0 0 4 0"/></>,
    download:  <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></>,
    filter:    <><path d="M3 4h18l-7 9v6l-4-2v-4z"/></>,
    calendar:  <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></>,
    car:       <><path d="M5 17h14M5 17a2 2 0 0 1-2-2v-3l2-5a2 2 0 0 1 2-1h10a2 2 0 0 1 2 1l2 5v3a2 2 0 0 1-2 2"/><circle cx="7.5" cy="17.5" r="1.5"/><circle cx="16.5" cy="17.5" r="1.5"/></>,
    droplet:   <><path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11Z"/></>,
    user:      <><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></>,
    check:     <><path d="m5 12 5 5L20 7"/></>,
    x:         <><path d="m6 6 12 12M18 6 6 18"/></>,
    chevron_down: <><path d="m6 9 6 6 6-6"/></>,
    chevron_right: <><path d="m9 6 6 6-6 6"/></>,
    arrow_right: <><path d="M5 12h14M13 5l7 7-7 7"/></>,
    more:      <><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></>,
    lock:      <><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></>,
    unlock:    <><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 7-2"/></>,
    inbox:     <><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11Z"/></>,
    receipt:   <><path d="M4 2v20l3-2 3 2 3-2 3 2 3-2 1 2V2"/><path d="M8 7h8M8 11h8M8 15h5"/></>,
    sparkle:   <><path d="M12 3v6M12 15v6M3 12h6M15 12h6M5.6 5.6l4.2 4.2M14.2 14.2l4.2 4.2M5.6 18.4l4.2-4.2M14.2 9.8l4.2-4.2"/></>,
    upload:    <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/></>,
    print:     <><path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8" rx="1"/></>,
  };
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24"
         fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round"
         style={{ flex: '0 0 auto', display: 'block' }}>
      {paths[name] || <circle cx="12" cy="12" r="9"/>}
    </svg>
  );
};

// ============== FORMAT ==============
// Paraguay convention: thousands with '.', no decimals.
const fmtPYG = (n, { sign = false } = {}) => {
  const abs = Math.abs(Math.round(n)).toLocaleString('de-DE');
  if (sign && n > 0) return '+ Gs. ' + abs;
  if (sign && n < 0) return '− Gs. ' + abs;
  return 'Gs. ' + abs;
};

// ============== BUTTON ==============
const Button = ({ variant = 'primary', size = 'md', children, leading, trailing, full, style, ...rest }) => {
  const base = {
    fontFamily: 'inherit', fontWeight: 500, letterSpacing: '-0.01em',
    border: '1px solid transparent', cursor: 'pointer',
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    gap: 'var(--s-2)', whiteSpace: 'nowrap',
    transition: 'background .12s ease, border-color .12s ease, box-shadow .12s ease, color .12s ease',
    width: full ? '100%' : 'auto',
  };
  const sizes = {
    sm: { height: 30, padding: '0 12px', fontSize: 13, borderRadius: 'var(--r-md)' },
    md: { height: 36, padding: '0 14px', fontSize: 14, borderRadius: 'var(--r-md)' },
    lg: { height: 44, padding: '0 18px', fontSize: 15, borderRadius: 'var(--r-md)' },
  };
  const variants = {
    primary: {
      background: 'var(--accent)', color: 'var(--accent-fg)',
      boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.15), var(--shadow-xs)',
    },
    secondary: {
      background: 'var(--bg-surface)', color: 'var(--text-primary)',
      borderColor: 'var(--border-default)', boxShadow: 'var(--shadow-xs)',
    },
    ghost: {
      background: 'transparent', color: 'var(--text-secondary)',
    },
    danger: {
      background: 'var(--bg-surface)', color: 'var(--neg-fg)',
      borderColor: 'var(--border-default)',
    },
    success: {
      background: 'var(--pos)', color: '#fff',
      boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.15), var(--shadow-xs)',
    },
  };
  return (
    <button {...rest} style={{ ...base, ...sizes[size], ...variants[variant], ...style }}>
      {leading}{children}{trailing}
    </button>
  );
};

// ============== INPUT ==============
const Input = ({ label, hint, value, placeholder, leading, trailing, style, prefix, suffix, error, ...rest }) => (
  <label style={{ display: 'flex', flexDirection: 'column', gap: 6, ...style }}>
    {label && (
      <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', letterSpacing: 0 }}>
        {label}
      </span>
    )}
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 8,
      height: 38, padding: '0 12px',
      background: 'var(--bg-surface)',
      border: `1px solid ${error ? 'var(--neg)' : 'var(--border-default)'}`,
      borderRadius: 'var(--r-md)',
      boxShadow: error ? 'none' : 'var(--shadow-xs)',
      transition: 'border-color .12s, box-shadow .12s',
    }}>
      {leading && <span style={{ color: 'var(--text-tertiary)', display: 'flex' }}>{leading}</span>}
      {prefix && <span style={{ color: 'var(--text-tertiary)', fontSize: 13 }} className="mono">{prefix}</span>}
      <input
        defaultValue={value}
        placeholder={placeholder}
        {...rest}
        style={{
          flex: 1, border: 0, outline: 0, background: 'transparent',
          fontFamily: 'inherit', fontSize: 14, color: 'var(--text-primary)',
          minWidth: 0, padding: 0,
        }}
      />
      {suffix && <span style={{ color: 'var(--text-tertiary)', fontSize: 13 }} className="mono">{suffix}</span>}
      {trailing && <span style={{ color: 'var(--text-tertiary)', display: 'flex' }}>{trailing}</span>}
    </span>
    {hint && (
      <span style={{ fontSize: 12, color: error ? 'var(--neg-fg)' : 'var(--text-tertiary)' }}>
        {hint}
      </span>
    )}
  </label>
);

// ============== BADGE ==============
const Badge = ({ tone = 'neutral', children, dot, style }) => {
  const tones = {
    neutral: { bg: 'var(--bg-sunken)', fg: 'var(--text-secondary)', dot: 'var(--text-tertiary)' },
    pos:     { bg: 'var(--pos-soft)', fg: 'var(--pos-fg)',         dot: 'var(--pos)' },
    neg:     { bg: 'var(--neg-soft)', fg: 'var(--neg-fg)',         dot: 'var(--neg)' },
    warn:    { bg: 'var(--warn-soft)',fg: 'var(--warn-fg)',        dot: 'var(--warn)' },
    accent:  { bg: 'var(--accent-soft)', fg: 'var(--accent)',      dot: 'var(--accent)' },
  };
  const t = tones[tone];
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      height: 22, padding: '0 8px',
      borderRadius: 'var(--r-pill)',
      background: t.bg, color: t.fg,
      fontSize: 11, fontWeight: 500, letterSpacing: 0,
      ...style,
    }}>
      {dot && <span style={{ width: 6, height: 6, borderRadius: 999, background: t.dot }} />}
      {children}
    </span>
  );
};

// ============== CARD ==============
const Card = ({ title, action, padding = 'var(--s-5)', children, style, bodyStyle }) => (
  <div style={{
    background: 'var(--bg-surface)',
    border: '1px solid var(--border-default)',
    borderRadius: 'var(--r-lg)',
    boxShadow: 'var(--shadow-xs)',
    ...style,
  }}>
    {(title || action) && (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: 'var(--s-4) var(--s-5)',
        borderBottom: '1px solid var(--border-subtle)',
      }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{title}</div>
        <div>{action}</div>
      </div>
    )}
    <div style={{ padding, ...bodyStyle }}>{children}</div>
  </div>
);

// ============== KPI CARD ==============
const KPI = ({ label, value, delta, deltaTone = 'pos', sparkline, hint }) => (
  <div style={{
    background: 'var(--bg-surface)',
    border: '1px solid var(--border-default)',
    borderRadius: 'var(--r-lg)',
    padding: 'var(--s-5)',
    boxShadow: 'var(--shadow-xs)',
    display: 'flex', flexDirection: 'column', gap: 'var(--s-3)',
  }}>
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', letterSpacing: 0 }}>{label}</div>
      {delta && <Badge tone={deltaTone} dot>{delta}</Badge>}
    </div>
    <div className="num" style={{ fontSize: 28, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.03em', lineHeight: 1.1 }}>
      {value}
    </div>
    <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 'var(--s-3)' }}>
      <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{hint}</div>
      {sparkline}
    </div>
  </div>
);

// ============== SPARKLINE ==============
const Sparkline = ({ data, color = 'var(--accent)', width = 80, height = 28, fill = true }) => {
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return [x, y];
  });
  const path = 'M' + points.map(p => p.join(',')).join(' L');
  const area = path + ` L${width},${height} L0,${height} Z`;
  const id = 'sg-' + Math.random().toString(36).slice(2, 8);
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ flex: '0 0 auto' }}>
      {fill && (
        <>
          <defs>
            <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity="0.2" />
              <stop offset="100%" stopColor={color} stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d={area} fill={`url(#${id})`} />
        </>
      )}
      <path d={path} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};

// ============== SECTION HEADER (in-screen) ==============
const SectionH = ({ title, subtitle, action }) => (
  <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 'var(--s-4)' }}>
    <div>
      <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-tertiary)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>{subtitle}</div>
      <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginTop: 2 }}>{title}</div>
    </div>
    {action}
  </div>
);

// ============== LOGO ==============
const Logo = ({ size = 22, color = 'var(--text-primary)' }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <rect x="2" y="2" width="20" height="20" rx="6" fill={color} />
      <path d="M7 16c1.5-2 3-2 5 0s3.5 2 5 0" stroke="var(--bg-surface)" strokeWidth="1.8" strokeLinecap="round" fill="none" />
      <circle cx="9" cy="9" r="1.4" fill="var(--bg-surface)" />
      <circle cx="15" cy="9" r="1.4" fill="var(--bg-surface)" />
    </svg>
    <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>Mukusoft</span>
  </div>
);

// ============== ARTBOARD WRAPPER ==============
// Wraps artboard contents so they pick up the right CSS-var theme.
const Themed = ({ theme = 'light', children, style }) => (
  <div className={`theme-${theme}`} style={{
    width: '100%', height: '100%',
    background: 'var(--bg-app)',
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-sans)',
    fontSize: 14,
    overflow: 'hidden',
    ...style,
  }}>
    {children}
  </div>
);

Object.assign(window, {
  Icon, Button, Input, Badge, Card, KPI, Sparkline, SectionH, Logo, Themed, fmtPYG,
});
