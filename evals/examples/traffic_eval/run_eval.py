"""跑评估 → 综合得分(0-100)+ 每 Phase 命中 + 落盘 JSON + HTML(可网页查看)。"""

from __future__ import annotations

import os
import sys
import dataclasses
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from traffic_dataset import build_dataset, task_function
from traffic_evaluator import WEIGHTS_PHASE


def _val(x) -> float:
    """把 evaluator 返值(float/bool/EvaluationReason)归一为 [0,1]。"""
    if x is None:
        return 0.0
    if hasattr(x, 'value'):
        v = x.value
        if isinstance(v, bool):
            return 1.0 if v else 0.0
        if isinstance(v, (int, float)):
            return float(v)
        return 0.0
    if isinstance(x, bool):
        return 1.0 if x else 0.0
    if isinstance(x, (int, float)):
        return float(x)
    return 0.0


def _reason(x):
    return getattr(x, 'reason', None) if hasattr(x, 'reason') else None


def _legend_html() -> str:
    """码义图例(折叠):HTML 里看到的 phase2/3/4 码含义对照,来源 _shared/diagnosis-result-schema.md。"""
    cols2 = lambda rows: ''.join(f'<tr><td class="code">{a}</td><td class="desc">{b}</td></tr>' for a, b in rows)
    cols3 = lambda rows: ''.join(f'<tr><td class="code">{a}</td><td class="tag">{b}</td><td class="desc">{c}</td></tr>' for a, b, c in rows)
    p2 = cols3([
        ('01', '定向科', 'N42/N5/N50/N10/N14 侧(SPI/人群/疲劳/N10规则/时间过滤)'),
        ('02', '召回科', 'N1/N3/N33 供给侧(算法规则/双塔/离线/实时因子)'),
        ('03', '排序科', 'N11/12/13/15-18/22/44 海王星;截断结果转诊到此'),
        ('04', '补全截断科', '仅补全机制真失败(截-01);"排不进被截"不填 04'),
    ])
    p3r = cols3([
        ('召-01', '算法·规则', '品在池规则没召回(GMV低/无行为/标签不配/未配投放)'),
        ('召-02', '算法·双塔', '品在池双塔分低排不进2500 / 向量不近'),
        ('召-03', '供给·离线因子', '品不在池 被离线F-code卡 或 不在白名单'),
        ('召-04', '供给·实时因子', '品不在池 被REAL_TIME F-code卡(BLIND需userId)'),
    ])
    p3d = cols3([
        ('定-01', '人群 crowd', 'N10 crowd/matchCrowdIds / N42 LOCAL_RULE 人群定向'),
        ('定-02', 'SPI 因子', 'N10 UIEW/SPI / N5 SPI(前置/后置)'),
        ('定-03', '疲劳 fatigue', 'N10 fatigue / N42 FATIGUE / N14 hasFatigue'),
        ('定-04', 'N10 其他规则', 'initScore/sceneFeature/itemFeature 未归类(规则非模型)'),
        ('定-05', '时间过滤 TIME_RANGE', 'N42/N5 时段过滤(OUTER/INNER)'),
    ])
    p3s = cols3([
        ('排-01', '打分低/虚高', '模型算法 N11/N12(N11掉点曝光≥1000);查PCOC+goldweight+样本'),
        ('排-02', 'N11 没量(冷启)', 'N11掉点曝光<1000;冷启没跑通(召回没留精排/保量失效)'),
        ('排-03', '干预不生效', '置顶/拉承/保量配了没生效;优先级链逐层归因'),
        ('排-04', '打散异常', '过度(同组只出1条)/不足(同质化刷屏)'),
    ])
    p3t = cols3([
        ('截-01', '动态补全失败', 'N26/C#N26 补全超时 / preSize不足致B进不了候选池(可治)'),
        ('截-02', '转诊到排序科', '截断是结果非病因,真因在排序打分低(回溯优先①)'),
    ])
    p4 = cols3([
        ('01', '确定性直修', '创意下线/实验切流/失效引用/日志不全/冷启三门缺/配置错配;直修+7天观测,不走实验'),
        ('02', '用药·L2 组件级', 'N3/N10/N23/SPI 组件级参数 A/B;补全 preSize·timeout'),
        ('03', '用药·L3 钩子/创意/置顶', '*_blackHook 人群 / BIZ_DECISION_CREATIVE_EXP / 置顶时间窗'),
        ('04', '手术·L4 海王星(须AREC)', 'ctr/cvr/kd 模型;N12 rerank 融合公式;双塔打分'),
        ('05', '手术·L2方案级/L0班车/L1 DRM', 'SOLUTION_CODE 切换/跨展位联合/DRM切流;含 ext_info 冷启参数'),
        ('06', '术后', '推全看 version.status=6(非type=1);回滚回 type=0'),
    ])
    mp = cols2([
        ('召-01 规则/池过严', '02 或 01'), ('召-01 业务未配投放', '01'),
        ('召-02 双塔', '04'), ('召-03 离线因子(被卡)', '02 / 01'),
        ('召-03 不在白名单', '01'), ('召-04 实时因子', '01'),
        ('定-01 人群', '03 / 02(换N42)'), ('定-02 SPI', '02 / 04(加特征)'),
        ('定-03 疲劳', '02'), ('定-04 N10其他规则', '01'), ('定-05 时间过滤', '02'),
        ('排-01 打分低', '04 + PCOC'), ('排-02 N11没量冷启', '05(补coldStart+N13)'),
        ('排-03 干预不生效', '03 / 02'), ('排-04 打散', '05'),
        ('截-01 动态补全失败', '02(preSize·timeout)'),
        ('截-02 转诊排序', '随所转排序码(排-01→04 / 排-02→05)'),
        ('确定性缺陷', '01(直修+7天观测)'),
    ])
    blk = lambda t, body: f'<div class="leg-block"><h3>{t}</h3><table><tbody>{body}</tbody></table></div>'
    return (
        '<details class="legend"><summary>📖 码义图例(点此展开/收起)— 来源 <code>_shared/diagnosis-result-schema.md</code></summary>'
        '<div class="legend-grid">'
        + blk("phase2 进哪科", p2)
        + blk("phase3 根因子 · 召回科(02)", p3r)
        + blk("phase3 · 定向科(01)", p3d)
        + blk("phase3 · 排序科(03)", p3s)
        + blk("phase3 · 补全截断科(04)", p3t)
        + blk("phase4 治疗切口", p4)
        + blk("Step3→Step4 映射", mp)
        + '</div></details>'
    )


