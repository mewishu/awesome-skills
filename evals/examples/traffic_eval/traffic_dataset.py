"""构造 pydantic_evals Dataset(20 cases + 6 evaluators) + task 函数。

**题面(inputs)+金标(expected_output)都 inline 在本文件 `_CASES` 列表里**,无外部文件依赖。
改金标 = 改下方 `_CASES`(每题一行 helper `_c(...)`),改完 `python run_eval.py` 重跑。

task 从被测报告的同级 .json 读诊断结论码(raw-output/NN.json)。
report path 注入在 inputs['report_md_path'](指向 eval/raw-output/NN.md),对应 .json 在同目录。
"""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path

from pydantic_evals import Case, Dataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from traffic_evaluator import ALL_EVALUATORS


REPORTS_DIR = Path(__file__).resolve().parent / 'raw-output'

def _c(qid, position, dt_start, dt_end, flavor, object_type, obj_id, position_type, problem_type,
       phase2_label, phase3_label, phase4_label):
    """short helper:每行构造一个 Case。phase2/phase3/phase4_label 空 → run_eval 该题该 phase 跳过(不评/不计综合分)。
    """
    return Case(
        name=f'题{qid:02d}',
        inputs={
            'position_name': position,
            'dt_start': dt_start,
            'dt_end': dt_end,
            '诉求': flavor,
            'object_id': obj_id,
            'object_type': object_type,
            'problem_type': problem_type,
            'position_type': position_type,
            'report_md_path': str(REPORTS_DIR / f'{qid:02d}.md'),
        },
        expected_output={
            'phase2_label': phase2_label, 'phase3_label': phase3_label, 'phase4_label': phase4_label,
        },
        metadata={'qid': f'{qid:02d}'},
    )


# 20 题 cases:每行 1 题。字段顺序(用户输入 → 诊断中间产出 → 答案码):(qid, 展位码, dt_start, dt_end, 流量档, obj_type, obj_id, position_type(诊断中间·Phase1), problem_type, phase2_label, phase3_label, phase4_label)
_CASES = [
    _c(1, 'TEST_STRATEGY_VERSION', '2026-08-15', '2026-08-21', '几乎没量 3UV', 'creative', 'C2026010101010101', 'AREC_STRATEGY_REC', '纯量', ['02'], ['召-01', '召-02', '排-02'], ['04', '05']),
    _c(2, 'TEST_STRATEGY_VERSION', '2026-08-15', '2026-08-21', '流量较少 976/9.4%', 'creative', 'C2026010101010102', 'AREC_STRATEGY_REC', '量+效率', ['03'], ['排-01'], ['04']),
    _c(3, 'TEST_MARKET_2025_FEEDS', '2026-08-15', '2026-08-21', '几乎没量 3UV', 'creative', 'C2026010101010103', 'AREC_STRATEGY_REC', '纯量', ['01', '03'], ['召-02', '定-03'], ['04']),
    _c(4, 'TEST_MARKET_2025_FEEDS', '2026-08-15', '2026-08-21', '流量较少 976/20%', 'creative', 'C2026010101010104', 'AREC_STRATEGY_REC', '量+效率', ['02'], ['召-01', '召-02'], ['04']),
    _c(5, 'TEST_MARKET_2025_FEEDS', '2026-08-15', '2026-08-21', '流量较少 576/17%', 'creative', 'C2026010101010105', 'AREC_STRATEGY_REC', '量+效率', ['02'], ['召-01', '召-02'], ['04']),
    _c(6, 'TEST_MARKET_MIND_CARDS_BLOCK', '2026-08-15', '2026-08-21', '几乎没量 3UV', 'creative', 'C2026010101010106', 'STRATEGY_REC', '纯量', ['01', '03', '04'], ['定-02'], ['03']),
    _c(7, 'TEST_MARKET_MIND_CARDS_BLOCK', '2026-08-15', '2026-08-21', '流量较少 204/19.6%', 'creative', 'C2026010101010106', 'STRATEGY_REC', '量+效率', ['01'], ['定-02'], ['03']),
    _c(8, 'TEST_MARKET_MIND_CARDS_BLOCK', '2026-08-15', '2026-08-21', '流量较少 8947/11.3%', 'creative', 'C2026010101010107', 'STRATEGY_REC', '量+效率', ['01'], ['定-01'], ['03']),
    _c(9, 'TEST_BRAND_MIND_TEST', '2026-08-15', '2026-08-21', '几乎没量 9UV/0点击', 'creative', 'C2026010101010108', 'STRATEGY_REC', '纯量', ['02'], ['召-03', '截-01'], ['02']),
    _c(10, 'TEST_BRAND_MIND_TEST', '2026-08-15', '2026-08-21', '流量较少 7026/1.4%', 'creative', 'C2026010101010109', 'STRATEGY_REC', '量+效率', ['02'], ['召-04'], ['03']),
    _c(11, 'TEST_ASSET_USER_PRE_INTERVENTION_STRATEGY', '2026-08-17', '2026-08-18', '流量较少 194UV/2天·诉求"没曝光"', 'creative', 'C2026010101010110', 'STRATEGY_REC', '纯量', ['01', '02'], ['召-04', '定-02'], ['03']),
    _c(12, 'TEST_ASSET_USER_PRE_INTERVENTION_STRATEGY', '2026-08-15', '2026-08-21', '几乎没量 10UV', 'creative', 'C2026010101010111', 'STRATEGY_REC', '纯量', ['01', '02'], ['召-04', '定-02'], ['03']),
    _c(13, 'TEST_HP_DELIVER_BANNER_BLOCK', '2026-08-15', '2026-08-21', '几乎没量 14UV', 'creative', 'C2026010101010112', 'STRATEGY_REC', '纯量', ['01'], ['定-05'], ['02']),
    _c(14, 'TEST_HP_DELIVER_BANNER_BLOCK', '2026-08-15', '2026-08-21', '流量较少 154/39.6%', 'creative', 'C2026010101010113', 'STRATEGY_REC', '量+效率', ['01'], ['定-05'], ['02']),
    _c(15, 'TEST_BLACKCARD_OPTIONAL_TEST', '2026-08-15', '2026-08-21', '几乎没量 103UV', 'creative', 'C2026010101010114', 'STRATEGY_REC', '纯量', ['02'], ['排-02'], ['05']),
    _c(16, 'TEST_BLACKCARD_OPTIONAL_TEST', '2026-08-15', '2026-08-21', '流量较少 1685/2.9%', 'creative', 'C2026010101010115', 'STRATEGY_REC', '量+效率', ['03','04'], ['排-01'], ['04']),
    _c(17, 'TEST_HP_SIMPLE_SHELF_DQLC_PLUS_BLOCK', '2026-08-15', '2026-08-21', '几乎没量 17UV', 'entity', '20230912000230030000000000000', 'STRATEGY_REC', '纯量', ['03','04'], ['排-02'], ['05']),
    _c(18, 'TEST_HP_SIMPLE_SHELF_DQLC_PLUS_BLOCK', '2026-08-15', '2026-08-21', '流量较少 66.6万/0.5%', 'entity', '20230912000230030000000000001', 'STRATEGY_REC', '量+效率', ['01', '03','04'], ['排-01'], ['04']),
    _c(19, 'TEST_HP_SIMPLE_SHELF_HQLC_PLUS_BLOCK', '2026-08-15', '2026-08-21', '几乎没量 64UV', 'entity', '20230912000230030000000000002', 'STRATEGY_REC', '纯量', ['01'], ['定-04'], ['05']),
    _c(20, 'TEST_HP_SIMPLE_SHELF_HQLC_PLUS_BLOCK', '2026-08-15', '2026-08-21', '流量较少 诉求"几乎没量" 2486/0.04%', 'entity', '20230912000230030000000000003', 'STRATEGY_REC', '纯量', ['03','04'], ['排-01'], ['05']),
]


