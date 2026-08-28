"""6 个节点级 + 端到端 Evaluator,继承 pydantic_evals.evaluators.Evaluator。

输出/金标 dict 约定:
  output (agent 自填 JSON):   {object_type, problem_type, position_type, phase2_codes, phase3_codes, phase4_codes, has_funnel_section}
  inputs (题面):            {object_type, problem_type, position_type, ...} —— Phase0/1 期望取 inputs 对应字段(原始值,无 01/02 映射),直接 vs output['object_type'/'problem_type'/'position_type']
  expected (golden):        {phase2_label, phase3_label, phase4_label}            —— Phase2/3/4 期望码(label = 金标;Phase0/1 期望不存 expected_output)

权重 B(HTML 表单 W):Phase0=8 / Phase1=12 / Phase2=18 / Phase3=28 / Phase4=34,合计 100。
Phase2/3/4 多选;补全截断去独立码(Phase2=04 → Phase3 走排序科 01-04),由 extractor 和 expected_output 集合各自归一,evaluator 只做集合比对。
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.evaluators.evaluator import EvaluationReason


WEIGHTS_PHASE: dict[str, int] = {
    'Phase0': 8,
    'Phase1': 12,
    'Phase2': 18,
    'Phase3': 28,
    'Phase4': 34,
}


def _f1_set(expected: list[str] | set[str] | None, actual: list[str] | set[str] | None) -> float:
    """多选集合的 F1(命中=交集大小;精确率=交/act;召回率=交/exp)。"""
    exp = set(expected or [])
    act = set(actual or [])
    if not exp and not act:
        return 1.0  # 两边都空,视为匹配(无期望无实际)
    if not exp or not act:
        return 0.0  # 单边空=错
    inter = len(exp & act)
    if inter == 0:
        return 0.0
    return 2 * inter / (len(exp) + len(act))


def _get(d: dict | None, key: str, default=None):
    return (d or {}).get(key, default)


@dataclass(repr=False)
class Phase0Evaluator(Evaluator[object, object, object]):
    """分诊意图:object_type + problem_type 两维单选,命中率=(od_hit+pt_hit)/2。"""

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> float:
        out = ctx.output or {}
        inputs = ctx.inputs or {}
        # Phase0 期望 = inputs 中 object_type/problem_type 的原始值(creative/entity/纯量/量+效率),直接比对 output['object_type'/'problem_type']
        od_hit = _get(out, 'object_type') == inputs.get('object_type')
        pt_hit = _get(out, 'problem_type') == inputs.get('problem_type')
        return (float(od_hit) + float(pt_hit)) / 2.0

    def get_default_evaluation_name(self) -> str:
        return 'Phase0_分诊意图'


@dataclass(repr=False)
class Phase1Evaluator(Evaluator[object, object, object]):
    """链路类型单选:STRATEGY_REC / AREC_STRATEGY_REC。"""

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> float:
        out = ctx.output or {}
        inputs = ctx.inputs or {}
        # Phase1 期望 = inputs 中 position_type 的原始值(STRATEGY_REC/AREC_STRATEGY_REC),直接比对 output['position_type']
        return 1.0 if _get(out, 'position_type') == inputs.get('position_type') else 0.0

    def get_default_evaluation_name(self) -> str:
        return 'Phase1_链路类型'


@dataclass(repr=False)
class Phase2Evaluator(Evaluator[object, object, object]):
    """进哪科多选(01 定向 / 02 召回 / 03 排序 / 04 补全截断);集合 F1。"""

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> float:
        out, exp = ctx.output or {}, ctx.expected_output or {}
        return _f1_set(_get(exp, 'phase2_label'), _get(out, 'phase2_codes'))

    def get_default_evaluation_name(self) -> str:
        return 'Phase2_进哪科'


@dataclass(repr=False)
class Phase3Evaluator(Evaluator[object, object, object]):
    """根因子多选(召回 4 / 定向 4 / 排序 4);集合 F1。"""

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> float:
        out, exp = ctx.output or {}, ctx.expected_output or {}
        return _f1_set(_get(exp, 'phase3_label'), _get(out, 'phase3_codes'))

    def get_default_evaluation_name(self) -> str:
        return 'Phase3_根因子'


@dataclass(repr=False)
class Phase4Evaluator(Evaluator[object, object, object]):
    """治疗切口多选(01-06);集合 F1。"""

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> float:
        out, exp = ctx.output or {}, ctx.expected_output or {}
        return _f1_set(_get(exp, 'phase4_label'), _get(out, 'phase4_codes'))

    def get_default_evaluation_name(self) -> str:
        return 'Phase4_治疗切口'


@dataclass(repr=False)
class EndToEndEvaluator(Evaluator[object, object, object]):
    """端到端级联判档。返回 1.0(全过)或 EvaluationReason(value=0.0, reason)。

    降级口径(无 trajectory 跨进程 span,本版用报告内结构性信号):
      1. Phase3 错根因层(模式 D):被 抽 s3 与 expected s3 零交集 → 否决
      2. Phase4 不映射 Phase3(模式映射):被 抽 s4 与 expected s4 零交集 → 否决
      3. 缺创意漏斗硬出(模式 B)/蒙做(模式 A/C):报告无漏斗体检段但 Phase2/3 已出结论 → 否决
      全过 → 1.0
    """

    def evaluate(self, ctx: EvaluatorContext[object, object, object]):
        out, exp = ctx.output or {}, ctx.expected_output or {}
        reasons: list[str] = []

        # 1. Phase3 错根因层
        exp_s3 = set(_get(exp, 'phase3_label') or [])
        act_s3 = set(_get(out, 'phase3_codes') or [])
        if exp_s3 and not (exp_s3 & act_s3):
            reasons.append('Phase3 错根因层(模式D):s3 与 label 零交集')

        # 2. Phase4 不映射
        exp_s4 = set(_get(exp, 'phase4_label') or [])
        act_s4 = set(_get(out, 'phase4_codes') or [])
        if exp_s4 and not (exp_s4 & act_s4):
            reasons.append('Phase4 ≠ Phase3 映射:s4 与 label 零交集')

        # 3. 缺创意漏斗硬出 / 蒙做
        if not _get(out, 'has_funnel_section'):
            if _get(out, 'phase2_codes') or _get(out, 'phase3_codes'):
                reasons.append('缺创意漏斗硬出/蒙做(模式B/A):报告无漏斗体检段却出 Phase2/3 结论')

        if reasons:
            return EvaluationReason(value=0.0, reason='; '.join(reasons))
        return 1.0

    def get_default_evaluation_name(self) -> str:
        return 'EndToEnd_端到端级联'


ALL_EVALUATORS: list = [
    Phase0Evaluator(),
    Phase1Evaluator(),
    Phase2Evaluator(),
    Phase3Evaluator(),
    Phase4Evaluator(),
    EndToEndEvaluator(),
]