def _render_html(out: dict, ts: str) -> str:
    """把评估结果渲染成自包含 HTML(内联 CSS,可直接 file:// 双击打开)。
    顶栏:综合分 + E2E 通过率 + 每 phase 平均命中;主表:逐题命中色块 / E2E 红绿 / 得分 / label→诊断值 / 否决原因 + 码义图例。
    """
    cases = out['cases']
    pp = out['per_phase_avg_hit']
    wp = out['weights_phase']
    comp = out['composite_score']
    comp_color = '#c0392b' if comp < 40 else ('#e67e22' if comp < 70 else '#27ae60')

    def hit_cell(v):
        v = v or 0.0
        r = int(215 * (1 - v)); g = int(160 * v + 40); b = 50
        return f'<td class="hit" style="background:rgb({r},{g},{b})">{v:.2f}</td>'

    rows = []
    for c in cases:
        s = c['scores_per_evaluator']; exp = c['expected_output']; act = c['output_extracted']
        e2e_ok = c['e2e_hit'] >= 0.5
        rows.append(
            f'<tr class="{"fail" if not e2e_ok else "pass"}">'
            f'<td class="qid">{c["qid"]}</td>'
            f'{hit_cell(s.get("Phase2_进哪科", 0))}'
            f'{hit_cell(s.get("Phase3_根因子", 0))}'
            f'{hit_cell(s.get("Phase4_治疗切口", 0))}'
            f'<td class="e2e {"ok" if e2e_ok else "fail"}">{"✓" if e2e_ok else "✗"}</td>'
            f'<td class="score"><b>{c["final_score"]:.1f}</b></td>'
            f'<td class="cmp"><span class="gold">{exp.get("phase2_label")}</span> → <span class="act">{act.get("phase2_codes")}</span></td>'
            f'<td class="cmp"><span class="gold">{exp.get("phase3_label")}</span> → <span class="act">{act.get("phase3_codes")}</span></td>'
            f'<td class="cmp"><span class="gold">{exp.get("phase4_label")}</span> → <span class="act">{act.get("phase4_codes")}</span></td>'
            f'<td class="reason">{c.get("e2e_reason") or ""}</td>'
            f'</tr>'
        )
    stat_cells = ''.join(
        f'<div class="stat"><span class="k">{k}</span><span class="v">{v:.3f}</span></div>'
        for k, v in pp.items()
    )
    css = """*{box-sizing:border-box}
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;margin:20px auto;color:#222;max-width:1600px}
h1{font-size:20px;border-bottom:2px solid #888;padding-bottom:8px}
h1 small{font-size:13px;color:#888;font-weight:normal;margin-left:8px}
.top{display:flex;align-items:center;gap:30px;flex-wrap:wrap;margin:16px 0}
.big{font-size:48px;font-weight:bold;line-height:1}
.big small{font-size:16px;color:#888;font-weight:normal}
.top .meta div{margin:3px 0;color:#555;font-size:14px}
.top .meta b{color:#222}
.phases{display:flex;flex-wrap:wrap;gap:8px}
.stat{background:#f4f4f4;border-radius:6px;padding:6px 12px;font-size:13px;min-width:120px}
.stat .k{color:#666;display:block;font-size:11px;margin-bottom:2px}
.stat .v{font-weight:bold;font-size:15px}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:14px}
th,td{border:1px solid #ddd;padding:6px 8px;text-align:center;vertical-align:middle}
th{background:#333;color:#fff;position:sticky;top:0}
tbody tr:hover{background:#fffbe6}
tr.fail{background:#fff0f0}
tr.fail:hover{background:#ffe0e0}
.hit{font-weight:bold;color:#fff}
.e2e{font-weight:bold}
.e2e.ok{background:#27ae60;color:#fff}
.e2e.fail{background:#c0392b;color:#fff}
.score b{font-size:15px}
.gold{color:#a06000;font-weight:bold}
.act{color:#2255aa}
.cmp{font-family:monospace;font-size:12px;text-align:left}
.reason{color:#c0392b;font-size:12px;text-align:left;max-width:340px}
.qid{font-weight:bold}
.legend summary{cursor:pointer;background:#f4f4f4;padding:8px 12px;border-radius:6px;margin:18px 0 0;font-weight:bold;font-size:14px}
.legend-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:10px}
.leg-block h3{font-size:13px;margin:0 0 6px;color:#333;border-left:3px solid #888;padding-left:8px}
.leg-block table{font-size:12px;width:100%}
.leg-block td{border:1px solid #eee;padding:3px 6px;text-align:left;vertical-align:top}
.leg-block .code{font-family:monospace;font-weight:bold;color:#c0392b;white-space:nowrap}
.leg-block .tag{color:#2255aa;font-weight:bold;white-space:nowrap}
.leg-block .desc{color:#444}
"""
    return (
        '<!doctype html>\n<html lang="zh"><head><meta charset="utf-8">'
        f'<title>traffic-diagnosis eval {ts}</title>\n'
        f'<style>{css}</style></head>\n<body>'
        f'<h1>traffic-diagnosis 综合评估<small>{ts}</small></h1>'
        f'<div class="top">'
        f'<div class="big" style="color:{comp_color}">{comp}<small> /100</small></div>'
        f'<div class="meta">'
        f'<div>E2E 通过率: <b>{out["e2e_pass_rate"]}</b></div>'
        f'<div>题数: {out["num_cases"]}</div>'
        f'<div>权重(Phase0~4): {wp}</div>'
        f'</div>'
        f'<div class="phases">{stat_cells}</div>'
        f'</div>'
        f'<table><thead><tr>'
        f'<th>题</th><th>ph2 命中</th><th>ph3 命中</th><th>ph4 命中</th><th>E2E</th><th>得分</th>'
        f'<th>label ph2 → 诊断值</th><th>label ph3 → 诊断值</th><th>label ph4 → 诊断值</th><th>否决原因</th>'
        f'</tr></thead><tbody>{"".join(rows)}</tbody></table>'
        f'{_legend_html()}'
        f'</body></html>'
    )


