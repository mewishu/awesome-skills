# **<font style="color:rgba(25, 26, 31, 0.9);background-color:rgba(255, 255, 255, 0.8);">skill模式与最佳实践</font>**
## <font style="color:rgb(44, 44, 43);">5 种核心设计模式</font>
### <font style="color:rgb(44, 44, 43);">模式 1：线性流程</font>
**<font style="color:rgb(44, 44, 43);">适用场景</font>**<font style="color:rgb(44, 44, 43);">：部署、安装、迁移等有明确步骤的操作。</font>

**<font style="color:rgb(44, 44, 43);">代表</font>**<font style="color:rgb(44, 44, 43);">：</font>[<font style="color:rgb(0, 128, 255) !important;">openai/skills — vercel-deploy</font>](https://github.com/openai/skills/tree/main/skills/.curated/vercel-deploy)<font style="color:rgb(44, 44, 43);">（77 行）</font>

**<font style="color:rgb(44, 44, 43);">结构</font>**<font style="color:rgb(44, 44, 43);">：</font>

```markdown
# 标题
## Prerequisites（前置条件）
## Quick Start（主流程：Step 1 → 2 → 3）
## Fallback（降级方案）
## Troubleshooting（故障排除）
```

**<font style="color:rgb(44, 44, 43);">关键技巧</font>**<font style="color:rgb(44, 44, 43);">：</font>

| <font style="color:rgb(44, 44, 43);">技巧</font> | <font style="color:rgb(44, 44, 43);">示例</font> | <font style="color:rgb(44, 44, 43);">为什么有效</font> |
| --- | --- | --- |
| **<font style="color:rgb(44, 44, 43);">安全默认值</font>** | <font style="color:rgb(44, 44, 43);">"Always deploy as preview, not production"</font> | <font style="color:rgb(44, 44, 43);">防止 LLM 做出危险操作</font> |
| **<font style="color:rgb(44, 44, 43);">具体命令</font>** | <font style="color:rgb(44, 44, 43);">每步给出可直接执行的 bash 命令</font> | <font style="color:rgb(44, 44, 43);">LLM 不需要猜测</font> |
| **<font style="color:rgb(44, 44, 43);">超时提示</font>** | <font style="color:rgb(44, 44, 43);">"Use a 10 minute (600000ms) timeout"</font> | <font style="color:rgb(44, 44, 43);">防止 LLM 因超时中断</font> |
| **<font style="color:rgb(44, 44, 43);">降级方案</font>** | <font style="color:rgb(44, 44, 43);">CLI 失败有 Fallback 脚本</font> | <font style="color:rgb(44, 44, 43);">提供 B 计划</font> |
| **<font style="color:rgb(44, 44, 43);">负面指令</font>** | <font style="color:rgb(44, 44, 43);">"Do not curl the deployed URL to verify"</font> | <font style="color:rgb(44, 44, 43);">明确禁止不该做的事</font> |


**<font style="color:rgb(44, 44, 43);">适用判断</font>**<font style="color:rgb(44, 44, 43);">：如果你的 Skill 可以用"先做 A，再做 B，最后做 C"描述，就用线性模式。</font>

### <font style="color:rgb(44, 44, 43);">模式 2：决策树 + 按需加载</font>
**<font style="color:rgb(44, 44, 43);">适用场景</font>**<font style="color:rgb(44, 44, 43);">：大型平台选型、产品导航、问题诊断。</font>

**<font style="color:rgb(44, 44, 43);">代表</font>**<font style="color:rgb(44, 44, 43);">：</font>[<font style="color:rgb(0, 128, 255) !important;">openai/skills — cloudflare-deploy</font>](https://github.com/openai/skills/tree/main/skills/.curated/cloudflare-deploy)<font style="color:rgb(44, 44, 43);">（224 行）</font>

**<font style="color:rgb(44, 44, 43);">结构</font>**<font style="color:rgb(44, 44, 43);">：</font>

```markdown
# 标题
## Authentication（认证前置）
## Quick Decision Trees（决策树）
### "I need to run code"（按用户意图分类）
### "I need to store data"
### "I need AI/ML"
## Product Index（产品索引表）
```

**<font style="color:rgb(44, 44, 43);">关键技巧</font>**<font style="color:rgb(44, 44, 43);">：</font>

| <font style="color:rgb(44, 44, 43);">技巧</font> | <font style="color:rgb(44, 44, 43);">示例</font> | <font style="color:rgb(44, 44, 43);">为什么有效</font> |
| --- | --- | --- |
| **<font style="color:rgb(44, 44, 43);">用户意图分类</font>** | <font style="color:rgb(44, 44, 43);">"I need to run code" 而非 "Compute products"</font> | <font style="color:rgb(44, 44, 43);">用用户语言而非技术术语</font> |
| **<font style="color:rgb(44, 44, 43);">树形导航</font>** | `<font style="color:rgb(44, 44, 43);">├─ 边缘无服务器函数 → workers/</font>` | <font style="color:rgb(44, 44, 43);">LLM 快速定位正确产品</font> |
| **<font style="color:rgb(44, 44, 43);">渐进式披露</font>** | <font style="color:rgb(44, 44, 43);">主文件 7KB，references/ 按需展开到几十万字</font> | <font style="color:rgb(44, 44, 43);">不浪费上下文窗口</font> |
| **<font style="color:rgb(44, 44, 43);">产品索引表</font>** | <font style="color:rgb(44, 44, 43);">Product → Reference 的映射表</font> | <font style="color:rgb(44, 44, 43);">结构化的快速查找</font> |


**<font style="color:rgb(44, 44, 43);">适用判断</font>**<font style="color:rgb(44, 44, 43);">：如果你的 Skill 覆盖的知识域有 10+ 个分支，且每个分支都有大量详细文档，就用决策树模式。</font>

**<font style="color:rgb(44, 44, 43);">进阶</font>**<font style="color:rgb(44, 44, 43);">：同一个知识域可以拆成两个 Skill——</font>

+ **<font style="color:rgb(44, 44, 43);">导航型</font>**<font style="color:rgb(44, 44, 43);">（cloudflare）：只做选型，不涉及操作</font>
+ **<font style="color:rgb(44, 44, 43);">操作型</font>**<font style="color:rgb(44, 44, 43);">（cloudflare-deploy）：包含认证、命令、故障排除</font>

### <font style="color:rgb(44, 44, 43);">模式 3：循环迭代</font>
**<font style="color:rgb(44, 44, 43);">适用场景</font>**<font style="color:rgb(44, 44, 43);">：TDD、代码审查、设计评审等需要反复执行的流程。</font>

**<font style="color:rgb(44, 44, 43);">代表</font>**<font style="color:rgb(44, 44, 43);">：</font>[<font style="color:rgb(0, 128, 255) !important;">obra/superpowers — test-driven-development</font>](https://github.com/obra/superpowers/tree/main/skills/test-driven-development)<font style="color:rgb(44, 44, 43);">（371 行）</font>

**<font style="color:rgb(44, 44, 43);">结构</font>**<font style="color:rgb(44, 44, 43);">：</font>

```markdown
# 标题
## The Iron Law（铁律——不可违反的核心原则）
## Red-Green-Refactor（循环体）
### RED — 写失败的测试
### Verify RED — 验证确实失败
### GREEN — 写最少的代码
### Verify GREEN — 验证确实通过
### REFACTOR — 清理
### Repeat（回到 RED）
## Common Rationalizations（借口反驳表）
## Verification Checklist（退出条件）
```

**<font style="color:rgb(44, 44, 43);">关键技巧</font>**<font style="color:rgb(44, 44, 43);">：</font>

| <font style="color:rgb(44, 44, 43);">技巧</font> | <font style="color:rgb(44, 44, 43);">示例</font> | <font style="color:rgb(44, 44, 43);">为什么有效</font> |
| --- | --- | --- |
| **<font style="color:rgb(44, 44, 43);">强硬语气</font>** | <font style="color:rgb(44, 44, 43);">"Delete it. Start over."</font> | <font style="color:rgb(44, 44, 43);">LLM 倾向于"灵活变通"，强硬语气提高遵从率</font> |
| **<font style="color:rgb(44, 44, 43);">Good/Bad 对比</font>** | <font style="color:rgb(44, 44, 43);">用 </font>`<font style="color:rgb(44, 44, 43);"><Good></font>`<font style="color:rgb(44, 44, 43);"> 和 </font>`<font style="color:rgb(44, 44, 43);"><Bad></font>`<font style="color:rgb(44, 44, 43);"> 标签包裹代码示例</font> | <font style="color:rgb(44, 44, 43);">对比教学效果最好</font> |
| **<font style="color:rgb(44, 44, 43);">借口反驳表</font>** | <font style="color:rgb(44, 44, 43);">预判 LLM 可能的 12 种偷懒借口并逐一反驳</font> | <font style="color:rgb(44, 44, 43);">堵死所有逃避路径</font> |
| **<font style="color:rgb(44, 44, 43);">验证清单</font>** | <font style="color:rgb(44, 44, 43);">8 项 checklist 作为循环退出条件</font> | <font style="color:rgb(44, 44, 43);">确保质量达标才能结束</font> |
| **<font style="color:rgb(44, 44, 43);">人类兜底</font>** | <font style="color:rgb(44, 44, 43);">"ask your human partner"</font> | <font style="color:rgb(44, 44, 43);">不确定时交给人</font> |


**<font style="color:rgb(44, 44, 43);">适用判断</font>**<font style="color:rgb(44, 44, 43);">：如果你的 Skill 需要 LLM 反复执行"做→验证→改进"的循环，就用迭代模式。</font>

### <font style="color:rgb(44, 44, 43);">模式 4：接力棒循环（跨 Session 持久化）</font>
**<font style="color:rgb(44, 44, 43);">适用场景</font>**<font style="color:rgb(44, 44, 43);">：多次迭代的长期项目，需要跨多个 session 持续工作。</font>

**<font style="color:rgb(44, 44, 43);">代表</font>**<font style="color:rgb(44, 44, 43);">：</font>[<font style="color:rgb(0, 128, 255) !important;">google-labs-code/stitch-skills — stitch-loop</font>](https://github.com/google-labs-code/stitch-skills/tree/0337446dadde6f8c94210444e2aa9d546126480f/plugins/stitch-utilities/skills/stitch-loop)<font style="color:rgb(44, 44, 43);">（203 行）</font>

**<font style="color:rgb(44, 44, 43);">结构</font>**<font style="color:rgb(44, 44, 43);">：</font>

```markdown
# 标题
## Overview（接力棒模式概述）
## The Baton System（接力棒文件规范）
## Execution Protocol（6 步执行协议）
### Step 1: Read the Baton（读接力棒）
### Step 2: Consult Context Files（查阅上下文）
### Step 3: Generate（执行任务）
### Step 4: Integrate（集成结果）
### Step 5: Update Documentation（更新文档）
### Step 6: Prepare the Next Baton ⚠️（写下一个接力棒——关键！）
## File Structure Reference（文件协议）
## Orchestration Options（编排方式）
```

**<font style="color:rgb(44, 44, 43);">关键技巧</font>**<font style="color:rgb(44, 44, 43);">：</font>

| <font style="color:rgb(44, 44, 43);">技巧</font> | <font style="color:rgb(44, 44, 43);">示例</font> | <font style="color:rgb(44, 44, 43);">为什么有效</font> |
| --- | --- | --- |
| **<font style="color:rgb(44, 44, 43);">文件即状态</font>** | `<font style="color:rgb(44, 44, 43);">next-prompt.md</font>`<font style="color:rgb(44, 44, 43);"> 作为接力棒</font> | <font style="color:rgb(44, 44, 43);">LLM 不需要记住"上次做到哪了"</font> |
| **<font style="color:rgb(44, 44, 43);">续命机制</font>** | <font style="color:rgb(44, 44, 43);">Step 6 标记为 Critical + MUST</font> | <font style="color:rgb(44, 44, 43);">忘了写接力棒循环就断了</font> |
| **<font style="color:rgb(44, 44, 43);">文件协议</font>** | <font style="color:rgb(44, 44, 43);">每个文件有明确职责</font> | <font style="color:rgb(44, 44, 43);">LLM 只需按协议读写文件</font> |
| **<font style="color:rgb(44, 44, 43);">编排无关</font>** | <font style="color:rgb(44, 44, 43);">CI/CD、人在回路、Agent 链都能驱动</font> | <font style="color:rgb(44, 44, 43);">同一个 Skill 适配多种自动化环境</font> |


**<font style="color:rgb(44, 44, 43);">适用判断</font>**<font style="color:rgb(44, 44, 43);">：如果你的 Skill 需要跨多个 session 持续工作，或者需要多个 Agent 协作，就用接力棒模式。</font>

**<font style="color:rgb(44, 44, 43);">与模式 3 的区别</font>**<font style="color:rgb(44, 44, 43);">：</font>

| <font style="color:rgb(44, 44, 43);">维度</font> | <font style="color:rgb(44, 44, 43);">循环迭代（TDD）</font> | <font style="color:rgb(44, 44, 43);">接力棒循环（Stitch Loop）</font> |
| --- | --- | --- |
| <font style="color:rgb(44, 44, 43);">状态存储</font> | <font style="color:rgb(44, 44, 43);">LLM 对话上下文</font> | <font style="color:rgb(44, 44, 43);">外部文件系统</font> |
| <font style="color:rgb(44, 44, 43);">跨 session</font> | <font style="color:rgb(44, 44, 43);">❌</font> | <font style="color:rgb(44, 44, 43);">✅</font> |
| <font style="color:rgb(44, 44, 43);">循环退出</font> | <font style="color:rgb(44, 44, 43);">Checklist 全部打勾</font> | <font style="color:rgb(44, 44, 43);">路线图清空</font> |
| <font style="color:rgb(44, 44, 43);">适用时长</font> | <font style="color:rgb(44, 44, 43);">单次会话（分钟~小时）</font> | <font style="color:rgb(44, 44, 43);">长期项目（天~周）</font> |


### <font style="color:rgb(44, 44, 43);">模式 5：多阶段 + 检查点 + Skill 编排</font>
**适用场景**<font style="color:rgb(31, 35, 40);">：跨多个阶段、需在关键节点做 Go/No-Go 决策的复杂流程——无论是分钟级的多 Agent 自动化流水线，还是数周的人类引导式工作坊。</font>

#### <font style="color:rgb(31, 35, 40);">代表 1（自动化执行极，通用性更强、机制更密）</font>
[trailofbits/skills — zeroize-audit](https://github.com/trailofbits/skills/tree/main/plugins/zeroize-audit/skills/zeroize-audit)<font style="color:rgb(31, 35, 40);">（SKILL.md 360 行；11 个子 Agent、8 阶段）</font>

**结构**<font style="color:rgb(31, 35, 40);">：</font>

```markdown
# 标题
## When to Use / When NOT to Use
## Inputs / Prerequisites（含 fail-fast vs 降级 失败模式表）
## Finding Capabilities（11 种发现 × 必需证据通道）
## Agent Architecture（11 Agent × 8 Phase + Wave 并行 + ID 命名空间）
### Phase 0~7（统一模板：Preconditions → Instructions → State Update → Error Handling → Next Phase）
## Confidence Gating（硬证据门 + 量化信号）
## PoC 双闭环（generator → validator → verifier → 人在回路）
## Rationalizations to Reject（借口反驳表）
## Fix Recommendations
```

**关键技巧**<font style="color:rgb(31, 35, 40);">：</font>

| <font style="color:rgb(31, 35, 40);">技巧</font> | <font style="color:rgb(31, 35, 40);">示例</font> | <font style="color:rgb(31, 35, 40);">为什么有效</font> |
| --- | --- | --- |
| **统一阶段模板** | <font style="color:rgb(31, 35, 40);">每个 Phase = Preconditions → Instructions → State Update → Error Handling → Next Phase</font> | <font style="color:rgb(31, 35, 40);">LLM 快速理解结构，且天然可断点续跑</font> |
| **决策检查点 / 早终止** | <font style="color:rgb(31, 35, 40);">零敏感对象 → 跳 Phase 6；findings 空 → 跳 4-5；Phase 5c 让人对失败 PoC 做 Accept/Reject</font> | <font style="color:rgb(31, 35, 40);">防盲目推进 + 唯一人在回路兜底</font> |
| **Agent 编排（并行）** | <font style="color:rgb(31, 35, 40);">编排器调度 11 子 Agent，含 N 个并行 TU、Wave 2a‖2b 并行</font> | <font style="color:rgb(31, 35, 40);">大 Skill 调度小 Agent，并行省时、隔离容错</font> |
| **文件即状态** | `<font style="color:rgb(31, 35, 40);">orchestrator-state.json</font>`<font style="color:rgb(31, 35, 40);"> + workdir 当总线，不靠对话历史</font> | <font style="color:rgb(31, 35, 40);">抗 context 压缩、断点可恢复</font> |
| **硬证据门** | <font style="color:rgb(31, 35, 40);">OPTIMIZED_AWAY 必须 IR diff；栈/寄存器残留必须汇编</font> | <font style="color:rgb(31, 35, 40);">杜绝"仅凭源码"误报</font> |
| **对抗式验证** | <font style="color:rgb(31, 35, 40);">PoC 生成(5) 与独立核验(5c) 分离，5c 专挑 5 的刺</font> | <font style="color:rgb(31, 35, 40);">防自我确认偏误</font> |
| **借口反驳表** | <font style="color:rgb(31, 35, 40);">7 种压低发现的借口被逐一拒绝，用借口就保留原置信度并记 evidence</font> | <font style="color:rgb(31, 35, 40);">堵死 LLM 偷懒逃避</font> |


**适用判断**<font style="color:rgb(31, 35, 40);">：如果你的 Skill 是技术 / 自动化类多阶段任务（安全审计、批量分析、迁移验证等），需要机器并行、证据门、对抗式自验、断点续跑，用 zeroize-audit 这种"自动化执行极"。</font>

#### <font style="color:rgb(31, 35, 40);">代表 2（人类工作坊极）</font>
[deanpeters/Product-Manager-Skills — discovery-process](https://github.com/deanpeters/Product-Manager-Skills/tree/main/skills/discovery-process)<font style="color:rgb(31, 35, 40);">（516 行）</font>

**结构**<font style="color:rgb(31, 35, 40);">：</font>

```markdown
# 标题
## Key Concepts（核心概念 + 反模式）
## Phase 1: Frame the Problem（阶段 1）
### Activities（调用哪些子 Skill）
### Outputs（阶段产出）
### Decision Point 1（检查点：YES/NO + 时间影响）
## Phase 2-6...（重复相同结构）
## Complete Workflow（端到端时间线）
## Common Pitfalls（常见陷阱）
## References（引用的子 Skill 列表）
```

**关键技巧**<font style="color:rgb(31, 35, 40);">：</font>

| <font style="color:rgb(31, 35, 40);">技巧</font> | <font style="color:rgb(31, 35, 40);">示例</font> | <font style="color:rgb(31, 35, 40);">为什么有效</font> |
| --- | --- | --- |
| **统一阶段模板** | <font style="color:rgb(31, 35, 40);">每个 Phase 都有 Activities → Outputs → Decision Point</font> | <font style="color:rgb(31, 35, 40);">LLM 快速理解结构</font> |
| **决策检查点** | <font style="color:rgb(31, 35, 40);">"达到饱和了吗？YES → 下一阶段，NO → +1 周"</font> | <font style="color:rgb(31, 35, 40);">防止盲目推进</font> |
| **Skill 编排** | <font style="color:rgb(31, 35, 40);">调度 10+ 个子 Skill 完成各阶段</font> | <font style="color:rgb(31, 35, 40);">编排器模式，大 Skill 调度小 Skill</font> |
| **时间影响** | <font style="color:rgb(31, 35, 40);">每个 NO 路径标注"+2-3 days"、"+1 week"</font> | <font style="color:rgb(31, 35, 40);">让用户了解延迟成本</font> |
| **交互协议分离** | <font style="color:rgb(31, 35, 40);">引用 </font>`<font style="color:rgb(31, 35, 40);">workshop-facilitation</font>`<font style="color:rgb(31, 35, 40);"> 定义交互方式</font> | <font style="color:rgb(31, 35, 40);">关注点分离</font> |


**适用判断**<font style="color:rgb(31, 35, 40);">：如果你的 Skill 跨越多天 / 多周、面向人类引导式工作坊，有明确阶段划分和 Go/No-Go 决策点，用 discovery-process 这种"人类工作坊极"。</font>


### <font style="color:rgb(44, 44, 43);">特殊模式：思维框架（控制 LLM "怎么想"）</font>
**<font style="color:rgb(44, 44, 43);">适用场景</font>**<font style="color:rgb(44, 44, 43);">：安全审计、代码审查、架构分析等需要深度思考的场景。</font>

**<font style="color:rgb(44, 44, 43);">代表</font>**<font style="color:rgb(44, 44, 43);">：</font>[<font style="color:rgb(0, 128, 255) !important;">trailofbits/skills — audit-context-building</font>](https://github.com/trailofbits/skills/tree/main/plugins/audit-context-building/skills/audit-context-building)<font style="color:rgb(44, 44, 43);">（302 行）</font>

**<font style="color:rgb(44, 44, 43);">结构</font>**<font style="color:rgb(44, 44, 43);">：</font>

```markdown
# 标题
## Purpose（定位：控制思维方式，不是控制行为）
## When to Use / When NOT to Use
## Rationalizations（借口反驳表）
## Phase 1: Initial Orientation（定向扫描）
## Phase 2: Ultra-Granular Function Analysis（逐行分析——核心）
### Per-Function Checklist（函数微分析清单）
### Cross-Function Flow Analysis（跨函数追踪）
### Output Requirements（输出格式 + 量化阈值）
### Completeness Checklist（完整性检查）
## Phase 3: Global System Understanding（全局理解）
## Stability Rules（反幻觉规则）
## Non-Goals（明确禁止做的事）
```

**<font style="color:rgb(44, 44, 43);">关键技巧</font>**<font style="color:rgb(44, 44, 43);">：</font>

| <font style="color:rgb(44, 44, 43);">技巧</font> | <font style="color:rgb(44, 44, 43);">示例</font> | <font style="color:rgb(44, 44, 43);">为什么有效</font> |
| --- | --- | --- |
| **<font style="color:rgb(44, 44, 43);">思维工具</font>** | <font style="color:rgb(44, 44, 43);">第一性原理、5 Why、5 How</font> | <font style="color:rgb(44, 44, 43);">给 LLM 分析框架而非具体命令</font> |
| **<font style="color:rgb(44, 44, 43);">量化阈值</font>** | <font style="color:rgb(44, 44, 43);">"每个函数最少 3 个不变量、5 个假设"</font> | <font style="color:rgb(44, 44, 43);">强制 LLM 达到足够的分析深度</font> |
| **<font style="color:rgb(44, 44, 43);">非目标约束</font>** | <font style="color:rgb(44, 44, 43);">"不要识别漏洞、不要提出修复"</font> | <font style="color:rgb(44, 44, 43);">克制 LLM 最想做的事，先理解再判断</font> |
| **<font style="color:rgb(44, 44, 43);">反幻觉规则</font>** | <font style="color:rgb(44, 44, 43);">"Never reshape evidence to fit earlier assumptions"</font> | <font style="color:rgb(44, 44, 43);">防止 LLM 自我欺骗</font> |
| **<font style="color:rgb(44, 44, 43);">子 Agent 指导</font>** | <font style="color:rgb(44, 44, 43);">何时以及如何使用 function-analyzer Agent</font> | <font style="color:rgb(44, 44, 43);">分而治之</font> |


**<font style="color:rgb(44, 44, 43);">适用判断</font>**<font style="color:rgb(44, 44, 43);">：如果你的 Skill 需要 LLM 进行深度分析而非快速执行，需要控制的是"思维质量"而非"操作步骤"，就用思维框架模式。</font>

## <font style="color:rgb(44, 44, 43);">模式选择决策树</font>
```markdown
你的 Skill 需要做什么？
│
├─ 执行一个有明确步骤的操作
│  └─ → 模式 1：线性流程
│
├─ 在大量选项中帮用户选择正确的方向
│  └─ → 模式 2：决策树 + 按需加载
│
├─ 在单次会话中反复执行"做→验证→改进"
│  └─ → 模式 3：循环迭代
│
├─ 跨多个 session 持续推进一个长期项目
│  └─ → 模式 4：接力棒循环
│
├─ 跨越多天/多周，有阶段划分和 Go/No-Go 决策
│  └─ → 模式 5：多阶段 + 检查点
│
└─ 需要 LLM 进行深度分析而非快速执行
   └─ → 特殊模式：思维框架
```

## <font style="color:rgb(44, 44, 43);">快速上手模板</font>
### <font style="color:rgb(44, 44, 43);">最小可用 Skill（线性模式）</font>
```markdown
description: [一句话描述做什么 + 什么时候触发]
---

# Skill 名称

[一句话核心原则 + 安全默认值]

## Prerequisites
- [前置条件 1]
- [前置条件 2]

## Steps

### Step 1: [动作]
\`\`\`bash
[具体命令]
\`\`\`

### Step 2: [动作]
[具体指令]

### Step 3: [动作]
[具体指令]

## Troubleshooting
| Issue | Solution |
|-------|----------|
| [问题 1] | [解决方案] |
```

### <font style="color:rgb(44, 44, 43);">循环迭代 Skill 模板</font>
```markdown
## Core Principle
[不可违反的铁律]

## The Loop

### Phase A — [动作]
[具体指令]

### Verify A
[验证命令]

### Phase B — [动作]
[具体指令]

### Verify B
[验证命令]

### Repeat
回到 Phase A。

## Rationalizations
| Excuse | Reality |
|--------|---------|
| "[借口 1]" | [反驳] |

## Completion Checklist
- [ ] [条件 1]
- [ ] [条件 2]

```

## <font style="color:rgb(44, 44, 43);">参考资源</font>
### <font style="color:rgb(44, 44, 43);">官方规范</font>
+ [<font style="color:rgb(0, 128, 255) !important;">Agent Skills 开放标准</font>](https://agentskills.io/)
+ [<font style="color:rgb(0, 128, 255) !important;">anthropics/skills — 官方模板</font>](https://github.com/anthropics/skills/tree/main/template)
+ [<font style="color:rgb(0, 128, 255) !important;">anthropics/skills — 规范文档</font>](https://github.com/anthropics/skills/tree/main/spec)

### <font style="color:rgb(44, 44, 43);">精选仓库</font>
+ [<font style="color:rgb(0, 128, 255) !important;">openai/skills</font>](https://github.com/openai/skills)<font style="color:rgb(44, 44, 43);"> — OpenAI Codex 官方 Skill 目录</font>
+ [<font style="color:rgb(0, 128, 255) !important;">obra/superpowers</font>](https://github.com/obra/superpowers)<font style="color:rgb(44, 44, 43);"> — 14 个工作流型 Skill</font>
+ [<font style="color:rgb(0, 128, 255) !important;">google-labs-code/stitch-skills</font>](https://github.com/google-labs-code/stitch-skills)<font style="color:rgb(44, 44, 43);"> — 设计到代码的 Skill</font>
+ [<font style="color:rgb(0, 128, 255) !important;">deanpeters/Product-Manager-Skills</font>](https://github.com/deanpeters/Product-Manager-Skills)<font style="color:rgb(44, 44, 43);"> — 40+ 产品管理 Skill</font>
+ [<font style="color:rgb(0, 128, 255) !important;">trailofbits/skills</font>](https://github.com/trailofbits/skills)<font style="color:rgb(44, 44, 43);"> — 安全审计 Skill</font>
+ [<font style="color:rgb(0, 128, 255) !important;">openclaw/clawhub</font>](https://github.com/openclaw/clawhub)<font style="color:rgb(44, 44, 43);"> — Skill 注册中心</font>

### <font style="color:rgb(44, 44, 43);">精选列表</font>
+ [<font style="color:rgb(0, 128, 255) !important;">VoltAgent/awesome-agent-skills</font>](https://github.com/VoltAgent/awesome-agent-skills)<font style="color:rgb(44, 44, 43);"> — 500+ Skill 索引</font>
+ [<font style="color:rgb(0, 128, 255) !important;">travisvn/awesome-claude-skills</font>](https://github.com/travisvn/awesome-claude-skills)<font style="color:rgb(44, 44, 43);"> — 精选列表 + Skill vs MCP 对比</font>
+ [<font style="color:rgb(0, 128, 255) !important;">ComposioHQ/awesome-claude-skills</font>](https://github.com/ComposioHQ/awesome-claude-skills)<font style="color:rgb(44, 44, 43);"> — 精选列表Skill列表</font>
