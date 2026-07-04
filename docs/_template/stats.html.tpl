<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>📊 Stats — Makeup Blowout {{CITY}} {{YEAR}}</title>
  <link href="https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@400;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Josefin Sans',Helvetica,sans-serif;background:#0a0a14;color:#fff;
         min-height:100vh;padding:30px 20px;line-height:1.5}
    .wrap{max-width:1100px;margin:0 auto}
    h1{font-size:clamp(26px,5vw,40px);color:#f5e45b;margin-bottom:6px}
    .sub{color:#aaa;font-size:14px;margin-bottom:6px}
    .pulled{color:#666;font-size:11px;margin-bottom:24px;font-family:ui-monospace,monospace}
    .nodata{background:linear-gradient(135deg,#1a1a2a,#2a1a3a);border:1px solid #3a3a4a;
            border-radius:14px;padding:34px 22px;text-align:center;margin:30px 0}
    .nodata h2{color:#fbbf24;margin-bottom:8px;font-size:22px}
    .nodata p{color:#aaa;font-size:14px}

    /* ====== Registrations section (always-on signup tracker) ====== */
    .reg-wrap{background:linear-gradient(135deg,#15151f,#1a1a2a);border-radius:14px;
              padding:24px;margin-bottom:26px;border:1px solid #2a2a3a}
    .reg-title{color:#22c55e;font-size:18px;font-weight:800;margin-bottom:6px;letter-spacing:-0.3px;
               display:flex;align-items:center;gap:10px;flex-wrap:wrap}
    .reg-sub{color:#888;font-size:12px;margin-bottom:16px;font-family:ui-monospace,monospace}
    .reg-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
              gap:14px;margin-bottom:20px}
    .reg-tile{background:rgba(255,255,255,0.04);border-radius:12px;padding:18px 20px;
              border:1px solid rgba(255,255,255,0.06);position:relative;overflow:hidden}
    .reg-tile.eb{border-left:4px solid #22c55e}
    .reg-tile.sms{border-left:4px solid #f01070}
    .reg-tile .reg-label{color:#aaa;font-size:11px;letter-spacing:1.2px;
                         text-transform:uppercase;font-weight:700;margin-bottom:4px}
    .reg-tile .reg-num{font-size:36px;color:#f5e45b;font-weight:800;line-height:1}
    .reg-tile .reg-extra{color:#bbb;font-size:13px;margin-top:8px}
    .reg-tile .reg-delta{display:inline-block;margin-top:8px;padding:3px 10px;
                         border-radius:14px;font-size:12px;font-weight:700;letter-spacing:0.3px}
    .reg-tile .reg-delta.up{background:rgba(34,197,94,0.18);color:#4ade80}
    .reg-tile .reg-delta.flat{background:rgba(148,163,184,0.18);color:#cbd5e1}
    .reg-tile .reg-delta.down{background:rgba(239,68,68,0.18);color:#fca5a5}
    .reg-tile .reg-cap-wrap{margin-top:10px;height:6px;background:#2a2a3a;
                            border-radius:3px;overflow:hidden}
    .reg-tile .reg-cap-bar{height:100%;background:linear-gradient(90deg,#22c55e,#10b981)}
    .reg-chart-wrap{background:rgba(0,0,0,0.2);border-radius:10px;padding:14px;
                    border:1px solid rgba(255,255,255,0.04);position:relative}
    .reg-chart-title{color:#aaa;font-size:11px;letter-spacing:1.2px;text-transform:uppercase;
                     font-weight:700;margin-bottom:10px;display:flex;justify-content:space-between;
                     align-items:center;flex-wrap:wrap;gap:8px}
    .reg-chart-legend{display:flex;gap:14px;font-size:11px;color:#aaa}
    .reg-chart-legend .dot{display:inline-block;width:8px;height:8px;border-radius:50%;
                           margin-right:4px;vertical-align:middle}
    .reg-chart-legend .dot.eb{background:#22c55e}
    .reg-chart-legend .dot.sms{background:#f01070}
    #reg-chart{width:100%!important;height:260px!important}
    .reg-empty{text-align:center;padding:30px 14px;color:#666;font-size:13px}
    .reg-refresh-pill{font-size:11px;color:#888;background:rgba(255,255,255,0.04);
                      padding:3px 10px;border-radius:10px;letter-spacing:0.3px}

    /* Funnel visualization */
    .funnel-wrap{background:linear-gradient(135deg,#15151f,#1a1a2a);border-radius:14px;
                 padding:24px;margin-bottom:26px;border:1px solid #2a2a3a}
    .funnel-title{color:#f01070;font-size:18px;font-weight:800;margin-bottom:16px;letter-spacing:-0.3px}
    .funnel-stage{margin-bottom:8px;position:relative}
    .funnel-bar-wrap{display:flex;align-items:center;gap:14px;padding:14px 18px;
                     background:rgba(255,255,255,0.04);border-radius:10px;
                     transition:transform 0.15s ease}
    .funnel-bar-wrap:hover{transform:translateX(4px);background:rgba(255,255,255,0.07)}
    .funnel-icon{font-size:24px;min-width:32px;text-align:center}
    .funnel-info{flex:1;display:flex;flex-direction:column;gap:2px}
    .funnel-name{font-size:13px;color:#aaa;text-transform:uppercase;letter-spacing:1px;font-weight:700}
    .funnel-num{font-size:22px;color:#f5e45b;font-weight:800;line-height:1.1}
    .funnel-rate{font-size:11px;color:#22c55e;font-weight:600;margin-top:2px}
    .funnel-rate.weak{color:#fbbf24}
    .funnel-rate.bad{color:#ef4444}
    .funnel-bar{height:32px;background:linear-gradient(90deg,#f01070,#7c3aed);border-radius:6px;
                min-width:60px;position:relative;overflow:hidden}
    .funnel-bar::after{content:"";position:absolute;inset:0;
                       background:linear-gradient(45deg,transparent 30%,rgba(255,255,255,0.15) 50%,transparent 70%);
                       background-size:200% 200%;animation:shimmer 3s infinite}
    @keyframes shimmer { 0% { background-position: -200% 0 } 100% { background-position: 200% 0 } }
    .funnel-arrow{text-align:center;color:#444;font-size:14px;margin:2px 0;font-weight:700}

    /* Stats grid */
    .stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
               gap:14px;margin-bottom:26px}
    .stat-card{background:#1a1a2a;border-left:4px solid #f01070;border-radius:10px;
               padding:18px 20px}
    .stat-card .label{color:#aaa;font-size:12px;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px}
    .stat-card .num{font-size:30px;color:#f5e45b;font-weight:800;line-height:1}
    .stat-card .extra{color:#888;font-size:13px;margin-top:6px}
    .stat-card.success{border-left-color:#22c55e}
    .stat-card.warn{border-left-color:#fbbf24}
    .stat-card.bad{border-left-color:#ef4444}

    /* Forecast */
    .forecast-box{background:linear-gradient(135deg,#15151f,#1f1f2f);
                  border-radius:12px;padding:18px 22px;margin-bottom:18px;
                  border:1px solid #2a2a3a;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
    .forecast-box.on-track{border-color:rgba(34,197,94,0.4);background:linear-gradient(135deg,#0a1f15,#15151f)}
    .forecast-box.behind{border-color:rgba(239,68,68,0.4);background:linear-gradient(135deg,#1f0a0a,#15151f)}
    .forecast-icon{font-size:32px}
    .forecast-text{flex:1;min-width:200px}
    .forecast-text .h{font-size:13px;color:#aaa;text-transform:uppercase;letter-spacing:1px;margin-bottom:2px}
    .forecast-text .v{font-size:18px;font-weight:700;color:#fff}
    .forecast-progress{flex:1;min-width:200px}
    .progress-bar-wrap{height:10px;background:#2a2a3a;border-radius:5px;overflow:hidden;margin-bottom:4px}
    .progress-bar{height:100%;background:linear-gradient(90deg,#22c55e,#10b981);transition:width 0.4s ease}
    .progress-bar.behind{background:linear-gradient(90deg,#ef4444,#dc2626)}
    .progress-label{font-size:11px;color:#888;text-align:right}

    /* ====== Paid Acquisition section (Meta + TikTok side-by-side) ====== */
    .paid-wrap{background:linear-gradient(135deg,#15151f,#1a1a2a);border-radius:14px;
               padding:24px;margin-bottom:26px;border:1px solid #2a2a3a}
    .paid-title{color:#7c3aed;font-size:18px;font-weight:800;margin-bottom:6px;
                letter-spacing:-0.3px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
    .paid-sub{color:#888;font-size:12px;margin-bottom:16px;font-family:ui-monospace,monospace}
    .paid-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
    .platform-card{background:rgba(255,255,255,0.04);border-radius:12px;padding:18px 20px;
                   border:1px solid rgba(255,255,255,0.06);position:relative;overflow:hidden}
    .platform-card.meta{border-left:4px solid #1877f2}
    .platform-card.tiktok{border-left:4px solid #25f4ee}
    .platform-head{display:flex;align-items:center;justify-content:space-between;
                   margin-bottom:14px;gap:8px;flex-wrap:wrap}
    .platform-name{font-size:14px;font-weight:800;color:#fff;letter-spacing:0.5px;
                   text-transform:uppercase;display:flex;align-items:center;gap:8px}
    .platform-pill{font-size:10px;padding:3px 9px;border-radius:10px;letter-spacing:0.5px;
                   font-weight:700;text-transform:uppercase}
    .platform-pill.live{background:rgba(34,197,94,0.2);color:#4ade80}
    .platform-pill.idle{background:rgba(148,163,184,0.15);color:#94a3b8}
    .platform-pill.pending{background:rgba(251,191,36,0.18);color:#fbbf24}
    .platform-spend{font-size:30px;color:#f5e45b;font-weight:800;line-height:1;margin-bottom:4px}
    .platform-spend-sub{color:#888;font-size:11px;margin-bottom:14px}
    .platform-metrics{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:14px}
    .platform-metric{background:rgba(0,0,0,0.25);border-radius:8px;padding:10px 12px}
    .platform-metric .pm-label{color:#888;font-size:10px;letter-spacing:1px;
                                text-transform:uppercase;font-weight:700;margin-bottom:3px}
    .platform-metric .pm-val{color:#fff;font-size:16px;font-weight:700;line-height:1.1}
    .platform-metric .pm-sub{color:#666;font-size:10px;margin-top:2px}
    .platform-topads{margin-top:10px;padding-top:12px;border-top:1px dashed #2a2a3a}
    .platform-topads .ta-title{color:#aaa;font-size:11px;letter-spacing:1px;
                                text-transform:uppercase;font-weight:700;margin-bottom:8px}
    .platform-topads .ta-row{display:flex;align-items:center;
                             padding:8px 0;font-size:12px;color:#cbd5e1;gap:10px;
                             border-bottom:1px solid rgba(255,255,255,0.06)}
    .platform-topads .ta-row:last-child{border-bottom:0}
    .platform-topads .ta-rank{flex-shrink:0;font-size:11px;font-weight:700;color:#7a7a8a;
                              font-family:ui-monospace,monospace;min-width:42px}
    .platform-topads .ta-rank.winner{color:#fbbf24;font-size:13px;min-width:52px;
                                     text-shadow:0 0 8px rgba(251,191,36,0.4)}
    .platform-topads .ta-body{flex:1;min-width:0}
    .platform-topads .ta-name{overflow:hidden;text-overflow:ellipsis;
                              white-space:nowrap;color:#e5e5e5;font-weight:600}
    .platform-topads .ta-camp{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
                              color:#8a8a98;font-size:10.5px;margin-top:1px}
    .platform-topads .ta-nums{text-align:right;flex-shrink:0}
    .platform-topads .ta-num{color:#f5e45b;font-weight:700;
                             font-family:ui-monospace,monospace;font-size:12px}
    .platform-topads .ta-num-sub{color:#7a7a8a;font-size:10px;
                                 font-family:ui-monospace,monospace;margin-top:2px}

    /* ====== Language Breakdown (2026-05-14) ====== */
    .lang-wrap{background:linear-gradient(135deg,#15151f,#1a1a2a);border-radius:14px;
               padding:20px 22px;margin:18px 0;color:#e5e5e5}
    .lang-title{color:#22d3ee;font-size:18px;font-weight:800;margin-bottom:6px;
                display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
    .lang-sub{color:#888;font-size:12px;margin-bottom:16px}
    .lang-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
    .lang-card{background:rgba(34,211,238,0.06);border:1px solid rgba(34,211,238,0.18);
               border-radius:10px;padding:14px}
    .lang-card.winner{border-color:#fbbf24;background:rgba(251,191,36,0.08);
                      box-shadow:0 0 16px rgba(251,191,36,0.15)}
    .lang-flag{font-size:24px;margin-bottom:4px}
    .lang-name{font-size:13px;color:#cbd5e1;font-weight:700;letter-spacing:0.5px;
               text-transform:uppercase;margin-bottom:10px}
    .lang-spend{font-size:24px;font-weight:800;color:#22d3ee}
    .lang-spend-sub{font-size:11px;color:#888;margin-top:2px;margin-bottom:12px}
    .lang-metrics{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px}
    .lang-metric{background:rgba(255,255,255,0.03);padding:6px 8px;border-radius:6px}
    .lang-metric-label{color:#888;font-size:10px;letter-spacing:0.5px;text-transform:uppercase}
    .lang-metric-val{color:#e5e5e5;font-weight:700;font-family:ui-monospace,monospace;font-size:13px}
    .lang-badge{display:inline-block;padding:2px 8px;border-radius:8px;font-size:10px;font-weight:700;
                background:#fbbf24;color:#000}

    /* ====== Form Submissions per channel (2026-05-14) ====== */
    .forms-wrap{background:linear-gradient(135deg,#1a1a26,#1f1f30);border-radius:14px;
                padding:20px 22px;margin:18px 0;color:#e5e5e5}
    .forms-title{color:#34d399;font-size:18px;font-weight:800;margin-bottom:6px;
                 display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
    .forms-sub{color:#888;font-size:12px;margin-bottom:16px}
    .forms-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
    .forms-card{background:rgba(52,211,153,0.06);border:1px solid rgba(52,211,153,0.18);
                border-radius:10px;padding:14px}
    .forms-card.winner{border-color:#fbbf24;background:rgba(251,191,36,0.08)}
    .forms-card.empty{opacity:0.5}
    .forms-platform{font-size:13px;color:#cbd5e1;font-weight:700;letter-spacing:0.5px;
                    text-transform:uppercase;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center}
    .forms-count{font-size:32px;font-weight:800;color:#34d399}
    .forms-cpf{font-size:13px;color:#888;margin-top:4px;font-family:ui-monospace,monospace}
    .forms-cpf strong{color:#34d399;font-size:15px}

    /* ====== Daily chart (2026-05-14 PM) ====== */
    .daily-wrap{background:linear-gradient(135deg,#15151f,#1f1a26);border-radius:14px;
                padding:20px 22px;margin:18px 0;color:#e5e5e5}
    .daily-title{color:#f5e45b;font-size:18px;font-weight:800;margin-bottom:6px}
    .daily-sub{color:#888;font-size:12px;margin-bottom:16px}
    .daily-canvas-wrap{background:rgba(255,255,255,0.02);border-radius:10px;
                       padding:12px;min-height:220px;position:relative}

    /* ====== Engage-through breakdown (2026-05-14 PM) ====== */
    .engage-wrap{background:linear-gradient(135deg,#1a1f26,#1f2530);border-radius:14px;
                 padding:20px 22px;margin:18px 0;color:#e5e5e5}
    .engage-title{color:#a78bfa;font-size:18px;font-weight:800;margin-bottom:6px}
    .engage-sub{color:#888;font-size:12px;margin-bottom:16px}
    .engage-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
    .engage-card{background:rgba(167,139,250,0.06);border:1px solid rgba(167,139,250,0.18);
                 border-radius:10px;padding:14px}
    .engage-card.link{border-color:rgba(34,211,238,0.4)}
    .engage-card.engage{border-color:rgba(251,191,36,0.4)}
    .engage-name{font-size:13px;color:#cbd5e1;font-weight:700;letter-spacing:0.5px;
                 text-transform:uppercase;margin-bottom:8px}
    .engage-count{font-size:28px;font-weight:800;color:#e5e5e5}
    .engage-pct{font-size:13px;color:#888;margin-top:2px}
    .engage-cost{font-size:13px;color:#a78bfa;margin-top:8px;font-family:ui-monospace,monospace}
    .engage-meaning{font-size:11px;color:#666;margin-top:6px;line-height:1.4}

    /* ====== Insight callout boxes (2026-05-14 PM) ====== */
    .insight{margin-top:14px;padding:12px 16px;border-radius:10px;
             background:rgba(245,228,91,0.08);border-left:3px solid #f5e45b;
             color:#e5e5e5;font-size:13px;line-height:1.5}
    .insight.positive{background:rgba(52,211,153,0.08);border-left-color:#34d399}
    .insight.negative{background:rgba(248,113,113,0.08);border-left-color:#f87171}
    .insight.neutral{background:rgba(124,58,237,0.06);border-left-color:#a78bfa}
    .insight-icon{font-size:15px;margin-right:6px}
    .insight strong{color:#f5e45b}
    .insight.positive strong{color:#34d399}
    .insight.negative strong{color:#f87171}
    .insight em{color:#888;font-style:normal;font-size:12px;display:block;margin-top:4px}

    /* ====== Reel Shares — TOP priority (IRON RULE) ====== */
    .shares-wrap{background:linear-gradient(135deg,#1a0f2e,#2a1a3f);border-radius:14px;
                 padding:24px;margin:18px 0;color:#e5e5e5;
                 border:2px solid rgba(236,72,153,0.4)}
    .shares-title{color:#ec4899;font-size:20px;font-weight:800;margin-bottom:6px}
    .shares-sub{color:#888;font-size:12px;margin-bottom:18px}
    .shares-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px}
    .shares-card{background:rgba(236,72,153,0.08);border:1px solid rgba(236,72,153,0.25);
                 border-radius:10px;padding:16px;text-align:center}
    .shares-card.primary{background:rgba(236,72,153,0.15);
                         box-shadow:0 0 24px rgba(236,72,153,0.2)}
    .shares-card-label{color:#cbd5e1;font-size:11px;letter-spacing:1px;
                       text-transform:uppercase;font-weight:700;margin-bottom:8px}
    .shares-card-val{font-size:36px;font-weight:800;color:#ec4899;line-height:1}
    .shares-card.primary .shares-card-val{font-size:48px}
    .shares-card-sub{color:#888;font-size:11px;margin-top:4px}
    .platform-empty{color:#666;font-size:12px;padding:14px 0;text-align:center;
                    border-top:1px dashed #2a2a3a;margin-top:10px}
    .platform-cta{display:block;margin-top:12px;padding:9px 14px;background:rgba(124,58,237,0.15);
                  border:1px solid rgba(124,58,237,0.4);border-radius:8px;color:#c4b5fd;
                  text-align:center;font-size:12px;font-weight:700;text-decoration:none;
                  letter-spacing:0.3px;transition:background 0.15s ease}
    .platform-cta:hover{background:rgba(124,58,237,0.3);color:#fff}
    .platform-cta.meta{background:rgba(24,119,242,0.12);border-color:rgba(24,119,242,0.35);color:#93c5fd}
    .platform-cta.meta:hover{background:rgba(24,119,242,0.28);color:#fff}
    .platform-cta.tiktok{background:rgba(37,244,238,0.10);border-color:rgba(37,244,238,0.3);color:#67e8f9}
    .platform-cta.tiktok:hover{background:rgba(37,244,238,0.24);color:#fff}

    h2{color:#f01070;font-size:20px;margin:26px 0 12px}
    .breakdown{background:#15151f;border-radius:12px;padding:18px 22px;margin-bottom:18px}
    .row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;
         border-bottom:1px dashed #2a2a3a;gap:14px;flex-wrap:wrap}
    .row:last-child{border-bottom:none}
    .row .lbl{font-weight:700;color:#fff;flex:0 0 auto}
    .row .bar-track{flex:1 1 auto;height:8px;background:#2a2a3a;border-radius:4px;overflow:hidden;min-width:120px}
    .row .bar-fill{height:100%;background:linear-gradient(90deg,#f01070,#f5e45b)}
    .row .val{font-weight:700;color:#f5e45b;flex:0 0 auto;text-align:right;min-width:90px}
    .anomaly-box{background:#2a1010;border:1px solid #d97706;border-radius:10px;
                 padding:14px 18px;margin:18px 0}
    .anomaly-box .a-title{color:#fbbf24;font-weight:700;margin-bottom:6px;font-size:14px}
    .anomaly-box .a-item{color:#fde68a;font-size:13px;margin:4px 0}
    .anomaly-box .a-item.critical{color:#fecaca}
    .pixel-hint{background:rgba(124,58,237,0.08);border:1px dashed rgba(124,58,237,0.4);
                border-radius:12px;padding:16px 20px;margin:20px 0;color:#c4b5fd;font-size:13px;
                display:flex;align-items:center;gap:12px}
    .pixel-hint .ico{font-size:22px;flex-shrink:0}
    a.back{color:#aaa;text-decoration:none;font-size:13px}
    a.back:hover{color:#fff}
    @media (max-width: 600px) {
      .stat-grid{grid-template-columns:repeat(2,1fr)}
      .stat-card .num{font-size:24px}
      .reg-tile .reg-num{font-size:28px}
      .breakdown{padding:14px 16px}
      .funnel-num{font-size:18px}
      #reg-chart{height:220px!important}
    }

  /* 2026-06-05 — Budget → Success + optimization + insights */
  .budget-wrap{background:#161a22;border:1px solid #262c38;border-radius:14px;padding:16px;margin:14px 0}
  .budget-title{font-size:17px;font-weight:800;margin-bottom:2px}
  .budget-sub{color:#9aa6b8;font-size:12.5px;margin-bottom:12px}
  .budget-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px}
  .bcard{background:#0f131b;border:1px solid #262c38;border-radius:12px;padding:12px}
  .bcard-t{font-weight:700;font-size:14px;margin-bottom:8px}
  .bcard-rows{display:flex;flex-direction:column;gap:5px;margin-bottom:8px}
  .bcard-row{display:flex;justify-content:space-between;font-size:13px;color:#cdd6e4}
  .bcard-row b{color:#fff}
  .bcard-sub{color:#8a94a6;font-size:11.5px;line-height:1.4}
  .budget-opt,.budget-ins{margin-top:14px;background:#12161e;border:1px solid #262c38;border-radius:12px;padding:12px}
  .opt-head{font-weight:700;font-size:14px;margin-bottom:8px}
  .opt-row{font-size:13px;padding:7px 9px;border-radius:9px;background:#0f131b;margin-bottom:6px;border-right:3px solid #444}
  .opt-row.pause{border-right-color:#ff5d6c}
  .opt-row.scale{border-right-color:#22d39a}
  .opt-why{color:#9aa6b8;font-size:11.5px;margin-top:3px}
  .opt-cta{display:inline-block;margin-top:6px;color:#a98bff;font-size:13px;text-decoration:none}
  .ins-row{font-size:13px;color:#cdd6e4;padding:4px 0;line-height:1.5}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>
<div class="wrap">
  <a class="back" href="https://laurenlev10.github.io/lauren-agent-hub-data/launch/">&larr; Back to launch dashboard</a>
  <h1>📊 Live stats — {{CITY}} {{YEAR}}</h1>
  <div class="sub">{{MONTH}} {{START_DAY}}–{{END_DAY}} · {{HOTEL}}</div>
  <div class="pulled" id="pulled-at">loading…</div>

  <!-- ============================================================
       Registrations section — always renders when SMS/Eventbrite
       data is available, independent of Meta/TikTok pixel.
       ============================================================ -->
  <div id="reg-section" class="reg-wrap" style="display:none;">
    <div class="reg-title">
      <span>📋 הרשמות לאירוע</span>
      <span class="reg-refresh-pill" id="reg-refresh-pill">refreshes every 6 hours</span>
    </div>
    <div class="reg-sub" id="reg-sub">loading…</div>

    <div class="reg-grid">
      <div class="reg-tile eb">
        <div class="reg-label">🎟️ Eventbrite RSVPs</div>
        <div class="reg-num" id="reg-eb-num">—</div>
        <div class="reg-extra" id="reg-eb-extra">— / — capacity</div>
        <div class="reg-cap-wrap"><div class="reg-cap-bar" id="reg-eb-cap" style="width:0%"></div></div>
        <span class="reg-delta flat" id="reg-eb-delta">— today</span>
      </div>
      <div class="reg-tile sms">
        <div class="reg-label">📱 SMS subscribers</div>
        <div class="reg-num" id="reg-sms-num">—</div>
        <div class="reg-extra" id="reg-sms-extra">on year-specific list</div>
        <span class="reg-delta flat" id="reg-sms-delta">— today</span>
      </div>
    </div>

    <div class="reg-chart-wrap">
      <div class="reg-chart-title">
        <span>📈 Growth over time</span>
        <div class="reg-chart-legend">
          <span><span class="dot eb"></span>Eventbrite</span>
          <span><span class="dot sms"></span>SMS subscribers</span>
        </div>
      </div>
      <div id="reg-chart-host"><canvas id="reg-chart"></canvas></div>
      <div class="reg-empty" id="reg-chart-empty" style="display:none;">
        Not enough history yet — chart will populate after the next 6-hour refresh.
      </div>
    </div>
  </div>

  <!-- Pixel hint -->
  <div id="pixel-hint" class="pixel-hint" style="display:none;">
    <span class="ico">🔍</span>
    <div>
      <div style="font-weight:700;color:#ddd6fe;margin-bottom:2px">Pixel data not flowing yet</div>
      <div style="font-size:12px;color:#a78bfa">
        Meta + TikTok + GA4 pixels are installed on the landing pages — once your ads start running,
        the funnel, ROAS and traffic-source breakdowns will appear below automatically.
      </div>
    </div>
  </div>

  <!-- Fallback nothing-yet card -->
  <div id="nodata" class="nodata" style="display:none;">
    <h2>⏳ Data hasn't started flowing yet</h2>
    <p>Pixels are installed on this landing page. Once visitors come, this dashboard fills with real numbers (refreshed every 6 hours).</p>
    <p style="margin-top:10px;font-size:12px;color:#666">If you have a Meta Ads campaign running for this event, expect first data within 24 hours.</p>
  </div>

  <!-- Pixel content (Meta + TikTok + GA4) -->
  <div id="pixel-content" style="display:none;">

    <div id="forecast-wrap"></div>

    <!-- ============================================================
         Paid Acquisition — Meta + TikTok side-by-side.
         Renders empty platform cards (with "API pending" / "No data
         yet" pills) when their respective fetcher returned zero. The
         data shape comes from lauren_stats.py aggregate_for_events:
         ev.meta = { spend, impressions, clicks, ctr, cpc, cost_per_lpv, top_ads[] }
         ev.tiktok = { same shape }
         ============================================================ -->
    <!-- 2026-05-14 PM — Reel Shares (IRON RULE: shares are #1 metric) -->
    <div id="shares-section" class="shares-wrap" style="display:none;">
      <div class="shares-title">📸 שיתופי Reel — ה-#1 metric</div>
      <div class="shares-sub" id="shares-sub">total shares + rate + paid-engagement signal</div>
      <div class="shares-grid" id="shares-grid"></div>
      <div id="shares-insight" class="insight" style="display:none"></div>
    </div>

    <!-- 2026-06-05 — Budget -> Success (realized ROAS + registrations + shares) + per-event optimization + insights -->
    <div id="budget-section" class="budget-wrap" style="display:none;">
      <div class="budget-title">💸 תקציב → הצלחה</div>
      <div class="budget-sub">איך תקציב הפרסום מתורגם להצלחת האירוע — מכירות, הרשמות ושיתופים, כל אחד בנפרד</div>
      <div class="budget-grid" id="budget-grid"></div>
      <div id="budget-opt" class="budget-opt" style="display:none"></div>
      <div id="budget-insights" class="budget-ins" style="display:none"></div>
    </div>

    <div id="paid-section" class="paid-wrap" style="display:none;">
      <div class="paid-title">
        <span>🎯 Paid Acquisition</span>
        <span class="reg-refresh-pill" id="paid-refresh-pill">last 30 days · refreshes every 6h</span>
      </div>
      <div class="paid-sub" id="paid-sub">Total ad spend across platforms</div>
      <div class="paid-grid" id="paid-grid"></div>
      <div id="paid-insight" class="insight" style="display:none"></div>
    </div>

    <!-- 2026-05-14 — Language Breakdown (English vs Spanish vs Other ad spend) -->
    <div id="lang-section" class="lang-wrap" style="display:none;">
      <div class="lang-title">🌐 פיצול שפה — English vs Spanish (Meta)</div>
      <div class="lang-sub" id="lang-sub">איזה ניתוב שפה הביא יותר טלפונים ובכמה</div>
      <div class="lang-grid" id="lang-grid"></div>
      <div id="lang-insight" class="insight" style="display:none"></div>
    </div>

    <!-- 2026-05-14 — Form Submissions per channel (Meta Lead + TikTok SubmitForm) -->
    <div id="forms-section" class="forms-wrap" style="display:none;">
      <div class="forms-title">📝 הרשמות טופס — איזה ערוץ מביא טלפונים</div>
      <div class="forms-sub" id="forms-sub">conversion event per platform · last 30d</div>
      <div class="forms-grid" id="forms-grid"></div>
      <div id="forms-insight" class="insight" style="display:none"></div>
    </div>

    <!-- 2026-05-14 PM — Daily spend chart (line chart with two series) -->
    <div id="daily-section" class="daily-wrap" style="display:none;">
      <div class="daily-title">📈 ספנד יומי × לאנדינג פייג' ויוז</div>
      <div class="daily-sub" id="daily-sub">Meta — last 30 days · spend (yellow) vs LP views (cyan) per day</div>
      <div class="daily-canvas-wrap"><canvas id="daily-chart" height="200"></canvas></div>
      <div id="daily-insight" class="insight" style="display:none"></div>
    </div>

    <!-- 2026-05-14 PM — Engage-through breakdown (Meta's new attribution model) -->
    <div id="engage-section" class="engage-wrap" style="display:none;">
      <div class="engage-title">🔗 פיצול קליקים (Meta New Model — תקף השבוע)</div>
      <div class="engage-sub" id="engage-sub">link clicks vs social engagements (shares/saves/likes) · last 30d</div>
      <div class="engage-grid" id="engage-grid"></div>
      <div id="engage-insight" class="insight" style="display:none"></div>
    </div>

    <div class="funnel-wrap">
      <div class="funnel-title">🎯 The Funnel — from ad to SMS subscriber</div>
      <div id="funnel-stages"></div>
    </div>

    <div class="stat-grid">
      <div class="stat-card"><div class="label">Page views</div><div class="num" id="m-views">—</div><div class="extra" id="x-views">on landing page</div></div>
      <div class="stat-card success"><div class="label">Eventbrite RSVPs</div><div class="num" id="m-eb">—</div><div class="extra" id="x-eb">— / 250 capacity</div></div>
      <div class="stat-card"><div class="label">Form submits</div><div class="num" id="m-conv">—</div><div class="extra" id="x-conv">via landing page form</div></div>
      <div class="stat-card warn"><div class="label">SMS reach <span style="font-size:10px;font-weight:normal;opacity:0.7" id="x-sms-year">{{CITY}} {{YEAR}}</span></div><div class="num" id="m-sms">—</div><div class="extra" id="x-sms">on year-specific list</div></div>
    </div>

    <h2>By source<span style="font-size:12px;color:#888;font-weight:400"> · landing page views</span></h2>
    <div class="breakdown" id="by-source"></div>

    <h2>By language<span style="font-size:12px;color:#888;font-weight:400"> · landing page views</span></h2>
    <div class="breakdown" id="by-lang"></div>

    <h2>By campaign<span style="font-size:12px;color:#888;font-weight:400"> · landing page views</span></h2>
    <div class="breakdown" id="by-campaign"></div>

    <h2>Cost per lead by platform<span style="font-size:12px;color:#888;font-weight:400"> · USD per lead</span></h2>
    <div class="breakdown" id="by-roas"></div>

    <div id="anomaly-wrap"></div>
  </div>
</div>

<script>
(async function(){
  const slug = "{{EVENT_SLUG}}";

  async function fetchJson(path){
    try {
      const r = await fetch(path + "?t=" + Date.now(), { cache: "no-store" });
      return r.ok ? await r.json() : null;
    } catch(e) { return null; }
  }

  const [analytics, regStats, timeseries, optimizer] = await Promise.all([
    fetchJson("/state/event_analytics.json"),
    fetchJson("/state/registration_stats.json"),
    fetchJson("/state/event_timeseries.json"),
    fetchJson("/state/ads_optimizer.json"),
  ]);

  const evPixel = analytics && analytics.events && analytics.events[slug];
  const evAverages = (analytics && analytics._averages) || {};
  const evReg   = regStats  && regStats.events   && regStats.events[slug];
  const evSeries = timeseries && timeseries.events && timeseries.events[slug];

  // Header: most-recent pull
  const latestPull = [
    evReg && evReg.updated_at,
    evPixel && (evPixel.last_pulled || (analytics && analytics._updated_at)),
    timeseries && timeseries._updated_at,
  ].filter(Boolean).sort().pop();
  document.getElementById("pulled-at").textContent =
    latestPull ? ("Last pulled: " + new Date(latestPull).toLocaleString()) : "Last pull: not yet";

  // ============================================================
  // 1) REGISTRATIONS SECTION
  // ============================================================
  function renderDelta(elId, n, suffix){
    const el = document.getElementById(elId);
    if (n === null || n === undefined) { el.textContent = "— today"; return; }
    let cls = "flat", sign = "±";
    if (n > 0)      { cls = "up";   sign = "+"; }
    else if (n < 0) { cls = "down"; sign = "";  }
    el.className = "reg-delta " + cls;
    el.textContent = sign + Number(n).toLocaleString() + " " + (suffix || "today");
  }

  if (evReg) {
    document.getElementById("reg-section").style.display = "block";
    const eb = evReg.eventbrite || {};
    const sm = evReg.sms || {};
    document.getElementById("reg-eb-num").textContent = (eb.registrations || 0).toLocaleString();
    const cap = eb.capacity || 0;
    const fillPct = cap > 0 ? Math.min(100, eb.registrations / cap * 100) : 0;
    document.getElementById("reg-eb-extra").textContent =
      (eb.registrations || 0).toLocaleString() + " / " + (cap || "—") + " capacity" +
      (cap > 0 ? " (" + Math.round(fillPct) + "%)" : "");
    document.getElementById("reg-eb-cap").style.width = fillPct + "%";
    renderDelta("reg-eb-delta", eb.today_delta, "today");

    document.getElementById("reg-sms-num").textContent = (sm.active || sm.total || 0).toLocaleString();
    document.getElementById("reg-sms-extra").textContent =
      sm.list_name ? ('on "' + sm.list_name + '" list') : "on year-specific list";
    renderDelta("reg-sms-delta", sm.daily_delta, "today");

    document.getElementById("reg-sub").textContent =
      "Updated " + (evReg.updated_at ? new Date(evReg.updated_at).toLocaleString() : "—") +
      " · refreshes every 6 hours from Eventbrite + SimpleTexting";

    // Chart
    const snaps = (evSeries && evSeries.snapshots) || [];
    if (snaps.length >= 2 && typeof Chart !== "undefined") {
      const labels = snaps.map(s => {
        const d = new Date(s.ts);
        return d.toLocaleDateString(undefined, { month: "short", day: "numeric" }) +
               " " + d.getHours().toString().padStart(2, "0") + ":00";
      });
      const ebData  = snaps.map(s => s.eb);
      const smsData = snaps.map(s => s.sms);
      const ctx = document.getElementById("reg-chart").getContext("2d");
      new Chart(ctx, {
        type: "line",
        data: {
          labels: labels,
          datasets: [
            { label: "Eventbrite RSVPs", data: ebData,
              borderColor: "#22c55e", backgroundColor: "rgba(34,197,94,0.15)",
              tension: 0.3, yAxisID: "yEb", borderWidth: 2, pointRadius: 3, pointHoverRadius: 5 },
            { label: "SMS subscribers", data: smsData,
              borderColor: "#f01070", backgroundColor: "rgba(240,16,112,0.15)",
              tension: 0.3, yAxisID: "ySms", borderWidth: 2, pointRadius: 3, pointHoverRadius: 5 },
          ]
        },
        options: {
          responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: function(ctx){ return ctx.dataset.label + ": " + ctx.parsed.y.toLocaleString(); } } }
          },
          scales: {
            x:    { ticks: { color: "#888", maxTicksLimit: 8, font: { size: 10 } }, grid: { color: "rgba(255,255,255,0.04)" } },
            yEb:  { position: "left",  ticks: { color: "#22c55e", font: { size: 10 } }, grid: { color: "rgba(255,255,255,0.04)" }, title: { display: true, text: "Eventbrite", color: "#22c55e", font: { size: 10 } } },
            ySms: { position: "right", ticks: { color: "#f01070", font: { size: 10 } }, grid: { display: false },                  title: { display: true, text: "SMS",        color: "#f01070", font: { size: 10 } } },
          }
        }
      });
    } else {
      document.getElementById("reg-chart-host").style.display = "none";
      document.getElementById("reg-chart-empty").style.display = "block";
    }
  }

  // ============================================================
  // 1.5) BUDGET -> SUCCESS + OPTIMIZATION + INSIGHTS (2026-06-05)
  //   Three success lenses, each separate: realized sales/ROAS, registrations,
  //   reel shares — all tied to ad spend. Plus this event's @ads-optimizer recs
  //   and computed budget-improvement insights.
  // ============================================================
  (function renderBudget(){
    if(!evPixel) return;
    var meta = evPixel.meta||{}, tt = evPixel.tiktok||{};
    var spend = (meta.spend||0)+(tt.spend||0);
    if(spend<=0) return;
    var sec=document.getElementById("budget-section"); if(!sec) return;
    var $=function(id){return document.getElementById(id)};
    var f$=function(n){return "$"+Math.round(n||0).toLocaleString()};
    var f2=function(n){return "$"+(Number(n)||0).toFixed(2)};
    var esc=function(x){return (x||"").replace(/[&<>]/g,function(m){return{"&":"&amp;","<":"&lt;",">":"&gt;"}[m]})};
    function card3(title,rows,sub){
      return '<div class="bcard"><div class="bcard-t">'+title+'</div><div class="bcard-rows">'+
        rows.map(function(r){return '<div class="bcard-row"><span>'+r[0]+'</span><b>'+r[1]+'</b></div>'}).join("")+
        '</div><div class="bcard-sub">'+sub+'</div></div>';
    }
    function noteCard(title,txt){return '<div class="bcard"><div class="bcard-t">'+title+'</div><div class="bcard-sub">'+txt+'</div></div>'}
    sec.style.display="block";

    // Ladder A — realized sales / true ROAS
    var rz=evPixel.realized||null, aHtml;
    if(rz && rz.revenue>0){
      var roas=(rz.roas!=null)?rz.roas:(spend>0?rz.revenue/spend:null);
      aHtml=card3("💰 מכירות בפועל (ROAS אמיתי)",
        [["הכנסת אירוע",f$(rz.revenue)],["הוצאת פרסום",f$(spend)],["ROAS",(roas!=null?roas.toFixed(1)+"x":"—")]],
        "כל $1 פרסום ⇒ "+(roas!=null?"$"+roas.toFixed(1)+" מכירות":"—")+" · "+(rz.status==="live"?"חי — מצטבר":"סופי"));
    } else {
      aHtml=noteCard("💰 מכירות בפועל (ROAS)","האירוע עדיין לא התקיים — ROAS אמיתי יחושב אוטומטית אחרי האירוע ממכירות הקופה (OCTOPOS).");
    }
    // Ladder B — registration efficiency
    var sms=evPixel.sms_registered||0, eb=evPixel.eventbrite_registered||0, regs=sms+eb;
    var cpr=regs>0?spend/regs:null;
    var bHtml=card3("📋 הרשמות (עלות להרשמה)",
      [["הרשמות (SMS+EB)",regs.toLocaleString()],["עלות להרשמה",cpr!=null?f2(cpr):"—"],["SMS / EB",sms.toLocaleString()+" / "+eb.toLocaleString()]],
      "כמה עולה להביא נרשם/ת אחד/ת לאירוע");
    // Ladder C — share efficiency (#1 metric)
    var rs=evPixel.reel_shares||{}, shares=rs.total_shares||rs.total||0;
    var spd=(shares>0&&spend>0)?(shares/spend):null;
    var cHtml=card3("📸 שיתופי Reel (הגברה אורגנית)",
      [["שיתופים",shares.toLocaleString()],["שיתופים לכל $100",spd!=null?(spd*100).toFixed(1):"—"],["paid engagement",(rs.paid_engagement||0).toLocaleString()]],
      "המנוף שהופך פרסום בתשלום להגעה אורגנית חינמית");
    $("budget-grid").innerHTML=aHtml+bHtml+cHtml;

    // Per-event optimizer recommendations (read-only; approve in the dashboard)
    var recs=((optimizer&&optimizer.recommendations)||[]).filter(function(r){return r.event_slug===slug});
    if(recs.length){
      var pause=recs.filter(function(r){return r.action==="pause"}), scale=recs.filter(function(r){return r.action==="scale"});
      var rows=recs.map(function(r){
        var icon=r.action==="pause"?"🔻":"🔺";
        var st=(r.status&&r.status!=="open")?(' · <b>'+(r.status==="approved"?"מאושר":r.status==="executed"?"בוצע":"נדחה")+'</b>'):'';
        return '<div class="opt-row '+r.action+'">'+icon+' <b>'+esc(r.ad_name)+'</b> ('+(r.channel==="meta"?"Meta":"TikTok")+') — '+esc(r.suggested_change)+st+
               '<div class="opt-why">'+esc(r.reason)+'</div></div>';
      }).join("");
      $("budget-opt").innerHTML='<div class="opt-head">⚙️ אופטימיזציה לאירוע — '+scale.length+' להגדלה, '+pause.length+' לכיבוי</div>'+rows+
        '<a class="opt-cta" href="https://dashboard.themakeupblowout.com/ads-optimizer/" target="_blank">פתחי ב-@ads-optimizer כדי לאשר בקליק →</a>';
      $("budget-opt").style.display="block";
    }

    // Budget insights (computed)
    var ins=[];
    if(rz && rz.roas!=null){
      if(rz.roas>=3) ins.push("ROAS "+rz.roas.toFixed(1)+"x — מצוין. כל דולר פרסום מחזיר $"+rz.roas.toFixed(1)+" מכירות.");
      else if(rz.roas>0 && rz.roas<1.5) ins.push("ROAS "+rz.roas.toFixed(1)+"x נמוך — הפרסום בקושי מחזיר את עצמו; שווה לבחון קריאייטיב/קהל.");
    }
    var mcpl=evAverages.mean_cpl, mycpl=meta.cost_per_lpv||(meta.landing_page_views?meta.spend/meta.landing_page_views:0);
    if(mcpl && mycpl){
      var d=Math.round((mycpl-mcpl)/mcpl*100);
      if(d<=-15) ins.push("CPL "+f2(mycpl)+" — "+Math.abs(d)+"% מתחת לממוצע שלך ("+f2(mcpl)+"). אירוע יעיל — שווה להזרים אליו עוד תקציב.");
      else if(d>=15) ins.push("CPL "+f2(mycpl)+" — "+d+"% מעל הממוצע ("+f2(mcpl)+"). יקר — בדקי כיבוי מודעות חלשות (ראי אופטימיזציה למעלה).");
    }
    if(meta.spend>0 && tt.spend>0){
      var mc=meta.cost_per_lpv||0, tc=tt.cost_per_lpv||0;
      if(mc>0&&tc>0){
        if(tc<mc*0.7) ins.push("TikTok זול מ-Meta ל-LPV ("+f2(tc)+" מול "+f2(mc)+") — שקלי להעביר תקציב ל-TikTok.");
        else if(mc<tc*0.7) ins.push("Meta זול מ-TikTok ל-LPV ("+f2(mc)+" מול "+f2(tc)+") — שקלי להעביר תקציב ל-Meta.");
      }
    }
    if(spd!=null && spd*100<1) ins.push("שיתופים נמוכים יחסית להוצאה — תזכורת לצוות לבקש מהמשתתפים לשתף את ה-Reel תמורת מתנה.");
    var bl=meta.by_lang||{}, en=bl.english||{}, es=bl.spanish||{};
    if(en.cpl&&es.cpl&&en.lpv>=100&&es.lpv>=100){
      if(en.cpl<es.cpl*0.7) ins.push("English זול ב-"+Math.round((es.cpl-en.cpl)/es.cpl*100)+"% מ-Spanish — הטיית תקציב ל-English תוזיל הרשמות.");
      else if(es.cpl<en.cpl*0.7) ins.push("Spanish זול ב-"+Math.round((en.cpl-es.cpl)/en.cpl*100)+"% מ-English — הטיית תקציב ל-Spanish תוזיל הרשמות.");
    }
    // T-Nd time-aligned benchmark (2026-06-13) — compare this event to where past
    // events stood at the SAME days-before-event, not their full-run totals.
    var ta = evAverages.time_aligned, tn = meta.tnd_now;
    if (ta && ta.by_milestone && tn && (tn.days_to_event != null) && tn.days_to_event >= 0) {
      var stage = (tn.data_through_dte != null) ? tn.data_through_dte : tn.days_to_event;
      var best = null, bestD = 1e9;
      (ta.milestones || []).forEach(function(n){
        if (ta.by_milestone[String(n)]) { var dd = Math.abs(n - stage); if (dd < bestD) { bestD = dd; best = n; } }
      });
      if (best != null && bestD <= 3) {
        var co = ta.by_milestone[String(best)];
        if ((tn.cum_leads||0) >= 5 && (co.cum_cost_per_lead||0) > 0) {
          var myL = tn.cum_cost_per_lead, avL = co.cum_cost_per_lead, dL = Math.round((myL-avL)/avL*100);
          var baseL = "T-"+best+" (יום "+stage+" לפני האירוע): עלות לליד מצטברת "+f2(myL)+" מול "+f2(avL)+" — איפה ש-"+co.n_events+" אירועים קודמים עמדו באותו שלב";
          if (dL <= -12) ins.push(baseL+". מקדימה — "+Math.abs(dL)+"% זול יותר; שווה להזרים תקציב.");
          else if (dL >= 12) ins.push(baseL+". מאחור — "+dL+"% יקר יותר; בדקי קריאייטיב/קהל מול האירועים המוצלחים.");
          else ins.push(baseL+" — בקצב הרגיל (±"+Math.abs(dL)+"%).");
        } else if ((tn.cum_lpv||0) >= 50 && (co.cum_cpl||0) > 0) {
          var myV = tn.cum_cpl, avV = co.cum_cpl, dV = Math.round((myV-avV)/avV*100);
          var baseV = "T-"+best+": CPL מצטבר "+f2(myV)+" מול "+f2(avV)+" (ממוצע "+co.n_events+" אירועים באותו שלב)";
          if (dV <= -12) ins.push(baseV+" — מקדימה ב-"+Math.abs(dV)+"%.");
          else if (dV >= 12) ins.push(baseV+" — מאחור ב-"+dV+"%.");
        }
      }
    }
    if(!ins.length) ins.push("התקציב מתפקד באיזון — אין דגל אדום בולט כרגע. המשיכי לעקוב אחרי ה-CPL וה-ROAS.");
    $("budget-insights").innerHTML='<div class="opt-head">💡 תובנות תקציב — '+slug+'</div>'+ins.map(function(t){return '<div class="ins-row">• '+esc(t)+'</div>'}).join("");
    $("budget-insights").style.display="block";
  })();

  // ============================================================
  // 2) PIXEL SECTION (only when data has actually flowed)
  // ============================================================
  const hasPixelData = evPixel && (
    (evPixel.views && (evPixel.views.total || 0) > 0) ||
    (evPixel.conversions && (evPixel.conversions.total || 0) > 0) ||
    (evPixel.funnel && (evPixel.funnel.page_views || evPixel.funnel.impressions || evPixel.funnel.form_submits)) ||
    // 2026-05-13 fix: Meta/TikTok spend is also pixel data — without this check the
    // page hid \$14,630 of real Meta spend behind the "no data yet" placeholder.
    (evPixel.meta && (evPixel.meta.spend || 0) > 0) ||
    (evPixel.tiktok && (evPixel.tiktok.spend || 0) > 0)
  );

  if (hasPixelData) {
    document.getElementById("pixel-content").style.display = "block";

    const f = evPixel.funnel || {};
    const rates = evPixel.rates || {};
    const stages = [
      { name: "Ad Impressions",   icon: "📣", val: f.impressions       || 0, rate: null },
      { name: "Page Views",        icon: "👀", val: f.page_views        || 0, rateLabel: "CTR",     rate: rates.ctr },
      { name: "Form Submits",      icon: "📝", val: f.form_submits      || 0, rateLabel: "Form %",  rate: rates.form_conversion },
      { name: "Eventbrite RSVPs",  icon: "🎟️", val: f.eventbrite_registered || 0, rateLabel: "Final %", rate: f.page_views ? (f.eventbrite_registered/f.page_views*100) : null }
    ];
    const maxStageVal = Math.max(...stages.map(s => s.val), 1);
    const fc = document.getElementById("funnel-stages");
    fc.innerHTML = "";
    stages.forEach((s, i) => {
      const widthPct = Math.max(8, (s.val / maxStageVal * 100));
      let rateClass = "", rateText = "";
      if (s.rate !== null && s.rate !== undefined && !isNaN(s.rate)) {
        rateText = s.rateLabel + ": " + s.rate.toFixed(1) + "%";
        if (s.rate < 1) rateClass = "bad";
        else if (s.rate < 3) rateClass = "weak";
      }
      const stage = document.createElement("div");
      stage.className = "funnel-stage";
      stage.innerHTML = `
        <div class="funnel-bar-wrap">
          <div class="funnel-icon">${s.icon}</div>
          <div class="funnel-info">
            <div class="funnel-name">${s.name}</div>
            <div class="funnel-num">${s.val.toLocaleString()}</div>
            ${rateText ? `<div class="funnel-rate ${rateClass}">${rateText}</div>` : ""}
          </div>
          <div class="funnel-bar" style="width:${widthPct}%"></div>
        </div>
        ${i < stages.length - 1 ? '<div class="funnel-arrow">▼</div>' : ""}
      `;
      fc.appendChild(stage);
    });

    if (evPixel.forecast) {
      const fw = document.getElementById("forecast-wrap");
      const fcst = evPixel.forecast;
      const target = fcst.target || 250;
      const projected = fcst.projected_total || 0;
      const current = fcst.current || 0;
      const dailyRate = fcst.daily_rate || 0;
      const pct = Math.min(100, projected / target * 100);
      const status = fcst.status === "on_track";
      fw.innerHTML = `
        <div class="forecast-box ${status ? 'on-track' : 'behind'}">
          <div class="forecast-icon">${status ? '🎯' : '⚠️'}</div>
          <div class="forecast-text">
            <div class="h">Eventbrite RSVP forecast</div>
            <div class="v">${status ? 'On track!' : 'Behind target'} — ${fcst.days_remaining} days to event</div>
            <div style="font-size:11px;color:#888;margin-top:4px">Current: ${current} · Rate: ${dailyRate}/day · Projected: ${projected}</div>
          </div>
          <div class="forecast-progress">
            <div class="progress-bar-wrap"><div class="progress-bar ${status ? '' : 'behind'}" style="width:${pct}%"></div></div>
            <div class="progress-label">Projected ${projected.toLocaleString()} / Target ${target.toLocaleString()}${fcst.gap > 0 ? ` (gap: ${fcst.gap})` : ''}</div>
          </div>
        </div>
      `;
    }

    // ============================================================
    // 2a) PAID ACQUISITION (Meta + TikTok side-by-side)
    // ============================================================
    function renderPlatform(p, cfg) {
      // p = data object (evPixel.meta or evPixel.tiktok), cfg = {key, name, icon, adsManagerUrl, pendingLabel}
      const data = p || {};
      const spend = data.spend || 0;
      const imp   = data.impressions || 0;
      const clk   = data.clicks || 0;
      const lpv   = data.landing_page_views || 0;
      const ctr   = data.ctr || (imp ? (clk / imp * 100) : 0);
      const cpc   = data.cpc || (clk ? (spend / clk) : 0);
      const convs = data.conversions || 0;
      const cpl   = data.cost_per_lpv || (lpv ? (spend / lpv) : 0);
      // 2026-06-05 — objective-aware KPI. Lead-optimized campaigns (e.g. TikTok "City Leads")
      // drive form submits, not LP Views, so they legitimately report lpv=0 with real
      // conversions. Detect that and show Form Submits + Cost/Form instead of a misleading
      // "0 LPV / $thousands CPL" (the Cleveland cost_per_lpv=$2356 divide-by-1 artifact).
      const isLeadObj = convs > 0 && lpv <= convs * 0.05;
      const primLabel = isLeadObj ? "Form Submits" : "LP Views";
      const primVal   = isLeadObj ? convs : lpv;
      const primSub   = isLeadObj
        ? ("Cost/Form $" + (convs ? (spend / convs) : 0).toFixed(2))
        : ("CPL $" + (Number(cpl) || 0).toFixed(2));
      const topAds = data.top_ads || [];

      // Status pill: live (spend > 0), idle (no spend, no token), pending (TikTok API not approved)
      let pillCls = "idle", pillText = "no data yet";
      if (spend > 0) { pillCls = "live"; pillText = "live"; }
      else if (cfg.pendingLabel) { pillCls = "pending"; pillText = cfg.pendingLabel; }

      const fmtCurrency = (n) => "$" + (Number(n) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });
      const fmtCurrencyF = (n) => "$" + (Number(n) || 0).toFixed(2);
      const fmtNum = (n) => (Number(n) || 0).toLocaleString();
      const fmtPct = (n) => (Number(n) || 0).toFixed(2) + "%";

      const metricsHtml = `
        <div class="platform-metrics">
          <div class="platform-metric"><div class="pm-label">Impressions</div><div class="pm-val">${fmtNum(imp)}</div></div>
          <div class="platform-metric"><div class="pm-label">Clicks</div><div class="pm-val">${fmtNum(clk)}</div><div class="pm-sub">CTR ${fmtPct(ctr)}</div></div>
          <div class="platform-metric"><div class="pm-label">${primLabel}</div><div class="pm-val">${fmtNum(primVal)}</div><div class="pm-sub">${primSub}</div></div>
          <div class="platform-metric"><div class="pm-label">CPC</div><div class="pm-val">${fmtCurrencyF(cpc)}</div></div>
        </div>`;

      let topAdsHtml = "";
      if (topAds.length > 0) {
        // 2026-05-13 PM — Lauren wants ads ranked by best converter (lowest CPL first).
        // The aggregator already sorts top_ads by CPL asc. Show #1 as 🏆 winner;
        // others numbered #2..#5. Each row shows ad + campaign + spend + LPV + CPL.
        // 2026-06-05 — if NO ad has LPV, this is a Lead-objective platform: the aggregator's
        // CPL-asc sort is meaningless (all CPL=0), so re-rank by CPC asc and show clicks.
        const adsHaveLpv = topAds.some(a => (a.lpv || a.landing_page_views || 0) > 0);
        let ranked = topAds.slice(0, 5);
        if (!adsHaveLpv) {
          ranked = topAds.filter(a => (a.spend || 0) > 0).slice().sort((x, y) => {
            const cx = (x.clicks || 0) ? x.spend / x.clicks : Infinity;
            const cy = (y.clicks || 0) ? y.spend / y.clicks : Infinity;
            return cx - cy;
          }).slice(0, 5);
        }
        const taTitle = adsHaveLpv
          ? 'דירוג מודעות — מהמצליחה ביותר לפחות (CPL)'
          : 'דירוג מודעות — לפי עלות לקליק (קמפיין Leads — אין LPV)';
        topAdsHtml = '<div class="platform-topads"><div class="ta-title">' + taTitle + '</div>' +
          ranked.map((a, i) => {
            const adName = (a.ad_name || "ad #" + (a.ad_id || (i+1))).slice(0, 32);
            const camp = (a.campaign_name || "").slice(0, 36);
            const adLpv = a.lpv || a.landing_page_views || 0;
            const adClk = a.clicks || 0;
            const adCpl = adLpv ? (a.spend / adLpv) : 0;
            const adCpc = adClk ? (a.spend / adClk) : 0;
            const rank = i === 0
              ? '<span class="ta-rank winner">🏆 #1</span>'
              : `<span class="ta-rank">#${i+1}</span>`;
            const campLine = camp ? `<div class="ta-camp">${camp}</div>` : '';
            const numMain = adsHaveLpv ? (fmtCurrencyF(adCpl) + ' CPL') : (fmtCurrencyF(adCpc) + ' CPC');
            const numSub  = adsHaveLpv
              ? (fmtNum(adLpv) + ' LPV · ' + fmtCurrency(a.spend || 0))
              : (fmtNum(adClk) + ' clicks · ' + fmtCurrency(a.spend || 0));
            return `<div class="ta-row">
              ${rank}
              <div class="ta-body">
                <div class="ta-name">${adName}</div>
                ${campLine}
              </div>
              <div class="ta-nums">
                <div class="ta-num">${numMain}</div>
                <div class="ta-num-sub">${numSub}</div>
              </div>
            </div>`;
          }).join("") +
        '</div>';
      } else if (spend > 0) {
        topAdsHtml = '<div class="platform-empty">no per-ad breakdown returned yet</div>';
      }

      return `
        <div class="platform-card ${cfg.key}">
          <div class="platform-head">
            <div class="platform-name">${cfg.icon} ${cfg.name}</div>
            <span class="platform-pill ${pillCls}">${pillText}</span>
          </div>
          <div class="platform-spend">${fmtCurrency(spend)}</div>
          <div class="platform-spend-sub">ad spend · last 30 days</div>
          ${metricsHtml}
          ${topAdsHtml}
          <a class="platform-cta ${cfg.key}" href="${cfg.adsManagerUrl}" target="_blank" rel="noopener">Open in ${cfg.name} Ads Manager →</a>
        </div>`;
    }

    // 2026-05-14 PM — Reel Shares prominent block (Lauren's IRON RULE: shares = #1)
    function renderReelShares(rs) {
      if (!rs || (!rs.total && !rs.total_shares && !rs.paid_engagement && !rs.url)) return;
      const total = rs.total_shares || rs.total || 0;
      const paid = rs.paid_engagement || rs.paid || 0;
      const delta6 = rs.delta_6h || 0;
      const delta24 = rs.delta_24h || 0;
      const rate = rs.rate_per_hour || 0;
      const scans = rs.scan_count || 0;
      const fmtNum = (n) => (Number(n)||0).toLocaleString();
      const fmt$$ = (n) => (Number(n)||0).toFixed(1);

      let html = `
        <div class="shares-card primary">
          <div class="shares-card-label">Total Shares (IG)</div>
          <div class="shares-card-val">${fmtNum(total)}</div>
          <div class="shares-card-sub">${scans ? scans + ' scan' + (scans>1?'s':'') : 'אין סריקה עדיין'}</div>
        </div>`;
      if (delta24) {
        html += `
        <div class="shares-card">
          <div class="shares-card-label">24h Delta</div>
          <div class="shares-card-val">+${fmtNum(delta24)}</div>
          <div class="shares-card-sub">in last 24 hours</div>
        </div>`;
      }
      if (delta6 || rate) {
        html += `
        <div class="shares-card">
          <div class="shares-card-label">Rate</div>
          <div class="shares-card-val">${fmt$$(rate)}<span style="font-size:18px;color:#888"> /hr</span></div>
          <div class="shares-card-sub">+${fmtNum(delta6)} last 6h</div>
        </div>`;
      }
      if (paid) {
        html += `
        <div class="shares-card">
          <div class="shares-card-label">Paid Engagement (Meta)</div>
          <div class="shares-card-val" style="color:#a78bfa">${fmtNum(paid)}</div>
          <div class="shares-card-sub">post-level engagement signal</div>
        </div>`;
      }
      document.getElementById("shares-grid").innerHTML = html;
      document.getElementById("shares-section").style.display = "block";

      // Insight based on rate + total
      const insightEl = document.getElementById("shares-insight");
      if (total === 0 && !rs.url) {
        insightEl.style.display = "none";
      } else if (total === 0) {
        insightEl.className = "insight neutral";
        insightEl.innerHTML = '<span class="insight-icon">💡</span><strong>אין סריקה עדיין.</strong> <em>סריקות אוטומטיות: 12:00 מקומי בכל יום Tue/Wed/Thu שלפני האירוע (baseline) + 12:00/14:00/17:00 ב-Fri/Sat/Sun (בזמן האירוע).</em>';
        insightEl.style.display = "block";
      } else if (rate > 5) {
        insightEl.className = "insight positive";
        insightEl.innerHTML = `<span class="insight-icon">💡</span><strong>קצב חזק — ${fmt$$(rate)} shares/שעה.</strong> <em>אם הקצב נשמר, צפי ${Math.round(rate*24)} shares נוספים ביממה הקרובה.</em>`;
        insightEl.style.display = "block";
      } else if (total > 100) {
        insightEl.className = "insight positive";
        insightEl.innerHTML = `<span class="insight-icon">💡</span><strong>${total} shares — מומנטום חזק.</strong> <em>זה הופך paid spend ל-reach אורגנית בחינם. שווה לדחוף את הצוות באירוע לבקש מאנשים לשתף עוד.</em>`;
        insightEl.style.display = "block";
      } else {
        insightEl.style.display = "none";
      }
    }

        // 2026-05-14 PM — Insight callouts under each section.
    // Picks the most actionable observation for each section based on the data.
    function renderInsights(metaData, ttData, avgs) {
      const fmt$  = (n) => "$" + (Number(n)||0).toFixed(2);
      const fmtPct = (a, b) => b ? Math.round((a-b)/b*100) : 0;
      const show = (id, cls, html) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.className = "insight " + cls;
        el.innerHTML = '<span class="insight-icon">💡</span>' + html;
        el.style.display = "block";
      };

      // --- Paid Acquisition insight ---
      const meta_s = metaData.spend || 0;
      const tt_s   = ttData.spend || 0;
      const meta_leads = metaData.leads || 0;
      const tt_convs = ttData.conversions || 0;
      const totalS = meta_s + tt_s;
      if (totalS > 0) {
        const meta_pct = Math.round(meta_s/totalS*100);
        const tt_pct = Math.round(tt_s/totalS*100);
        if (tt_convs > 0 && meta_leads === 0 && tt_s > 0) {
          show("paid-insight", "neutral",
            `<strong>${meta_pct}% מהתקציב הולך ל-Meta אבל 100% מה-forms מגיעים מ-TikTok.</strong> ` +
            `<em>הפיקסל של Meta חדש מאתמול — נתוני Leads יצטברו בעוד 24-48 שעות. אז יהיה אפשר להחליט אם להזיז תקציב.</em>`);
        } else if (avgs.mean_cpl && metaData.cost_per_lpv) {
          const my = metaData.cost_per_lpv;
          const diff = fmtPct(my, avgs.mean_cpl);
          if (my < avgs.mean_cpl * 0.85) {
            show("paid-insight", "positive",
              `<strong>CPL ${fmt$(my)} = ${Math.abs(diff)}% מתחת לממוצע ${fmt$(avgs.mean_cpl)} שלך</strong> ` +
              `<em>(ממוצע על ${avgs.event_count} אירועים פעילים). אירוע יעיל — שווה להגדיל ספנד.</em>`);
          } else if (my > avgs.mean_cpl * 1.15) {
            show("paid-insight", "negative",
              `<strong>CPL ${fmt$(my)} = ${diff}% מעל הממוצע ${fmt$(avgs.mean_cpl)}.</strong> ` +
              `<em>לבדוק קריאייטיב מיושן או אודיינס מוצה.</em>`);
          } else {
            show("paid-insight", "neutral",
              `<strong>CPL ${fmt$(my)} = ${Math.abs(diff)}% ${diff < 0 ? 'מתחת' : 'מעל'} הממוצע ${fmt$(avgs.mean_cpl)}.</strong>`);
          }
        }
      }

      // --- Language insight ---
      const en = (metaData.by_lang || {}).english || {};
      const es = (metaData.by_lang || {}).spanish || {};
      if (en.cpl && es.cpl && en.lpv >= 100 && es.lpv >= 100) {
        if (en.cpl < es.cpl * 0.7) {
          const pct = Math.round((es.cpl - en.cpl) / es.cpl * 100);
          const saved = Math.round(es.spend * pct/100);
          show("lang-insight", "positive",
            `<strong>English זוול ${pct}% מ-Spanish (${fmt$(en.cpl)} vs ${fmt$(es.cpl)}).</strong> ` +
            `<em>חיסכון פוטנציאלי אם תזיזי תקציב Spanish→English: ~${fmt$(saved)} בחודש.</em>`);
        } else if (es.cpl < en.cpl * 0.7) {
          const pct = Math.round((en.cpl - es.cpl) / en.cpl * 100);
          const saved = Math.round(en.spend * pct/100);
          show("lang-insight", "positive",
            `<strong>Spanish זוול ${pct}% מ-English (${fmt$(es.cpl)} vs ${fmt$(en.cpl)}).</strong> ` +
            `<em>חיסכון פוטנציאלי אם תזיזי תקציב English→Spanish: ~${fmt$(saved)} בחודש.</em>`);
        } else {
          show("lang-insight", "neutral",
            `<strong>English ו-Spanish בעלות דומה (CPL הפרש < 30%).</strong> ` +
            `<em>אין צורך לשנות חלוקה — לחפש קריאייטיב חדש שיוריד עלות בשתי השפות.</em>`);
        }
      }

      // --- Form submissions insight ---
      if (tt_convs >= 5 || meta_leads >= 5) {
        const cpf_m = meta_leads ? meta_s/meta_leads : null;
        const cpf_t = tt_convs ? tt_s/tt_convs : null;
        if (cpf_t && cpf_t < 5) {
          show("forms-insight", "positive",
            `<strong>TikTok CPF ${fmt$(cpf_t)} — מצוין.</strong> ` +
            `<em>פחות מ-$5 לטלפון זה world-class. שווה לחפש איך לשכפל את הקריאייטיב לאירועים אחרים.</em>`);
        } else if (cpf_t && cpf_t > 15) {
          show("forms-insight", "negative",
            `<strong>TikTok CPF ${fmt$(cpf_t)} גבוה.</strong> ` +
            `<em>אודיינס מוצה או קריאייטיב חלש. לבדוק רענון Reel או הקטנת ספנד.</em>`);
        }
      } else if (totalS > 200 && meta_leads === 0 && tt_convs === 0) {
        show("forms-insight", "neutral",
          `<strong>0 הרשמות עדיין.</strong> ` +
          `<em>הפיקסל של Meta הותקן אתמול (13.5) — אם spend > $200 ועדיין 0 leads בעוד 48 שעות, להתריע על תקלת טופס.</em>`);
      }

      // --- Daily chart insight ---
      const ts = metaData.daily_timeseries || [];
      if (ts.length >= 7) {
        const recent = ts.slice(-3).reduce((sum,r)=>sum+r.lpv,0)/3;
        const older  = ts.slice(-7,-4).reduce((sum,r)=>sum+r.lpv,0)/3;
        if (older > 0) {
          const change = (recent - older) / older;
          if (change > 0.2) {
            show("daily-insight", "positive",
              `<strong>LPV עלה ב-${Math.round(change*100)}% ב-3 הימים האחרונים.</strong> ` +
              `<em>מומנטום חזק לקראת האירוע — להמשיך עם הספנד הנוכחי.</em>`);
          } else if (change < -0.2) {
            show("daily-insight", "negative",
              `<strong>LPV ירד ב-${Math.round(-change*100)}% ב-3 הימים האחרונים.</strong> ` +
              `<em>סימן אפשרי לאודיינס מוצה. לרענן קריאייטיב או להוסיף Lookalike.</em>`);
          }
        }
      }

      // --- Engage-through insight ---
      const linkClicks = metaData.link_clicks || 0;
      const engageThrough = metaData.engage_through || 0;
      const totalClicks = metaData.clicks || 0;
      if (totalClicks > 0) {
        const linkPct = Math.round(linkClicks/totalClicks*100);
        if (engageThrough > 1000) {
          show("engage-insight", "positive",
            `<strong>${engageThrough.toLocaleString()} engage-through — אמפליפיקציה חזקה.</strong> ` +
            `<em>אנשים משתפים/שומרים את ה-Reel = reach אורגנית בחינם. ${100-linkPct}% מהקליקים הם כאלה.</em>`);
        } else {
          show("engage-insight", "neutral",
            `<strong>${linkPct}% link clicks vs ${100-linkPct}% engage-through.</strong> ` +
            `<em>במודל החדש של Meta (השבוע), הקליקים שנספרים ב-Ads Manager ירדו ב-${100-linkPct}%. זה ויזואלית בלבד — לא ביצועים פחותים.</em>`);
        }
      }
    }

        // 2026-05-14 PM — Daily spend × LP views chart
    function renderDailyChart(metaData) {
      const ts = metaData.daily_timeseries || [];
      if (!ts.length) return;
      const labels = ts.map(r => r.date.slice(5));  // MM-DD
      const spend = ts.map(r => r.spend || 0);
      const lpv = ts.map(r => r.lpv || 0);
      const leads = ts.map(r => r.leads || 0);
      const canvas = document.getElementById("daily-chart");
      if (!canvas || typeof Chart === "undefined") return;
      // eslint-disable-next-line no-new
      new Chart(canvas, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            { label: 'Spend ($)', data: spend, borderColor: '#f5e45b',
              backgroundColor: 'rgba(245,228,91,0.1)', yAxisID: 'y1', tension: 0.3, fill: true },
            { label: 'LP Views', data: lpv, borderColor: '#22d3ee',
              backgroundColor: 'rgba(34,211,238,0.1)', yAxisID: 'y2', tension: 0.3, fill: true },
            { label: 'Form Submits', data: leads, borderColor: '#34d399',
              backgroundColor: 'rgba(52,211,153,0.1)', yAxisID: 'y2', tension: 0.3, fill: true, hidden: leads.every(v=>!v) },
          ]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { labels: { color: '#cbd5e1' } } },
          scales: {
            x: { ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,0.05)' } },
            y1: { position: 'left', ticks: { color: '#f5e45b', callback: v => '$' + v }, grid: { color: 'rgba(255,255,255,0.05)' } },
            y2: { position: 'right', ticks: { color: '#22d3ee' }, grid: { display: false } },
          }
        }
      });
      document.getElementById("daily-section").style.display = "block";
    }

    // 2026-05-14 PM — Engage-through breakdown (Meta's new attribution model)
    function renderEngageThrough(metaData) {
      const linkClicks = metaData.link_clicks || 0;
      const totalClicks = metaData.clicks || 0;
      const engageThrough = metaData.engage_through || 0;
      const cplc = metaData.cost_per_link_click || 0;
      const spend = metaData.spend || 0;
      if (totalClicks === 0) return;
      const linkPct = totalClicks ? Math.round(linkClicks/totalClicks*100) : 0;
      const engagePct = 100 - linkPct;
      const cpEngage = engageThrough ? (spend/engageThrough) : 0;
      const fmt$ = (n) => "$" + (Number(n)||0).toFixed(2);
      const fmtNum = (n) => (Number(n)||0).toLocaleString();
      document.getElementById("engage-grid").innerHTML = `
        <div class="engage-card link">
          <div class="engage-name">🔗 Link Clicks</div>
          <div class="engage-count">${fmtNum(linkClicks)}</div>
          <div class="engage-pct">${linkPct}% מסה"כ קליקים</div>
          <div class="engage-cost">CPC ${fmt$(cplc)}</div>
          <div class="engage-meaning">קליקים ישירים על ה-CTA. אלה ה"קליקים" שיופיעו בעמודת clicks ב-Ads Manager תחת המודל החדש.</div>
        </div>
        <div class="engage-card engage">
          <div class="engage-name">💛 Engage-through</div>
          <div class="engage-count">${fmtNum(engageThrough)}</div>
          <div class="engage-pct">${engagePct}% מסה"כ קליקים</div>
          <div class="engage-cost">cost per engage ${fmt$(cpEngage)}</div>
          <div class="engage-meaning">likes / shares / saves / כל אינטראקציה לא-לינק. עוברים לעמודת engage-through במודל החדש של Meta.</div>
        </div>`;
      document.getElementById("engage-section").style.display = "block";
      document.getElementById("engage-sub").textContent =
        `${fmtNum(linkClicks)} link clicks + ${fmtNum(engageThrough)} engage-through = ${fmtNum(totalClicks)} total · ${linkPct}/${engagePct}% split`;
    }

        // 2026-05-14 — Language breakdown card renderer
    function renderLangBreakdown(metaData) {
      const lang = metaData.by_lang || {};
      const en = lang.english || {};
      const es = lang.spanish || {};
      const other = lang.other || {};
      const totalSpend = (en.spend||0) + (es.spend||0) + (other.spend||0);
      if (!totalSpend) return;
      // Determine the winner. Lead-optimized Meta campaigns report leads (Form Subs) but
      // no per-language LP Views, so rank by Cost/Lead when LPV is unavailable. 2026-06-12.
      const anyLpv = ((en.lpv||0) + (es.lpv||0) + (other.lpv||0)) > 50;
      const cpfOf = (v) => (v.cost_per_lead!=null ? v.cost_per_lead : ((v.leads||0) ? (v.spend||0)/v.leads : Infinity));
      const candidates = [
        ['english', en], ['spanish', es], ['other', other]
      ].filter(([k,v]) => (v.spend||0) > 20 && (anyLpv ? (v.lpv||0) > 50 : (v.leads||0) >= 10));
      let winnerKey = null;
      if (candidates.length >= 2) {
        candidates.sort((a,b) => anyLpv
          ? ((a[1].cpl||999) - (b[1].cpl||999))
          : (cpfOf(a[1]) - cpfOf(b[1])));
        winnerKey = candidates[0][0];
      }
      const fmt$ = (n) => "$" + (Number(n)||0).toLocaleString(undefined, {maximumFractionDigits:0});
      const fmt$$ = (n) => "$" + (Number(n)||0).toFixed(2);
      const fmtNum = (n) => (Number(n)||0).toLocaleString();
      const card = (key, data, flag, name) => {
        if (!data.spend) return '';
        const winnerBadge = key === winnerKey ? '<span class="lang-badge">🏆 BEST</span>' : '';
        const cls = key === winnerKey ? 'lang-card winner' : 'lang-card';
        const pct = totalSpend ? (data.spend/totalSpend*100).toFixed(0) : 0;
        return `
          <div class="${cls}">
            <div class="lang-flag">${flag}</div>
            <div class="lang-name">${name} ${winnerBadge}</div>
            <div class="lang-spend">${fmt$(data.spend)}</div>
            <div class="lang-spend-sub">${pct}% of Meta spend · ${data.ad_count||0} ads</div>
            <div class="lang-metrics">
              ${anyLpv ? `
              <div class="lang-metric">
                <div class="lang-metric-label">LP Views</div>
                <div class="lang-metric-val">${fmtNum(data.lpv)}</div>
              </div>
              <div class="lang-metric">
                <div class="lang-metric-label">Cost/LPV</div>
                <div class="lang-metric-val">${fmt$$(data.cpl)}</div>
              </div>` : `
              <div class="lang-metric">
                <div class="lang-metric-label">Form Subs</div>
                <div class="lang-metric-val">${fmtNum(data.leads)}</div>
              </div>
              <div class="lang-metric">
                <div class="lang-metric-label">Cost/Form</div>
                <div class="lang-metric-val">${fmt$$(cpfOf(data)===Infinity?0:cpfOf(data))}</div>
              </div>`}
              <div class="lang-metric">
                <div class="lang-metric-label">CTR</div>
                <div class="lang-metric-val">${(data.ctr||0).toFixed(2)}%</div>
              </div>
              <div class="lang-metric">
                <div class="lang-metric-label">CPC</div>
                <div class="lang-metric-val">${fmt$$(data.cpc||0)}</div>
              </div>
            </div>
          </div>`;
      };
      document.getElementById("lang-grid").innerHTML =
        card('english', en, '🇺🇸', 'English') +
        card('spanish', es, '🇲🇽', 'Spanish') +
        card('other',   other, '🎬', 'Reel / Other');
      document.getElementById("lang-section").style.display = "block";
      const winLabel = (k) => k === 'english' ? 'English' : k === 'spanish' ? 'Spanish' : 'Reel/Other';
      const winnerText = winnerKey
        ? ('הזוכה: ' + winLabel(winnerKey) + (anyLpv ? ' עם CPL הזול ביותר' : ' עם העלות הנמוכה ביותר לליד'))
        : 'אין מספיק נתונים להכרזת מנצח';
      document.getElementById("lang-sub").textContent = winnerText;
    }

    // 2026-05-14 — Form Submissions per channel renderer
    function renderFormSubmissions(metaData, ttData) {
      const metaLeads = metaData.leads || 0;
      const metaSpend = metaData.spend || 0;
      const ttConvs = ttData.conversions || 0;
      const ttSpend = ttData.spend || 0;
      const totalForms = metaLeads + ttConvs;
      // Show even when 0 — Lauren wants to know "waiting for data" too
      if (metaSpend === 0 && ttSpend === 0) return;
      const fmtNum = (n) => (Number(n)||0).toLocaleString();
      const fmt$ = (n) => "$" + (Number(n)||0).toFixed(2);
      const metaCpf = metaLeads ? metaSpend/metaLeads : 0;
      const ttCpf = ttConvs ? ttSpend/ttConvs : 0;
      const winner = (metaLeads >= 10 && ttConvs >= 10)
        ? (metaCpf < ttCpf ? 'meta' : 'tt')
        : null;
      const card = (key, count, spend, cpf, name, icon) => {
        const empty = count === 0;
        const winnerCls = key === winner ? ' winner' : '';
        const emptyCls = empty ? ' empty' : '';
        const winnerBadge = key === winner ? '<span class="lang-badge">🏆 BEST</span>' : '';
        return `
          <div class="forms-card${winnerCls}${emptyCls}">
            <div class="forms-platform">
              <span>${icon} ${name}</span>
              ${winnerBadge}
            </div>
            <div class="forms-count">${fmtNum(count)}</div>
            <div class="forms-cpf">
              ${empty
                ? '<em>אין עדיין נתונים — מחכים ל-form submits</em>'
                : 'CPF <strong>' + fmt$(cpf) + '</strong> · על $' + spend.toFixed(0) + ' spend'}
            </div>
          </div>`;
      };
      document.getElementById("forms-grid").innerHTML =
        card('meta', metaLeads, metaSpend, metaCpf, 'Meta (Pixel Lead)', '📘') +
        card('tt',   ttConvs,    ttSpend,   ttCpf,   'TikTok (SubmitForm)', '🎵');
      document.getElementById("forms-section").style.display = "block";
      const sub = totalForms === 0
        ? 'הפיקסל זה עתה הותקן ב-Meta. מחכים לטופס ראשון (~24-48 שעות).'
        : 'סה״כ ' + fmtNum(totalForms) + ' טפסים מולאו · CPF ממוצע ' + (totalForms ? fmt$((metaSpend+ttSpend)/totalForms) : '—');
      document.getElementById("forms-sub").textContent = sub;
    }

    const meta = evPixel.meta || {};
    const tt = evPixel.tiktok || {};
    const totalSpend = (meta.spend || 0) + (tt.spend || 0);
    document.getElementById("paid-section").style.display = "block";
    document.getElementById("paid-sub").textContent =
      "Total spend: $" + totalSpend.toLocaleString(undefined, { maximumFractionDigits: 0 }) +
      " · last 30 days · refreshes every 6 hours";

    // 2026-05-14 — Language Breakdown (Meta by_lang.english/spanish/other)
    renderLangBreakdown(meta);

    // 2026-05-14 — Form Submissions per channel (Meta Lead + TikTok SubmitForm)
    renderFormSubmissions(meta, tt);

    // 2026-05-14 PM — Reel shares (TOP priority per IRON RULE)
    renderReelShares(evPixel.reel_shares || {});

    // 2026-05-14 PM — Daily spend chart + Engage-through cards
    renderDailyChart(meta);
    renderEngageThrough(meta);

    // 2026-05-14 PM — Insight callouts under each section
    renderInsights(meta, tt, evAverages);

    const grid = document.getElementById("paid-grid");
    grid.innerHTML =
      renderPlatform(meta, {
        key: "meta", name: "Meta", icon: "📘",
        adsManagerUrl: "https://adsmanager.facebook.com/adsmanager/manage/campaigns",
      }) +
      renderPlatform(tt, {
        key: "tiktok", name: "TikTok", icon: "🎵",
        adsManagerUrl: "https://ads.tiktok.com/i18n/perf/campaign",
        // While Marketing API access is pending (see CLAUDE.md ticket 2026-05-12),
        // TikTok rows return zero — show that explicitly so Lauren knows why.
        pendingLabel: "API pending",
      });

    const v = evPixel.views || {};
    const c = evPixel.conversions || {};
    const sms = evPixel.sms_registered || (f.sms_registered) || 0;
    document.getElementById("m-views").textContent  = (v.total || (evPixel.funnel&&evPixel.funnel.page_views) || 0).toLocaleString();
    document.getElementById("m-conv").textContent   = (c.total || (evPixel.funnel&&evPixel.funnel.form_submits) || 0).toLocaleString();
    document.getElementById("m-sms").textContent    = sms.toLocaleString();
    const listName = evPixel.sms_list_name || "";
    document.getElementById("x-sms").textContent = listName ? ('on "' + listName + '" list') : "year-specific list";
    const ebReg = evPixel.eventbrite_registered || (f.eventbrite_registered) || 0;
    const ebCap = evPixel.eventbrite_capacity || 250;
    document.getElementById("m-eb").textContent     = ebReg.toLocaleString();
    document.getElementById("x-eb").textContent     = ebReg + " / " + ebCap + " capacity (" + (ebCap > 0 ? Math.round(ebReg/ebCap*100) : 0) + "%)";

    function renderRows(elId, obj, formatter){
      const el = document.getElementById(elId);
      if (!el) return;
      el.innerHTML = "";
      const entries = Object.entries(obj || {}).sort((a,b)=>b[1]-a[1]);
      if (!entries.length) { el.innerHTML = '<div style="color:#666;text-align:center;padding:14px">no data yet</div>'; return; }
      const max = entries[0][1] || 1;
      entries.forEach(([k,vv])=>{
        const pct = (vv/max*100).toFixed(0);
        const row = document.createElement("div");
        row.className = "row";
        row.innerHTML = `<span class="lbl">${k.replace(/_/g," ")}</span>
                         <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>
                         <span class="val">${formatter ? formatter(vv) : vv.toLocaleString()}</span>`;
        el.appendChild(row);
      });
    }
    // GA4 (v.by_*) is empty on every event (service-account gap) — fall back to
    // Meta/TikTok pixel data so these panels aren't blank. (2026-07-04)
    function _nz(o){ return o && Object.keys(o).length; }
    var _bl = meta.by_lang || {};
    var langFb = {};
    ["english","spanish","other"].forEach(function(k){
      var o = _bl[k] || {}, val = o.lpv || o.leads || o.impressions || 0;
      if (val) langFb[k.charAt(0).toUpperCase()+k.slice(1)] = val;
    });
    var srcFb = {};
    if (meta.landing_page_views) srcFb["Meta (paid)"] = meta.landing_page_views;
    if (tt.landing_page_views)   srcFb["TikTok (paid)"] = tt.landing_page_views;
    var campFb = {};
    (meta.top_ads || []).concat(tt.top_ads || []).forEach(function(a){
      var name = a.campaign_name || a.ad_name, val = a.lpv || 0;
      if (name && val) campFb[name] = (campFb[name] || 0) + val;
    });
    var cplFb = {};
    if (meta.spend > 0 && (meta.leads || 0) > 0)       cplFb["Meta"]   = meta.spend / meta.leads;
    if (tt.spend > 0 && (tt.conversions || 0) > 0)     cplFb["TikTok"] = tt.spend / tt.conversions;
    renderRows("by-lang",     _nz(v.by_lang)     ? v.by_lang     : langFb);
    renderRows("by-source",   _nz(v.by_source)   ? v.by_source   : srcFb);
    renderRows("by-campaign", _nz(v.by_campaign) ? v.by_campaign : campFb);
    renderRows("by-roas",     cplFb, function(x){ return "$" + x.toFixed(2); });

    const aw = document.getElementById("anomaly-wrap");
    aw.innerHTML = "";
    if (evPixel.anomalies && evPixel.anomalies.length) {
      const box = document.createElement("div");
      box.className = "anomaly-box";
      box.innerHTML = '<div class="a-title">⚠ Anomalies detected</div>' +
        evPixel.anomalies.map(a => {
          const cls = a.severity === 'critical' ? 'critical' : '';
          return `<div class="a-item ${cls}"><b>${a.metric}:</b> ${a.hypothesis || ''} (observed: ${a.observed})</div>`;
        }).join('');
      aw.appendChild(box);
    }
  }

  // ============================================================
  // 3) Fallback messaging
  // ============================================================
  if (!evReg && !hasPixelData) {
    document.getElementById("nodata").style.display = "block";
  } else if (evReg && !hasPixelData) {
    document.getElementById("pixel-hint").style.display = "flex";
  }
})();
</script>
</body>
</html>
