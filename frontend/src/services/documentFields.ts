export function documentFieldSourceLabel(source: string): string {
  const map: Record<string, string> = {
    CHANGE_SPEC: '명세',
    SQL_PACK: 'SQL 팩',
    requestOrigin: '요청 원문',
    targetTable: '대상 테이블',
    operation: '변경 작업',
    predicates: '대상 조건',
    mutations: '변경 값',
    identityKeyColumns: '식별 키',
    expectedRowCount: '예상 영향 건수',
    precheckSql: '확인 SQL',
    backupSql: '백업 SQL',
    executionSql: '실행 SQL',
    verificationSql: '검증 SQL',
    rollbackSql: '롤백 SQL',
    reviewVerdict: '검토 판정',
    riskLevel: '위험 등급',
    approver: '승인자',
  }
  return map[source] ?? source
}

export function isSqlField(key: string): boolean {
  return ['precheckSql', 'backupSql', 'executionSql', 'verificationSql', 'rollbackSql'].includes(key)
}

export type TemplateId = 'default' | 'security' | 'simple'

export const documentFieldSourceOptions = [
  { value: 'requestOrigin', label: '요청 원문' },
  { value: 'targetTable', label: '대상 테이블' },
  { value: 'operation', label: '변경 작업' },
  { value: 'predicates', label: '대상 조건' },
  { value: 'mutations', label: '변경 값' },
  { value: 'identityKeyColumns', label: '식별 키' },
  { value: 'expectedRowCount', label: '예상 영향 건수' },
  { value: 'precheckSql', label: '확인 SQL' },
  { value: 'backupSql', label: '백업 SQL' },
  { value: 'executionSql', label: '실행 SQL' },
  { value: 'verificationSql', label: '검증 SQL' },
  { value: 'rollbackSql', label: '롤백 SQL' },
  { value: 'reviewVerdict', label: '검토 판정' },
  { value: 'riskLevel', label: '위험 등급' },
  { value: 'approver', label: '승인자' },
] as const
