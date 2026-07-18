const steps = ["选择数据源", "配置目标", "迁移预检", "执行迁移", "迁移结果"];

export function StepIndicator({ step }: { step: number }) {
  return <nav aria-label="迁移步骤"><ol className="step-indicator">
    {steps.map((label, index) => <li key={label} aria-current={index === step ? "step" : undefined} className={index <= step ? "active" : undefined}><span>{index + 1}</span>{label}</li>)}
  </ol></nav>;
}