_PHASE_KEYS = [
    # (evaluator_name, weight_key, skip_field_name_or_None)
    ('Phase0_分诊意图', 'Phase0', None),
    ('Phase1_链路类型', 'Phase1', None),
    ('Phase2_进哪科', 'Phase2', 'phase2_label'),
    ('Phase3_根因子', 'Phase3', 'phase3_label'),
    ('Phase4_治疗切口', 'Phase4', 'phase4_label'),
]
_E2E_NAME = 'EndToEnd_端到端级联'


def main():
    ds = build_dataset()
    report = ds.evaluate_sync(task_function)

    case_details = []
    for rc in report.cases:
        scores_dict = {}
        if getattr(rc, 'scores', None):
            scores_dict = rc.scores
        elif getattr(rc, 'assertions', None):
            scores_dict = rc.assertions

        hits = {name: _val(v) for name, v in (scores_dict or {}).items()}
        exp = rc.expected_output or {}
        skip_flags = {f: len(exp.get(f, []) or []) == 0 for _, _, f in _PHASE_KEYS if f}

        phase_total = 0.0
        avail_weight = 0.0
        for sname, skey, skip_field in _PHASE_KEYS:
            if skip_field and skip_flags.get(skip_field):
                continue
            phase_total += hits.get(sname, 0.0) * WEIGHTS_PHASE[skey]
            avail_weight += WEIGHTS_PHASE[skey]
        e2e_hit = hits.get(_E2E_NAME, 0.0)

        # 综合(每题):phase_total/avail_weight*100 × 级联系数(否决→0);空金标→0
        if avail_weight > 0:
            raw_score = (phase_total / avail_weight) * 100.0
            score = raw_score * (1.0 if e2e_hit >= 0.5 else 0.0)
        else:
            score = 0.0

        case_details.append({
            'case': rc.name,
            'qid': (rc.metadata or {}).get('qid', rc.name),
            'expected_output': rc.expected_output,
            'output_extracted': rc.output,
            'scores_per_evaluator': hits,
            'phase_total_weighted': phase_total,
            'avail_weight': avail_weight,
            'skip_flags': skip_flags,
            'e2e_hit': e2e_hit,
            'e2e_reason': _reason((scores_dict or {}).get(_E2E_NAME)),
            'final_score': score,
        })

    composite = sum(d['final_score'] for d in case_details) / len(case_details) if case_details else 0.0
    per_phase_avg = {}
    per_phase_n_valid = {}
    for sname, skey, skip_field in _PHASE_KEYS:
        if skip_field:
            n = sum(1 for d in case_details if not d['skip_flags'].get(skip_field))
            s = sum(d['scores_per_evaluator'].get(sname, 0.0) for d in case_details if not d['skip_flags'].get(skip_field))
        else:
            n = len(case_details)
            s = sum(d['scores_per_evaluator'].get(sname, 0.0) for d in case_details)
        per_phase_avg[sname] = s / n if n else 0.0
        per_phase_n_valid[sname] = n
    e2e_pass_rate = sum(1 for d in case_details if d['e2e_hit'] >= 0.5) / len(case_details)

    out_dir = Path(__file__).resolve().parent.parent / 'eval' / 'runs'
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_json = out_dir / f'creative-entity-lowtraffic-20260815_pydc-eval_{ts}.json'

    try:
        agg = report.averages()
        agg_dict = agg.model_dump(mode='json') if hasattr(agg, 'model_dump') else (
            dataclasses.asdict(agg) if dataclasses.is_dataclass(agg) else str(agg)
        )
    except Exception as e:  # noqa
        agg_dict = {'error': str(e)}

    out = {
        'set': 'creative-entity-lowtraffic-20260815',
        'reports_evaluated': 'eval/raw-output/01-20.md',
        'golden': 'inline _CASES in traffic_dataset_20260819.py (hardcode 真金标;Phase2/3/4 skip = expected label 空)',
        'composite_score': round(composite, 2),
        'per_phase_avg_hit': {k: round(v, 3) for k, v in per_phase_avg.items()},
        'per_phase_n_valid': per_phase_n_valid,
        'e2e_pass_rate': round(e2e_pass_rate, 3),
        'weights_phase': WEIGHTS_PHASE,
        'num_cases': len(case_details),
        'cases': case_details,
        'averages_pydc_native': agg_dict,
    }
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    out_html = out_json.with_suffix('.html')
    out_html.write_text(_render_html(out, ts), encoding='utf-8')

    print('=================== traffic-diagnosis 综合评估 ===================')
    print(f'综合得分 (0-100)                 : {composite:.2f}')
    print(f'端到端级联通过率 (E2E pass rate)  : {e2e_pass_rate:.3f}')
    print(f'--- 每 Phase 平均命中 ---')
    for k, v in per_phase_avg.items():
        print(f'  {k:<24}: {v:.3f}')
    print(f'--- 落盘 ---')
    print(f'  JSON: {out_json}')
    print(f'  HTML: {out_html}')
    print('==================================================================')

    return out


if __name__ == '__main__':
    main()