def build_dataset() -> Dataset:
    """20 cases × 6 evaluators。"""
    return Dataset(name='traffic-diagnosis-eval', cases=_CASES, evaluators=ALL_EVALUATORS)


def task_function(inputs: dict) -> dict:
    """从被测报告的同级 .json 读诊断结论码(raw-output/NN.json)。

    JSON 文件含 agent 自填的结构化诊断结论:
      object_type: "creative"/"entity"/"position"
      problem_type: "纯量"/"量+效率"
      position_type: "STRATEGY_REC"/"AREC_STRATEGY_REC"
      phase2_codes: ["02","03"]       (clinic 4 码:01 定向/02 召回/03 排序/04 补全截断)
      phase3_codes: ["召-01",...]     (3 科 × 4 码 + 补全截断 2 码)
      phase4_codes: ["04","05"]       (治疗切口 6 码)
      has_funnel_section: true/false
    """
    md_path = Path((inputs or {}).get('report_md_path', ''))
    json_path = md_path.with_suffix('.json')
    raw = json.loads(json_path.read_text(encoding='utf-8'))
    return {
        'object_type': raw.get('object_type', ''),
        'problem_type': raw.get('problem_type', ''),
        'position_type': raw.get('position_type', ''),
        'phase2_codes': list(raw.get('phase2_codes', []) or []),
        'phase3_codes': list(raw.get('phase3_codes', []) or []),
        'phase4_codes': list(raw.get('phase4_codes', []) or []),
        'has_funnel_section': bool(raw.get('has_funnel_section', False)),
    }


if __name__ == '__main__':
    ds = build_dataset()
    print(f'Dataset {ds.name}: {len(ds.cases)} 题, {len(ALL_EVALUATORS)} evaluators')
    for c in ds.cases:
        e = c.expected_output
        skips = [lbl.split('_')[0] for lbl in ('phase2_label', 'phase3_label', 'phase4_label') if not e.get(lbl)]
        print(f"  题{c.metadata['qid']}: 用户输入=[{c.inputs['position_name']}|{c.inputs['dt_start']}~{c.inputs['dt_end']}|{c.inputs['诉求']}|{c.inputs['object_id']}] | 诊断中间=[link={c.inputs['position_type']} obj={c.inputs['object_type']} pt={c.inputs['problem_type']}] | 答案: ph2={e['phase2_label']} ph3={e['phase3_label']} ph4={e['phase4_label']}"
              + (f' | SKIP:{",".join(skips)}' if skips else ''))
